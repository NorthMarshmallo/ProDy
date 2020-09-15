# -*- coding: utf-8 -*-
"""This module defines functions for fetching and parsing files in the PDB  
for the Biologically Interesting Molecule Reference Dictionary (BIRD_). 

.. _BIRD: https://www.wwpdb.org/data/bird

The chemical information is stored in Peptide Reference Dictionary (PRD) files, 
whereas the biological function is documented in a separate family file."""

import os

from prody import LOGGER, getPackagePath
from prody.utilities import isListLike
from prody.proteins import wwPDBServer, WWPDB_FTP_SERVERS

__all__ = ['fetchBIRDviaHTTP']

def fetchBIRDviaHTTP(**kwargs):
    """Retrieve the whole Biologically Interesting Molecule Reference 
    Dictionary (BIRD) resource, which is updated every week. This includes 
    2 kinds of keys, which can be selected with the **keys** keyword argument.

    The chemical information is found in a zipped (tar.gz) directory at 
    https://files.rcsb.org/pub/pdb/data/bird/prd/prd-all.cif.gz, which 
    contains individual CIF files within it. This data will be downloaded 
    and extracted to :file:`.prody/bird-prd`.

    Biological function information is also found in a zipped (tar.gz) directory at 
    https://files.rcsb.org/pub/pdb/data/bird/family/family-all.cif.gz, which 
    contains individual CIF files within it. This data will be downloaded 
    and extracted to :file:`.prody/bird-family`.

    :arg keys: keys specifying which data to fetch out of ``'prd'``, ``'family'`` or ``'both'``
               default is ``'both'``
    :type keys: str, tuple, list, :class:`~numpy.ndarray`

    The underlying data can be accessed using :func:`parseBIRD`."""

    BIRD_PATH = os.path.join(getPackagePath(), 'bird')
    
    keys = kwargs.get('keys', 'both')
    if isinstance(keys, str):
        if keys == 'both':
            keys = ['prd', 'family']
        elif keys[:3].lower() == 'prd':
            keys = ['prd']
        elif keys[:3].lower() == 'fam':
            keys = ['family']
        else:
            raise ValueError("keys should be 'both', 'prd' or 'fam'")

    elif isListLike(keys):
        keys = list(keys)
    else:
        raise TypeError("keys should be list-like or string")

    ftp_divided = 'pdb/data/bird/'
    ftp_pdbext = '.cif.gz'
    ftp_prefix = ''

    if not os.path.isdir(BIRD_PATH):
        os.mkdir(BIRD_PATH)

    LOGGER.progress('Downloading BIRD', len(keys),
                    '_prody_fetchBIRD')

    ftp_name, ftp_host, ftp_path = WWPDB_FTP_SERVERS[wwPDBServer() or 'us']
    LOGGER.debug('Connecting wwPDB FTP server {0}.'.format(ftp_name))

    from ftplib import FTP
    try:
        ftp = FTP(ftp_host)
    except Exception as error:
        raise type(error)('FTP connection problem, potential reason: '
                          'no internet connectivity')
    else:
        count = 0
        success = 0
        failure = 0
        filenames = []
        ftp.login('')
        for i, x in enumerate(keys):
            data = []
            ftp_fn = ftp_prefix + '{0}-all'.format(x) + ftp_pdbext
            try:
                ftp.cwd(ftp_path)
                ftp.cwd(ftp_divided)
                ftp.cwd(x)
                ftp.retrbinary('RETR ' + ftp_fn, data.append)
            except Exception as error:
                if ftp_fn in ftp.nlst():
                    LOGGER.warn('{0} download failed ({1}). It is '
                                'possible that you do not have rights to '
                                'download .gz files in the current network.'
                                .format(x, str(error)))
                else:
                    LOGGER.info('{0} download failed. {1} does not exist '
                                'on {2}.'.format(ftp_fn, x, ftp_host))
                failure += 1
                filenames.append(None)
            else:
                if len(data):
                    filename = BIRD_PATH + '/{0}-all.cif.gz'.format(x)

                    with open(filename, 'w+b') as outfile:
                        write = outfile.write
                        [write(block) for block in data]

                    success += 1
                else:
                    failure += 1
            count += 1
            LOGGER.update(i, label='_prody_fetchBIRD')
        LOGGER.finish()

    LOGGER.debug('PDB download via FTP completed ({0} downloaded, '
                 '{1} failed).'.format(success, failure))

