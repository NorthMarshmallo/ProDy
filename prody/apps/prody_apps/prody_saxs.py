# -*- coding: utf-8 -*-
"""Perform Small Angle Scattering profile calculations of ANM modes 
   to enlighten solution structure of proteins. 
"""

from prody import *
import numpy as np
import sys
import argparse

from saxs import *

__all__ = ['prody_saxs']

def prody_saxs(pdb_file, saxs_file, **kwargs):
    #Set default values for calculations.

    if kwargs is not None:
        args_numModes=kwargs.get('numModes', 3)
        args_numFrames=kwargs.get('numFrames', 20)
        args_scalCoeff=kwargs.get('scalCoeff', 3.0)
        args_out_pdb_file=kwargs.get('out_pdb_file', 'best_model.pdb')
        args_out_saxs_file=kwargs.get('out_saxs_file', 'best_model_I_q.dat')

    #1-This module produces normal modes of a protein structure and 
    #by using anisotropic network model.    
    protein = parsePDB(pdb_file)
    calphas = protein.select('calpha')
    origCoords=calphas.getCoords()
    
    anm = ANM('ANM Analysis')
    anm.buildHessian(calphas)

    numCalphas=calphas.numAtoms()

    modes=anm.calcModes(n_modes=args_numModes, zeros=False)

#    mode_ensemble=traverseMode(anm[0], calphas, n_steps=10, rmsd=3.0)
#    print mode_ensemble[0]
#    writePDB('traverseMode_0.pdb', mode_ensemble, csets=None, autoext=True)
#    sys.exit(-1)

    #Parse experimental/simulated SAXS data.
    Q_exp, I_q_exp, sigma_q=parseSaxsData(saxs_file, simulated=False, isLogScale=True)

    I_model=np.zeros(len(Q_exp))
    prody.LOGGER.info('Number of experimental data points=%.d'%len(Q_exp))

    #Calculate a SAXS profile for initial pdb file by using Fast-SAXS approach.
    prody.LOGGER.info('Solvating the system and calculating SAXS profile.')
    calcSaxsPerModel(calphas, I_model, Q_exp)

    #Get initial chi value between pdb_file and saxs_file
    max_chi=calcSaxsChi(Q_exp, I_q_exp, sigma_q, Q_exp, I_model)
    prody.LOGGER.info('Chi value between pdb file and experimental SAXS profile=%.3f'%max_chi)

    #A SAXS profile is produced for each model in a mode using Fast-SAXS approach.
    #Now, lets do it with python code rather than calling an external fast-saxs-pro program

    chi_overall=[]
    frames_overall=[]

    #All modes are interpolated in +/- directions. scalCoeff is scaling coefficient of interpolation.
    #  A positive value of larger than 1 is recommended.

    mod_num=None

    prody.LOGGER.timeit('_intplt_mode')    
    for i in range (0, args_numModes):
            eigenvalue=anm[i].getEigval()
            eigenvector=np.transpose(anm[i].getEigvec())

            # setup toolbar
            sys.stdout.write("@> Calculating SAXS profiles for nonzero mode %d: " % (i+1))
            sys.stdout.write("[%s]" % (" " * (args_numFrames+1)))
            sys.stdout.flush()
            sys.stdout.write("\b" * (args_numFrames+2)) # return to start of line, after '['

            invEigVal=(1.0/eigenvalue)
            for j in range((-args_numFrames/2), ((args_numFrames/2)+1)):
                coeff=j*(args_scalCoeff)*invEigVal*2.0/args_numFrames
                
                newCoords=calphas.getCoords().flatten()+(coeff*eigenvector)
                calphas.setCoords(newCoords.reshape((numCalphas, 3), order='C'))
                calcSaxsPerModel(calphas, I_model, Q_exp)
                chi=calcSaxsChi(Q_exp, I_q_exp, sigma_q, Q_exp, I_model)
                chi_overall.append(chi)
                frames_overall.append(j)
                if(chi<max_chi):
                    max_chi=chi
                    mod_num=i
                    writePDB(args_out_pdb_file, calphas)

                    #           extendModel(calphas, 'calphas', protein)
                    #           writePDB('best_model.pdb', protein)
                    
                #Reset coordinates to the original values
                calphas.setCoords(origCoords)
            
                sys.stdout.write('#')
                sys.stdout.flush()
            sys.stdout.write("\n")

    prody.LOGGER.report('SAXS profile calculations were performed in %2fs.', '_intplt_mode')
    
#    showChivsFrames(chi_overall, frames_overall, args_numFrames)
    writeChivsFrames(chi_overall, frames_overall, 'chi_vs_frames.png', numFrames=args_numFrames)

    #The model with the lowest Chi value is written to a pdb file.
    prody.LOGGER.info('Chi value between the best model and the experimental SAXS data=%.3f'%np.amin(chi_overall))

    #    print np.argmin(chi_overall)
    best_model_all = parsePDB(args_out_pdb_file)
    best_model_calphas = best_model_all.select('calpha')
    calcSaxsPerModel(best_model_calphas, I_model, Q_exp)
    writeSaxsProfile(I_model, Q_exp, sigma_q, args_out_saxs_file)

def addCommand(commands):

    subparser = commands.add_parser('saxs',
        help='Perform Small Angle X-ray Scattering analysis of a protein')

#    subparser.add_argument('--quiet', help="suppress info messages to stderr",
#        action=Quiet, nargs=0)

#    subparser.add_argument('--examples', action=UsageExample, nargs=0,
#        help='show usage examples and exit')

    subparser.set_defaults(usage_example=
    """Try to obtain closed conformation of adenylate kinase 
    by using pdb file of open conformation and SAXS data of open
    conformation.

    $ prody saxs 4ake_chainA.pdb 1ake_chainA_saxs_w_yerrorbars.dat""",
    test_examples=[0]
    )

    subparser.add_argument('pdb_file' , nargs='?', type=str, \
                           help='Mandatory input pdb file.')

    subparser.add_argument('saxs_file', nargs='?', type=str,\
                           help='Mandatory experimental/simulated SAXS profile.')

    subparser.add_argument('-n', '--nmodes', type=int, dest='numModes',\
                           default=5, \
                           help='Number of nonzero modes to be used in calculations.')

    subparser.add_argument('-f', '--nframes', type=int, dest='numFrames',\
                           default=20, \
                           help='Number of frames to interpolate a single mode.')

    subparser.add_argument('-c', '--coeff', type=float, dest='scalCoeff',\
                           default=3.0, \
                           help='''Scaling coefficient for interpolating a single'''+\
                           ''' mode. A positive value of larger than 1 is recommended.''')

    subparser.add_argument('-p', '--out-pdb', \
                           type=str, dest='out_pdb_file', \
                           default='best_model.pdb', \
                           help='Output pdb file for the best model.')

    subparser.add_argument('-s', '--out-saxs', type=str, dest='out_saxs_file', \
                           default='best_model_I_q.dat', \
                           help='Output SAXS profile for the best model')

    subparser.set_defaults(func=lambda ns: prody_saxs(ns.__dict__.pop('pdb_file'),\
                                                      ns.__dict__.pop('saxs_file'),\
                                                      **ns.__dict__))
    subparser.set_defaults(subparser=subparser)

def main():
    #0-Parse all arguments
    parser = argparse.ArgumentParser(description=\
    'Find the best mode fitting to a given SAXS profile.',\
    epilog=\
    'Example: python prody_saxs.py 4ake_chainA.pdb 1ake_chainA_saxs_w_yerrorbars.dat ')
    parser.add_argument('pdb_file', nargs='?', type=str, \
                        help='Mandatory input pdb file.')
    
    parser.add_argument('saxs_file', nargs='?', type=str,\
                           help='Mandatory experimental/simulated SAXS profile.')

    parser.add_argument('-n', '--nmodes', type=int, dest='numModes',\
                        default=5, \
                        help='Number of nonzero modes to be used in calculations.')

    parser.add_argument('-f', '--nframes', type=int, dest='numFrames',\
                        default=20, \
                        help='Number of frames to interpolate a single mode.')
    
    parser.add_argument('-c', '--coeff', type=float, dest='scalCoeff',\
                        default=3.0, \
                        help='''Scaling coefficient for interpolating a single'''+\
                        ''' mode. A positive value of larger than 1 is recommended.''')

    parser.add_argument('-p', '--out-pdb', \
                        type=str, dest='out_pdb_file', \
                        default='best_model.pdb', \
                        help='Output pdb file for the best model.')

    parser.add_argument('-s', '--out-saxs', type=str, dest='out_saxs_file', \
                        default='best_model_I_q.dat', \
                        help='Output SAXS profile for the best model')

    args = parser.parse_args()
    
    kwargs=vars(args)
    pdb_file=kwargs.pop('pdb_file')
    saxs_file=kwargs.pop('saxs_file')
    prody_saxs(pdb_file, saxs_file, **kwargs)    
    
if __name__ == "__main__":
    main()

