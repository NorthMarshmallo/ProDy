# -*- coding: utf-8 -*-
"""This module defines a class and a function for anisotropic network model
(ANM) calculations."""

import numpy as np
from numbers import Integral

from prody import LOGGER
from prody.atomic import Atomic, AtomGroup
from prody.proteins import parsePDB
from prody.utilities import checkCoords
from prody.kdtree import KDTree

from .nma import NMA
from .gnm import GNMBase, solveEig, checkENMParameters

__all__ = ['ANM', 'calcANM']

class ANMBase(NMA):

    def __init__(self, name='Unknown'):

        super(ANMBase, self).__init__(name)
        self._is3d = True
        self._cutoff = None
        self._gamma = None
        self._hessian = None
        self._coords = None

    def _reset(self):

        super(ANMBase, self)._reset()
        self._cutoff = None
        self._gamma = None
        self._hessian = None
        self._is3d = True
        self._coords = None
    
    def _clear(self):
        self._trace = None
        self._cov = None

    def getHessian(self):
        """Returns a copy of the Hessian matrix."""

        if self._hessian is None:
            return None
        return self._hessian.copy()

    def _getHessian(self):
        """Returns the Hessian matrix."""

        return self._hessian

    def setHessian(self, hessian):
        """Set Hessian matrix.  A symmetric matrix is expected, i.e. not a
        lower- or upper-triangular matrix."""

        if not isinstance(hessian, np.ndarray):
            raise TypeError('hessian must be a Numpy array')
        elif hessian.ndim != 2 or hessian.shape[0] != hessian.shape[1]:
            raise ValueError('hessian must be square matrix')
        elif hessian.shape[0] % 3:
            raise ValueError('hessian.shape must be (3*n_atoms,3*n_atoms)')
        elif hessian.dtype != float:
            try:
                hessian = hessian.astype(float)
            except:
                raise ValueError('hessian.dtype must be float')
        self._reset()
        self._hessian = hessian
        self._dof = hessian.shape[0]
        self._n_atoms = self._dof // 3
        
    def buildHessian(self, coords, cutoff=15., gamma=1., **kwargs):
        """Build Hessian matrix for given coordinate set.

        :arg coords: a coordinate set or an object with ``getCoords`` method
        :type coords: :class:`numpy.ndarray`

        :arg cutoff: cutoff distance (Å) for pairwise interactions,
            default is 15.0 Å, minimum is 4.0 Å
        :type cutoff: float

        :arg gamma: spring constant, default is 1.0
        :type gamma: float, :class:`Gamma`

        :arg sparse: elect to use sparse matrices, default is **False**. If
            Scipy is not found, :class:`ImportError` is raised.
        :type sparse: bool

        :arg kdtree: elect to use KDTree for building Hessian matrix,
            default is **False** since KDTree method is slower
        :type kdtree: bool

        Instances of :class:`Gamma` classes and custom functions are
        accepted as *gamma* argument.

        When Scipy is available, user can select to use sparse matrices for
        efficient usage of memory at the cost of computation speed."""

        try:
            coords = (coords._getCoords() if hasattr(coords, '_getCoords') else
                      coords.getCoords())
        except AttributeError:
            try:
                checkCoords(coords)
            except TypeError:
                raise TypeError('coords must be a Numpy array or an object '
                                'with `getCoords` method')

        cutoff, g, gamma = checkENMParameters(cutoff, gamma)
        self._reset()
        self._cutoff = cutoff
        self._gamma = g
        self._coords = coords
        n_atoms = coords.shape[0]

        dof = n_atoms * 3
        LOGGER.timeit('_anm_hessian')

        sparse = kwargs.get('sparse', False)
        if sparse:
            try:
                from scipy import sparse as scipy_sparse
            except ImportError:
                raise ImportError('failed to import scipy.sparse, which  is '
                                  'required for sparse matrix calculations')
            kirchhoff = scipy_sparse.lil_matrix((n_atoms, n_atoms))
            hessian = scipy_sparse.lil_matrix((dof, dof))
        else:
            kirchhoff = np.zeros((n_atoms, n_atoms), 'd')
            hessian = np.zeros((dof, dof), float)

        if kwargs.get('kdtree', False):
            LOGGER.info('Using KDTree for building the Hessian.')
            kdtree = KDTree(coords)
            kdtree.search(cutoff)
            for i, j in kdtree.getIndices():
                i2j = coords[j] - coords[i]
                dist2 = np.dot(i2j, i2j)
                g = gamma(dist2, i, j)
                super_element = np.outer(i2j, i2j) * (- g / dist2)
                res_i3 = i*3
                res_i33 = res_i3+3
                res_j3 = j*3
                res_j33 = res_j3+3
                hessian[res_i3:res_i33, res_j3:res_j33] = super_element
                hessian[res_j3:res_j33, res_i3:res_i33] = super_element
                hessian[res_i3:res_i33, res_i3:res_i33] = \
                    hessian[res_i3:res_i33, res_i3:res_i33] - super_element
                hessian[res_j3:res_j33, res_j3:res_j33] = \
                    hessian[res_j3:res_j33, res_j3:res_j33] - super_element
                kirchhoff[i, j] = -g
                kirchhoff[j, i] = -g
                kirchhoff[i, i] = kirchhoff[i, i] + g
                kirchhoff[j, j] = kirchhoff[j, j] + g
        else:
            cutoff2 = cutoff * cutoff
            for i in range(n_atoms):
                res_i3 = i*3
                res_i33 = res_i3+3
                i_p1 = i+1
                i2j_all = coords[i_p1:, :] - coords[i]
                for j, dist2 in enumerate((i2j_all ** 2).sum(1)):
                    if dist2 > cutoff2:
                        continue
                    i2j = i2j_all[j]
                    j += i_p1
                    g = gamma(dist2, i, j)
                    res_j3 = j*3
                    res_j33 = res_j3+3
                    super_element = np.outer(i2j, i2j) * (- g / dist2)
                    hessian[res_i3:res_i33, res_j3:res_j33] = super_element
                    hessian[res_j3:res_j33, res_i3:res_i33] = super_element
                    hessian[res_i3:res_i33, res_i3:res_i33] = \
                        hessian[res_i3:res_i33, res_i3:res_i33] - super_element
                    hessian[res_j3:res_j33, res_j3:res_j33] = \
                        hessian[res_j3:res_j33, res_j3:res_j33] - super_element
                    kirchhoff[i, j] = -g
                    kirchhoff[j, i] = -g
                    kirchhoff[i, i] = kirchhoff[i, i] + g
                    kirchhoff[j, j] = kirchhoff[j, j] + g

        if sparse:
            kirchhoff = kirchhoff.tocsr()
            hessian = hessian.tocsr()

        LOGGER.report('Hessian was built in %.2fs.', label='_anm_hessian')
        self._kirchhoff = kirchhoff
        self._hessian = hessian
        self._n_atoms = n_atoms
        self._dof = dof

    def calcModes(self, n_modes=20, zeros=False, turbo=True):
        """Calculate normal modes.  This method uses :func:`scipy.linalg.eigh`
        function to diagonalize the Hessian matrix. When Scipy is not found,
        :func:`numpy.linalg.eigh` is used.

        :arg n_modes: number of non-zero eigenvalues/vectors to calculate.
            If **None** or ``'all'`` is given, all modes will be calculated.
        :type n_modes: int or None, default is 20

        :arg zeros: If **True**, modes with zero eigenvalues will be kept.
        :type zeros: bool, default is **True**

        :arg turbo: Use a memory intensive, but faster way to calculate modes.
        :type turbo: bool, default is **True**
        """

        if self._hessian is None:
            raise ValueError('Hessian matrix is not built or set')
        if str(n_modes).lower() == 'all':
            n_modes = None
        assert n_modes is None or isinstance(n_modes, int) and n_modes > 0, \
            'n_modes must be a positive integer'
        assert isinstance(zeros, bool), 'zeros must be a boolean'
        assert isinstance(turbo, bool), 'turbo must be a boolean'
        self._clear()
        LOGGER.timeit('_anm_calc_modes')
        values, vectors, vars = solveEig(self._hessian, n_modes=n_modes, zeros=zeros, 
                                         turbo=turbo, is3d=True)
        self._eigvals = values
        self._array = vectors
        self._vars = vars
        self._trace = self._vars.sum()

        self._n_modes = len(self._eigvals)
        LOGGER.report('{0} modes were calculated in %.2fs.'
                     .format(self._n_modes), label='_anm_calc_modes')

    
    def setEigens(self, vectors, values=None):
        self._clear()
        super(ANMBase, self).setEigens(vectors, values)
        

class ANM(ANMBase, GNMBase):

    """Class for Anisotropic Network Model (ANM) analysis of proteins
    ([PD00]_, [ARA01]_).

    See a usage example in :ref:`anm`.

    .. [PD00] Doruker P, Atilgan AR, Bahar I. Dynamics of proteins predicted by
       molecular dynamics simulations and analytical approaches: Application to
       a-amylase inhibitor. *Proteins* **2000** 40:512-524.

    .. [ARA01] Atilgan AR, Durrell SR, Jernigan RL, Demirel MC, Keskin O,
       Bahar I. Anisotropy of fluctuation dynamics of proteins with an
       elastic network model. *Biophys. J.* **2001** 80:505-515."""


    def __init__(self, name='Unknown'):

        super(ANM, self).__init__(name)


def calcANM(pdb, selstr='calpha', cutoff=15., gamma=1., n_modes=20,
            zeros=False, title=None):
    """Returns an :class:`ANM` instance and atoms used for the calculations.
    By default only alpha carbons are considered, but selection string helps
    selecting a subset of it.  *pdb* can be a PDB code, :class:`.Atomic` 
    instance, or a Hessian matrix (:class:`~numpy.ndarray`)."""

    if isinstance(pdb, np.ndarray):
        H = pdb
        if title is None:
            title = 'Unknown'
        anm = ANM(title)
        anm.setHessian(H)
        anm.calcModes(n_modes, zeros)
        
        return anm
        
    else:
        if isinstance(pdb, str):
            ag = parsePDB(pdb)
            if title is None:
                title = ag.getTitle()
        elif isinstance(pdb, Atomic):
            ag = pdb
            if title is None:
                if isinstance(pdb, AtomGroup):
                    title = ag.getTitle()
                else:
                    title = ag.getAtomGroup().getTitle()
        else:
            raise TypeError('pdb must be an atomic class, not {0}'
                            .format(type(pdb)))
        
        anm = ANM(title)
        sel = ag.select(selstr)
        anm.buildHessian(sel, cutoff, gamma)
        anm.calcModes(n_modes, zeros)
    
        return anm, sel
