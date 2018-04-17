# -*- coding: utf-8 -*-
"""This module defines plotting functions for protein dynamics analysis.

Plotting functions are called by the name of the plotted data/property
and are prefixed with ``show``.  Function documentations refers to the
:mod:`matplotlib.pyplot` function utilized for actual plotting.  Arguments
and keyword arguments are passed to the Matplotlib functions."""

from collections import defaultdict

import numpy as np

from prody import LOGGER, SETTINGS, PY3K
from prody.utilities import showFigure, addBreaks

from .nma import NMA
from .gnm import GNMBase
from .mode import Mode, VectorBase, Vector
from .modeset import ModeSet
from .analysis import calcSqFlucts, calcProjection
from .analysis import calcCrossCorr, calcPairDeformationDist
from .analysis import calcFractVariance, calcCrossProjection 
from .perturb import calcPerturbResponse, calcPerturbResponseProfiles
from .compare import calcOverlap
from prody.atomic import AtomGroup, Selection

__all__ = ['showContactMap', 'showCrossCorr',
           'showCumulOverlap', 'showFractVars',
           'showCumulFractVars', 'showMode',
           'showOverlap', 'showOverlaps', 'showOverlapTable', 
           'showProjection', 'showCrossProjection', 
           'showEllipsoid', 'showSqFlucts', 'showScaledSqFlucts', 
           'showNormedSqFlucts', 'resetTicks',
           'showDiffMatrix','showMechStiff','showNormDistFunct',
           'showPairDeformationDist','showMeanMechStiff', 
           'showPerturbResponse', 'showPerturbResponseProfiles',
           'showAtomicMatrix', 'showAtomicLine', 'showTree', 
           'showTree_networkx', 'showDomainBar']


def showEllipsoid(modes, onto=None, n_std=2, scale=1., *args, **kwargs):
    """Show an ellipsoid using  :meth:`~mpl_toolkits.mplot3d.Axes3D
    .plot_wireframe`.

    Ellipsoid volume gives an analytical view of the conformational space that
    given modes describe.

    :arg modes: 3 modes for which ellipsoid will be drawn.
    :type modes: :class:`.ModeSet`, :class:`.PCA`, :class:`.ANM`, :class:`.NMA`

    :arg onto: 3 modes onto which ellipsoid will be projected.
    :type modes: :class:`.ModeSet`, :class:`.PCA`, :class:`.ANM`, :class:`.NMA`

    :arg n_std: Number of standard deviations to scale the ellipsoid.
    :type n_std: float

    :arg scale: Used for scaling the volume of ellipsoid. This can be
        obtained from :func:`.sampleModes`.
    :type scale: float"""

    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    if not isinstance(modes, (NMA, ModeSet)):
        raise TypeError('modes must be a NMA or ModeSet instance, '
                        'not {0}'.format(type(modes)))
    if not modes.is3d():
        raise ValueError('modes must be from a 3-dimensional model')
    if len(modes) != 3:
        raise ValueError('length of modes is not equal to 3')
    if onto is not None:
        if not isinstance(onto, (NMA, ModeSet)):
            raise TypeError('onto must be a NMA or ModeSet instance, '
                            'not {0}'.format(type(onto)))
        if not onto.is3d():
            raise ValueError('onto must be from a 3-dimensional model')
        if len(onto) != 3:
            raise ValueError('length of onto is not equal to 3')
        if onto.numAtoms() != modes.numAtoms():
            raise ValueError('modes and onto must have same number of atoms')

    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)


    var = modes.getVariances()
    #randn = np.random.standard_normal((1000, 3))
    #coef = ((randn ** 2 * var).sum(1) ** 0.5).mean()
    #scale=float(n_std)*modes.numAtoms()**.5 * float(rmsd) / coef * var **.5
    scale = float(n_std) * scale * var ** 0.5
    #scale=float(n_std)*modes.numAtoms()**.5*float(rmsd)/var.sum()**.5*var**.5

    x = scale[0] * np.outer(np.cos(u), np.sin(v))
    y = scale[1] * np.outer(np.sin(u), np.sin(v))
    z = scale[2] * np.outer(np.ones(np.size(u)), np.cos(v))
    if onto is not None:
        change_of_basis = np.dot(modes._getArray().T, onto._getArray())

        xyz = np.array([x.flatten(), y.flatten(), z.flatten()])
        xyz = np.dot(xyz.T, change_of_basis)
        x = xyz[:,0].reshape((100,100))
        y = xyz[:,1].reshape((100,100))
        z = xyz[:,2].reshape((100,100))

    cf = plt.gcf()
    show = None
    for child in cf.get_children():
        if isinstance(child, Axes3D):
            show = child
            break
    if show is None:
        show = Axes3D(cf)
    show.plot_wireframe(x, y, z, rstride=6, cstride=6, *args, **kwargs)
    if onto is not None:
        onto = list(onto)
        show.set_xlabel('Mode {0} coordinate'.format(int(onto[0])+1))
        show.set_ylabel('Mode {0} coordinate'.format(int(onto[1])+1))
        show.set_zlabel('Mode {0} coordinate'.format(int(onto[2])+1))
    else:
        modes = list(modes)
        show.set_xlabel('Mode {0} coordinate'.format(int(modes[0])+1))
        show.set_ylabel('Mode {0} coordinate'.format(int(modes[1])+1))
        show.set_zlabel('Mode {0} coordinate'.format(int(modes[2])+1))
    if SETTINGS['auto_show']:
        showFigure()
    return show


def showFractVars(modes, *args, **kwargs):
    """Show fraction of variances using :func:`~matplotlib.pyplot.bar`.  Note
    that mode indices are incremented by 1."""

    import matplotlib.pyplot as plt
    if not isinstance(modes, (ModeSet, NMA)):
        raise TypeError('modes must be NMA, or ModeSet, not {0}'
                        .format(type(modes)))
    
    if SETTINGS['auto_show']:
        plt.figure()

    fracts = calcFractVariance(modes)
    fracts = [(int(mode), fract) for mode, fract in zip(modes, fracts)]
    fracts = np.array(fracts)
    show = plt.bar(fracts[:,0]+0.5, fracts[:,1], *args, **kwargs)
    axis = list(plt.axis())
    axis[0] = 0.5
    axis[2] = 0
    axis[3] = 1
    plt.axis(axis)
    plt.xlabel('Mode index')
    plt.ylabel('Fraction of variance')
    if SETTINGS['auto_show']:
        showFigure()
    return show


def showCumulFractVars(modes, *args, **kwargs):
    """Show fraction of variances of *modes* using :func:`~matplotlib.pyplot.
    plot`.  Note that mode indices are incremented by 1.  See also
    :func:`.showFractVars` function."""

    import matplotlib.pyplot as plt
    if not isinstance(modes, (Mode, NMA, ModeSet)):
        raise TypeError('modes must be a Mode, NMA, or ModeSet instance, '
                        'not {0}'.format(type(modes)))
    if isinstance(modes, Mode):
        indices = modes.getIndices() + 0.5
        modes = [modes]
    elif isinstance(modes, ModeSet):
        indices = modes.getIndices() + 0.5
    else:
        indices = np.arange(len(modes)) + 0.5
    
    if SETTINGS['auto_show']:
        plt.figure()

    fracts = calcFractVariance(modes).cumsum()
    show = plt.plot(indices, fracts, *args, **kwargs)
    axis = list(plt.axis())
    axis[0] = 0.5
    axis[2] = 0
    axis[3] = 1
    plt.axis(axis)
    plt.xlabel('Mode index')
    plt.ylabel('Fraction of variance')
    if SETTINGS['auto_show']:
        showFigure()
    return show


def showProjection(ensemble, modes, *args, **kwargs):
    """Show a projection of conformational deviations onto up to three normal
    modes from the same model.

    :arg ensemble: an ensemble, trajectory or a conformation for which
        deviation(s) will be projected, or a deformation vector
    :type ensemble: :class:`.Ensemble`, :class:`.Conformation`,
        :class:`.Vector`, :class:`.Trajectory`

    :arg modes: up to three normal modes
    :type modes: :class:`.Mode`, :class:`.ModeSet`, :class:`.NMA`

    :arg color: a color name or a list of color names or values, 
        default is ``'blue'``
    :type color: str, list

    :arg label: label or a list of labels
    :type label: str, list

    :arg marker: a marker or a list of markers, default is ``'o'``
    :type marker: str, list

    :arg linestyle: line style, default is ``'None'``
    :type linestyle: str

    :arg text: list of text labels, one for each conformation
    :type text: list

    :arg fontsize: font size for text labels
    :type fontsize: int

    The projected values are by default converted to RMSD.  Pass ``rmsd=False``
    to use projection itself.

    Matplotlib function used for plotting depends on the number of modes:

      * 1 mode: :func:`~matplotlib.pyplot.hist`
      * 2 modes: :func:`~matplotlib.pyplot.scatter`
      * 3 modes: :meth:`~mpl_toolkits.mplot3d.Axes3D.scatter`"""

    import matplotlib.pyplot as plt

    cmap = kwargs.pop('cmap', None)

    if SETTINGS['auto_show']:
        fig = plt.figure()
 
    projection = calcProjection(ensemble, modes, kwargs.pop('rmsd', True), kwargs.pop('norm', True))

    if projection.ndim == 1 or projection.shape[1] == 1:
        show = plt.hist(projection.flatten(), *args, **kwargs)
        plt.xlabel('{0} coordinate'.format(str(modes)))
        plt.ylabel('Number of conformations')
        return show
    elif projection.shape[1] > 3:
        raise ValueError('Projection onto up to 3 modes can be shown. '
                         'You have given {0} mode.'.format(len(modes)))

    num = projection.shape[0]

    markers = kwargs.pop('marker', 'o')
    if isinstance(markers, str) or markers is None:
        markers = [markers] * num
    elif isinstance(markers, list):
        if len(markers) != num:
            raise ValueError('length of marker must be {0}'.format(num))
    else:
        raise TypeError('marker must be a string or a list')

    colors = kwargs.pop('color', 'blue')
    if isinstance(colors, str) or colors is None:
        colors = [colors] * num
    elif isinstance(colors, list):
        if len(colors) != num:
            raise ValueError('length of color must be {0}'.format(num))
    else:
        raise TypeError('color must be a string or a list')

    labels = kwargs.pop('label', None)
    if isinstance(labels, str) or labels is None:
        labels = [labels] * num
    elif isinstance(labels, list):
        if len(labels) != num:
            raise ValueError('length of label must be {0}'.format(num))
    elif labels is not None:
        raise TypeError('label must be a string or a list')

    kwargs['linestyle'] = kwargs.pop('linestyle', None) or kwargs.pop('ls', 'None')

    texts = kwargs.pop('text', None)
    if texts:
        if not isinstance(texts, list):
            raise TypeError('text must be a list')
        elif len(texts) != num:
            raise TypeError('length of text must be {0}'.format(num))
        size = kwargs.pop('fontsize', None) or kwargs.pop('size', None)

    indict = defaultdict(list)
    for i, opts in enumerate(zip(markers, colors, labels)):  # PY3K: OK
        indict[opts].append(i)

    modes = [m for m in modes]
    if len(modes) == 2: 
        plot = plt.plot
        show = plt.gcf()
        text = plt.text
    else: 
        from mpl_toolkits.mplot3d import Axes3D
        cf = plt.gcf()
        show = None
        for child in cf.get_children():
            if isinstance(child, Axes3D):
                show = child
                break
        if show is None:
            show = Axes3D(cf)
        plot = show.plot
        text = show.text

    args = list(args)
    for opts, indices in indict.items():  # PY3K: OK
        marker, color, label = opts
        kwargs['marker'] = marker
        if cmap is not None:
            color = cmap.colors[int(float(color))]
        kwargs['c'] = color

        if label:
            kwargs['label'] = label
        else:
            kwargs.pop('label', None)

        plot(*(list(projection[indices].T) + args), **kwargs)

    if texts:
        kwargs = {}
        if size:
            kwargs['size'] = size
        for args in zip(*(list(projection.T) + [texts])):
            text(*args, **kwargs)

    if len(modes) == 2:
        plt.xlabel('{0} coordinate'.format(int(modes[0])+1))
        plt.ylabel('{0} coordinate'.format(int(modes[1])+1))
    elif len(modes) == 3:
        show.set_xlabel('Mode {0} coordinate'.format(int(modes[0])+1))
        show.set_ylabel('Mode {0} coordinate'.format(int(modes[1])+1))
        show.set_zlabel('Mode {0} coordinate'.format(int(modes[2])+1))

    if SETTINGS['auto_show']:
        showFigure()

    return show


def showCrossProjection(ensemble, mode_x, mode_y, scale=None, *args, **kwargs):
    """Show a projection of conformational deviations onto modes from
    different models using :func:`~matplotlib.pyplot.plot`.  This function
    differs from :func:`.showProjection` by accepting modes from two different
    models.

    :arg ensemble: an ensemble or a conformation for which deviation(s) will be
        projected, or a deformation vector
    :type ensemble: :class:`.Ensemble`, :class:`.Conformation`,
        :class:`.Vector`, :class:`.Trajectory`
    :arg mode_x: projection onto this mode will be shown along x-axis
    :type mode_x: :class:`.Mode`, :class:`.Vector`
    :arg mode_y: projection onto this mode will be shown along y-axis
    :type mode_y: :class:`.Mode`, :class:`.Vector`
    :arg scale: scale width of the projection onto mode ``x`` or ``y``,
        best scaling factor will be calculated and printed on the console,
        absolute value of scalar makes the with of two projection same,
        sign of scalar makes the projections yield a positive correlation
    :type scale: str
    :arg scalar: scalar factor for projection onto selected mode
    :type scalar: float
    :arg color: a color name or a list of color name, default is ``'blue'``
    :type color: str, list
    :arg label: label or a list of labels
    :type label: str, list
    :arg marker: a marker or a list of markers, default is ``'o'``
    :type marker: str, list
    :arg linestyle: line style, default is ``'None'``
    :type linestyle: str
    :arg text: list of text labels, one for each conformation
    :type text: list
    :arg fontsize: font size for text labels
    :type fontsize: int


    The projected values are by default converted to RMSD.  Pass ``rmsd=False``
    to calculate raw projection values.  See :ref:`pca-xray-plotting` for a
    more elaborate example."""

    import matplotlib.pyplot as plt

    if SETTINGS['auto_show']:
        plt.figure()

    norm = kwargs.pop('norm', True)
    xcoords, ycoords = calcCrossProjection(ensemble, mode_x, mode_y,
                                           scale=scale, norm=norm, **kwargs)

    num = len(xcoords)

    markers = kwargs.pop('marker', 'o')
    if isinstance(markers, str) or markers is None:
        markers = [markers] * num
    elif isinstance(markers, list):
        if len(markers) != num:
            raise ValueError('length of marker must be {0}'.format(num))
    else:
        raise TypeError('marker must be a string or a list')

    colors = kwargs.pop('color', 'blue')
    if isinstance(colors, str) or colors is None:
        colors = [colors] * num
    elif isinstance(colors, list):
        if len(colors) != num:
            raise ValueError('length of color must be {0}'.format(num))
    else:
        raise TypeError('color must be a string or a list')

    labels = kwargs.pop('label', None)
    if isinstance(labels, str) or labels is None:
        labels = [labels] * num
    elif isinstance(labels, list):
        if len(labels) != num:
            raise ValueError('length of label must be {0}'.format(num))
    elif labels is not None:
        raise TypeError('label must be a string or a list')

    kwargs['ls'] = kwargs.pop('linestyle', None) or kwargs.pop('ls', 'None')

    texts = kwargs.pop('text', None)
    if texts:
        if not isinstance(texts, list):
            raise TypeError('text must be a list')
        elif len(texts) != num:
            raise TypeError('length of text must be {0}'.format(num))
        size = kwargs.pop('fontsize', None) or kwargs.pop('size', None)

    indict = defaultdict(list)
    for i, opts in enumerate(zip(markers, colors, labels)):  # PY3K: OK
        indict[opts].append(i)

    for opts, indices in indict.items():  # PY3K: OK
        marker, color, label = opts
        kwargs['marker'] = marker
        kwargs['color'] = color
        if label:
            kwargs['label'] = label
        else:
            kwargs.pop('label', None)
        show = plt.plot(xcoords[indices], ycoords[indices], *args, **kwargs)
    if texts:
        kwargs = {}
        if size:
            kwargs['size'] = size
        for x, y, t in zip(xcoords, ycoords, texts):
            plt.text(x, y, t, **kwargs)
    plt.xlabel('{0} coordinate'.format(mode_x))
    plt.ylabel('{0} coordinate'.format(mode_y))
    if SETTINGS['auto_show']:
        showFigure()
    return show


def showOverlapTable(modes_x, modes_y, **kwargs):
    """Show overlap table using :func:`~matplotlib.pyplot.pcolor`.  *modes_x*
    and *modes_y* are sets of normal modes, and correspond to x and y axes of
    the plot.  Note that mode indices are incremented by 1.  List of modes
    is assumed to contain a set of contiguous modes from the same model.

    Default arguments for :func:`~matplotlib.pyplot.pcolor`:

      * ``cmap=plt.cm.jet``
      * ``norm=matplotlib.colors.Normalize(0, 1)``"""

    import matplotlib.pyplot as plt
    import matplotlib

    overlap = abs(calcOverlap(modes_y, modes_x))
    if overlap.ndim == 0:
        overlap = np.array([[overlap]])
    elif overlap.ndim == 1:
        overlap = overlap.reshape((modes_y.numModes(), modes_x.numModes()))

    cmap = kwargs.pop('cmap', plt.cm.jet)
    norm = kwargs.pop('norm', matplotlib.colors.Normalize(0, 1))

    if SETTINGS['auto_show']:
        plt.figure()
    show = (plt.pcolor(overlap, cmap=cmap, norm=norm, **kwargs),
            plt.colorbar())
    x_range = np.arange(1, modes_x.numModes() + 1)
    plt.xticks(x_range-0.5, x_range)
    plt.xlabel(str(modes_x))
    y_range = np.arange(1, modes_y.numModes() + 1)
    plt.yticks(y_range-0.5, y_range)
    plt.ylabel(str(modes_y))
    plt.axis([0, modes_x.numModes(), 0, modes_y.numModes()])
    if SETTINGS['auto_show']:
        showFigure()
    return show


def showCrossCorr(modes, *args, **kwargs):
    """Show cross-correlations using :func:`~matplotlib.pyplot.imshow`.  By
    default, *origin=lower* and *interpolation=bilinear* keyword  arguments
    are passed to this function, but user can overwrite these parameters.
    See also :func:`.calcCrossCorr`."""

    import matplotlib.pyplot as plt
    if SETTINGS['auto_show']:
        plt.figure()

    arange = np.arange(modes.numAtoms())
    cross_correlations = np.zeros((arange[-1]+2, arange[-1]+2))
    cross_correlations[arange[0]+1:,
                       arange[0]+1:] = calcCrossCorr(modes)
    if not 'interpolation' in kwargs:
        kwargs['interpolation'] = 'bilinear'
    if not 'origin' in kwargs:
        kwargs['origin'] = 'lower'
    show = plt.imshow(cross_correlations, *args, **kwargs), plt.colorbar()
    plt.axis([arange[0]+0.5, arange[-1]+1.5, arange[0]+0.5, arange[-1]+1.5])
    plt.title('Cross-correlations for {0}'.format(str(modes)))
    plt.xlabel('Indices')
    plt.ylabel('Indices')
    if SETTINGS['auto_show']:
        showFigure()
    return show


def showMode(mode, *args, **kwargs):
    """Show mode array using :func:`~matplotlib.pyplot.plot`."""
    
    import matplotlib.pyplot as plt

    show_hinges = kwargs.pop('show_hinges', False)
    show_zero = kwargs.pop('show_zero', True)
    overlay_chains = kwargs.get('overlay_chains',False)
    atoms = kwargs.get('atoms',None)

    if not isinstance(mode, (Mode, Vector)):
        raise TypeError('mode must be a Mode or Vector instance, '
                        'not {0}'.format(type(mode)))
    if mode.is3d():
        a3d = mode.getArrayNx3()
        show = []
        show.append(plt.plot(a3d[:, 0], *args, label='x-component', **kwargs))
        show.append(plt.plot(a3d[:, 1], *args, label='y-component', **kwargs))
        show.append(plt.plot(a3d[:, 2], *args, label='z-component', **kwargs))

        if atoms is not None:
            plt.title(str(mode))
        else:
            plt.title(str(mode))
    else:
        a1d = mode._getArray()
        show = plt.plot(a1d, *args, **kwargs)
        if show_hinges and isinstance(mode, Mode):
            hinges = mode.getHinges()
            if hinges is not None:
                if atoms is not None:
                    if overlay_chains:
                        n = 0
                        chain_colors = 'gcmyrwbk'
                        for i in atoms.getHierView().iterChains():
                            for hinge in hinges:
                                if i.getResindices()[0] < hinge < i.getResindices()[-1]:
                                    plt.plot(hinge - i.getResindices()[0], \
                                                 a1d[hinge], '*', color=chain_colors[n], \
                                                 markeredgecolor='k', markersize=10)
                            n += 1
                    else:
                        plt.plot(hinges, a1d[hinges], 'r*')
                else:
                    plt.plot(hinges, a1d[hinges], 'r*')
        if atoms is not None:
            plt.title(str(mode))
        else:
            plt.title(str(mode))
    if show_zero:
        if not mode.is3d():
            if atoms is not None:
                plt.plot(plt.xlim(), (0,0), '--', color='grey')
            else:
                plt.plot(plt.xlim(), (0,0), '--', color='grey')
        else:
            plt.plot(plt.xlim(), (0,0), '--', color='grey')
    if SETTINGS['auto_show']:
        showFigure()
    return show


def showSqFlucts(modes, *args, **kwargs):
    """Show square fluctuations using :func:`~matplotlib.pyplot.plot`.  See
    also :func:`.calcSqFlucts`."""

    import matplotlib.pyplot as plt
    show_hinge = kwargs.pop('hinge', False)
    sqf = calcSqFlucts(modes)
    if not 'label' in kwargs:
        kwargs['label'] = str(modes)

    atoms = kwargs.get('atoms', None)
    show = showAtomicLine(sqf, *args, atoms=atoms, **kwargs)
    plt.ylabel('Square fluctuations')
    plt.title(str(modes))
    if show_hinge and not modes.is3d():
        hinges = modes.getHinges()
        if hinges is not None:
            plt.plot(hinges, sqf[hinges], 'r*')
    if SETTINGS['auto_show']:
        showFigure()
    return show


def showScaledSqFlucts(modes, *args, **kwargs):
    """Show scaled square fluctuations using :func:`~matplotlib.pyplot.plot`.
    Modes or mode sets given as additional arguments will be scaled to have
    the same mean squared fluctuations as *modes*."""

    import matplotlib.pyplot as plt
    sqf = calcSqFlucts(modes)
    mean = sqf.mean()
    args = list(args)
    modesarg = []
    i = 0
    while i < len(args):
        if isinstance(args[i], (VectorBase, ModeSet, NMA)):
            modesarg.append(args.pop(i))
        else:
            i += 1
    show = plt.plot(sqf, *args, label=str(modes), **kwargs)
    plt.xlabel('Indices')
    plt.ylabel('Square fluctuations')
    for modes in modesarg:
        sqf = calcSqFlucts(modes)
        scalar = mean / sqf.mean()
        show.append(plt.plot(sqf * scalar, *args,
                             label='{0} (x{1:.2f})'.format(str(modes), scalar),
                             **kwargs))
    if SETTINGS['auto_show']:
        showFigure()
    return show


def showNormedSqFlucts(modes, *args, **kwargs):
    """Show normalized square fluctuations via :func:`~matplotlib.pyplot.plot`.
    """

    import matplotlib.pyplot as plt
    sqf = calcSqFlucts(modes)
    args = list(args)
    modesarg = []
    i = 0
    while i < len(args):
        if isinstance(args[i], (VectorBase, ModeSet, NMA)):
            modesarg.append(args.pop(i))
        else:
            i += 1
    show = plt.plot(sqf/(sqf**2).sum()**0.5, *args,
                     label='{0}'.format(str(modes)), **kwargs)
    plt.xlabel('Indices')
    plt.ylabel('Square fluctuations')
    for modes in modesarg:
        sqf = calcSqFlucts(modes)
        show.append(plt.plot(sqf/(sqf**2).sum()**0.5, *args,
                    label='{0}'.format(str(modes)), **kwargs))
    if SETTINGS['auto_show']:
        showFigure()
    return show


def showContactMap(enm, *args, **kwargs):
    """Show Kirchhoff matrix using :func:`~matplotlib.pyplot.spy`."""

    import matplotlib.pyplot as plt
    if SETTINGS['auto_show']:
        plt.figure()
        
    if not isinstance(enm, GNMBase):
        raise TypeError('model argument must be an ENM instance')
    kirchhoff = enm.getKirchhoff()
    if kirchhoff is None:
        LOGGER.warning('kirchhoff matrix is not set')
        return None
    show = plt.spy(kirchhoff, *args, **kwargs)
    plt.title('{0} contact map'.format(enm.getTitle()))
    plt.xlabel('Residue index')
    plt.ylabel('Residue index')
    if SETTINGS['auto_show']:
        showFigure()
    return show


def showOverlap(mode, modes, *args, **kwargs):
    """Show overlap :func:`~matplotlib.pyplot.bar`.

    :arg mode: a single mode/vector
    :type mode: :class:`.Mode`, :class:`.Vector`
    :arg modes: multiple modes
    :type modes: :class:`.ModeSet`, :class:`.ANM`, :class:`.GNM`, :class:`.PCA`
    """

    import matplotlib.pyplot as plt

    if SETTINGS['auto_show']:
        plt.figure()

    if not isinstance(mode, (Mode, Vector)):
        raise TypeError('mode must be Mode or Vector, not {0}'
                        .format(type(mode)))
    if not isinstance(modes, (NMA, ModeSet)):
        raise TypeError('modes must be NMA or ModeSet, not {0}'
                        .format(type(modes)))
    overlap = abs(calcOverlap(mode, modes))
    if isinstance(modes, NMA):
        arange = np.arange(0.5, len(modes)+0.5)
    else:
        arange = modes.getIndices() + 0.5
    show = plt.bar(arange, overlap, *args, **kwargs)
    plt.title('Overlap with {0}'.format(str(mode)))
    plt.xlabel('{0} mode index'.format(modes))
    plt.ylabel('Overlap')
    if SETTINGS['auto_show']:
        showFigure()
    return show

showOverlaps = showOverlap

def showCumulOverlap(mode, modes, *args, **kwargs):
    """Show cumulative overlap using :func:`~matplotlib.pyplot.plot`.

    :type mode: :class:`.Mode`, :class:`.Vector`
    :arg modes: multiple modes
    :type modes: :class:`.ModeSet`, :class:`.ANM`, :class:`.GNM`, :class:`.PCA`
    """

    import matplotlib.pyplot as plt
    if not isinstance(mode, (Mode, Vector)):
        raise TypeError('mode must be NMA, ModeSet, Mode or Vector, not {0}'
                        .format(type(mode)))
    if not isinstance(modes, (NMA, ModeSet)):
        raise TypeError('modes must be NMA, ModeSet, or Mode, not {0}'
                        .format(type(modes)))
    cumov = (calcOverlap(mode, modes) ** 2).cumsum() ** 0.5
    if isinstance(modes, NMA):
        arange = np.arange(0.5, len(modes)+0.5)
    else:
        arange = modes.getIndices() + 0.5
    
    if SETTINGS['auto_show']:
        plt.figure()
    show = plt.plot(arange, cumov, *args, **kwargs)
    plt.title('Cumulative overlap with {0}'.format(str(mode)))
    plt.xlabel('{0} mode index'.format(modes))
    plt.ylabel('Cumulative overlap')
    plt.axis((arange[0]-0.5, arange[-1]+0.5, 0, 1))
    if SETTINGS['auto_show']:
        showFigure()
    return show


def resetTicks(x, y=None):
    """Reset X (and Y) axis ticks using values in given *array*.  Ticks in the
    current figure should not be fractional values for this function to work as
    expected."""

    import matplotlib.pyplot as plt
    if x is not None:
        try:
            xticks = plt.xticks()[0]
            xlist = list(xticks.astype(int))
            if xlist[-1] > len(x):
                xlist.pop()
            if xlist:
                xlist = list(x[xlist])
                plt.xticks(xticks, xlist + [''] * (len(xticks) - len(xlist)))
        except:
            LOGGER.warning('xticks could not be reset.')
    if y is not None:
        try:
            yticks = plt.yticks()[0]
            ylist = list(yticks.astype(int))
            if ylist[-1] > len(y):
                ylist.pop()
            if ylist:
                ylist = list(y[ylist])
                plt.yticks(yticks, ylist + [''] * (len(yticks) - len(ylist)))
        except:
            LOGGER.warning('xticks could not be reset.')


def showDiffMatrix(matrix1, matrix2, *args, **kwargs):
    """Show the difference between two cross-correlation matrices from
    different models. For given *matrix1* and *matrix2* show the difference
    between them in the form of (matrix2 - matrix1) and plot the difference
    matrix using :func:`showAtomicMatrix`. When :class:`.NMA` models
    are passed instead of matrices, the functions could call
    :func:`.calcCrossCorr` function to calculate the matrices for given modes.

    To display the absolute values in the difference matrix, user could set
    *abs* keyword argument **True**.

    By default, *origin=lower* and *interpolation=bilinear* keyword arguments
    are passed to this function, but user can overwrite these parameters.
    """

    import matplotlib.pyplot as plt
    try:
        dim1, shape1 = matrix1.ndim, matrix1.shape
    except AttributeError:
        matrix1 = calcCrossCorr(matrix1)
        dim1, shape1 = matrix1.ndim, matrix1.shape
    try:
        dim2, shape2 = matrix2.ndim, matrix2.shape
    except AttributeError:
        matrix2 = calcCrossCorr(matrix2)
        dim2, shape2 = matrix2.ndim, matrix2.shape
    if (not ((dim1 == dim2 == 2) and (shape1 == shape2))):
        raise ValueError('Matrices must have same square shape.')
    if shape1[0] * shape1[1] == 0:
        raise ValueError('There are no data in matrices.')
    diff = matrix2 - matrix1
    if not 'interpolation' in kwargs:
        kwargs['interpolation'] = 'bilinear'
    if not 'origin' in kwargs:
        kwargs['origin'] = 'lower'
    if kwargs.pop('abs', False):
        diff = np.abs(diff)
    if SETTINGS['auto_show']:
        plt.figure()
    show = showAtomicMatrix(diff, *args, **kwargs)
    #show.im3.axis([-.5, shape1[1] - .5, -.5, shape1[0] - .5])
    plt.title('Difference Matrix')
    if SETTINGS['auto_show']:
        showFigure()
    plt.xlabel('Indices')
    plt.ylabel('Indices')
    return show


def showMechStiff(model, coords, *args, **kwargs):
    """Show mechanical stiffness matrix using :func:`~matplotlib.pyplot.imshow`.
    By default, *origin=lower* keyword  arguments are passed to this function, 
    but user can overwrite these parameters."""

    import math
    import matplotlib
    import matplotlib.pyplot as plt
    arange = np.arange(model.numAtoms())
    model.buildMechStiff(coords)

    if not 'origin' in kwargs:
        kwargs['origin'] = 'lower'
    if 'jet_r' in kwargs:
        import matplotlib.cm as plt
        kwargs['jet_r'] = 'cmap=cm.jet_r'
        
    MechStiff = model.getStiffness()
    matplotlib.rcParams['font.size'] = '14'

    if SETTINGS['auto_show']:
        fig = plt.figure(num=None, figsize=(10,8), dpi=100, facecolor='w')
    vmin = math.floor(np.min(MechStiff[np.nonzero(MechStiff)]))
    vmax = round(np.amax(MechStiff),1)
    show = showAtomicMatrix(MechStiff, vmin=vmin, vmax=vmax, *args, **kwargs)
    plt.title('Mechanical Stiffness Matrix')# for {0}'.format(str(model)))
    plt.xlabel('Indices', fontsize='16')
    plt.ylabel('Indices', fontsize='16')
    if SETTINGS['auto_show']:
        showFigure()
    return show


def showNormDistFunct(model, coords, *args, **kwargs):
    """Show normalized distance fluctuation matrix using 
    :func:`~matplotlib.pyplot.imshow`. By default, *origin=lower* 
    keyword  arguments are passed to this function, 
    but user can overwrite these parameters."""

    import math
    import matplotlib
    import matplotlib.pyplot as plt
    normdistfunct = model.getNormDistFluct(coords)

    if not 'origin' in kwargs:
        kwargs['origin'] = 'lower'
        
    matplotlib.rcParams['font.size'] = '14'

    if SETTINGS['auto_show']:
        fig = plt.figure(num=None, figsize=(10,8), dpi=100, facecolor='w')
    vmin = math.floor(np.min(normdistfunct[np.nonzero(normdistfunct)]))
    vmax = round(np.amax(normdistfunct),1)
    show = showAtomicMatrix(normdistfunct, vmin=vmin, vmax=vmax, *args, **kwargs)
    #plt.clim(math.floor(np.min(normdistfunct[np.nonzero(normdistfunct)])), \
    #                                       round(np.amax(normdistfunct),1))
    plt.title('Normalized Distance Fluctution Matrix')
    plt.xlabel('Indices', fontsize='16')
    plt.ylabel('Indices', fontsize='16')
    if SETTINGS['auto_show']:
        showFigure()
    return show


def showPairDeformationDist(model, coords, ind1, ind2, *args, **kwargs):
    """Show distribution of deformations in distance contributed by each mode
    for selected pair of residues *ind1* *ind2*
    using :func:`~matplotlib.pyplot.plot`. """

    import matplotlib
    import matplotlib.pyplot as plt
    if not isinstance(model, NMA):
        raise TypeError('model must be a NMA instance, '
                        'not {0}'.format(type(model)))
    elif not model.is3d():
        raise TypeError('model must be a 3-dimensional NMA instance')
    elif len(model) == 0:
        raise ValueError('model must have normal modes calculated')
    elif model.getStiffness() is None:
        raise ValueError('model must have stiffness matrix calculated')

    d_pair = calcPairDeformationDist(model, coords, ind1, ind2)
    with plt.style.context('fivethirtyeight'):
        matplotlib.rcParams['font.size'] = '16'
        fig = plt.figure(num=None, figsize=(12,8), dpi=100, facecolor='w')
        #plt.title(str(model))
        plt.plot(d_pair[0], d_pair[1], 'k-', linewidth=1.5, *args, **kwargs)
        plt.xlabel('mode (k)', fontsize = '18')
        plt.ylabel('d$^k$' '($\AA$)', fontsize = '18')
    if SETTINGS['auto_show']:
        showFigure()
    return plt.show


def showMeanMechStiff(model, coords, header, chain='A', *args, **kwargs):
    """Show mean value of effective spring constant with secondary structure
    taken from MechStiff. Header is needed to obatin secondary structure range.
    Using ``'jet_r'`` as argument color map will be reverse (similar to VMD 
    program coding).
    """
    meanStiff = np.array([np.mean(model.getStiffness(), axis=0)])
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    fig=plt.figure(figsize=[18,6], facecolor='w', dpi=100)
    
    if 'jet_r' in kwargs:
       import matplotlib.cm as plt
       kwargs['jet_r'] = 'cmap=cm.jet_r'
    if 'nearest' in kwargs:
        kwargs['nearest'] = 'interpolation=nearest'

    with plt.style.context('fivethirtyeight'):
        ax = fig.add_subplot(111)
        matplotlib.rcParams['font.size'] = '24'
        plt.plot(np.arange(len(meanStiff[0]))+coords.getResnums()[0],meanStiff[0], 'k-', linewidth = 3)
        plt.xlim(coords.getResnums()[0], coords.getResnums()[-1])
        ax_top=round(np.max(meanStiff[0])+((np.max(meanStiff[0])-np.min(meanStiff[0]))/3))
        ax_bottom=np.floor(np.min(meanStiff[0]))
        LOGGER.info('The range of mean effective force constant is: {0} to {1}.'
                                           .format(min(meanStiff[0]), max(meanStiff[0])))
        plt.ylim(ax_bottom,ax_top)
        plt.xlabel('residue', fontsize = '22')
        plt.ylabel('mean $\kappa$ [a.u.]', fontsize = '22')

    ax = fig.add_subplot(411, aspect='equal')
    plt.imshow(meanStiff, *args, **kwargs)
    header_ss = header['sheet_range'] + header['helix_range']
    for i in range(len(header_ss)):
        if header_ss[i][1] == chain:
            beg = int(header_ss[i][-2])-coords.getResnums()[0]
            end = int(header_ss[i][-1])-coords.getResnums()[0]
            add_beg = end - beg
            if header_ss[i][0] == 'H':
                ax.add_patch(patches.Rectangle((beg+1,-0.7),add_beg,\
                1.4,fill=False, linestyle='solid',edgecolor='#b22683', linewidth=2))    
            elif header_ss[i][0] == 'E':
                if header_ss[i][2] == -1:    
                    ax.add_patch(patches.Arrow(beg+1,0,add_beg,0,width=4.65, \
                    fill=False, linestyle='solid',edgecolor='black', linewidth=2))
                else: 
                    ax.add_patch(patches.Arrow(end+1,0,add_beg*(-1),0,width=4.65, \
                    fill=False, linestyle='solid',edgecolor='black', linewidth=2))
    plt.axis('off')
    ax.set_ylim(-1.7,1.7)
    if SETTINGS['auto_show']:
        showFigure()
    return plt.show

def showPerturbResponse(**kwargs):
    """ Plot the PRS matrix with the profiles along the right and bottom.

    If no PRS matrix or profiles are provided, these will be calculated first
    using the provided options with a provided model (e.g. ANM, GNM or EDA).
    So as to obtain different sensors and effectors, normMatrix=True by default.

    If atoms are provided then residue numbers can be used from there.
    *model* and *atoms* must have the same number of atoms. *atoms* must be an
    :class:`.AtomGroup` instance.

    :arg prs_matrix: a perturbation response matrix
    :type prs_matrix: :class:`~numpy.array`

    :arg effectiveness: an effectiveness profile from a PRS matrix
    :type effectiveness: :class:`~numpy.array`

    :arg sensitivity: a sensitivity profile from a PRS matrix
    :type sensitivity: :class:`~numpy.array`

    :arg model: any object with a calcCovariance method
        e.g. :class:`.ANM` instance
    :type model: NMA

    :arg atoms: a :class: `AtomGroup` instance
    :type atoms: AtomGroup

    :arg returnData: whether to return data for further analysis
        default is False
    :type returnData: bool
    
    :arg percentile: percentile argument for showAtomicMatrix
    :type percentile: float

    Return values are prs_matrix, effectiveness, sensitivity, ax1, ax2, im, ax3, ax4
    The PRS matrix, effectiveness and sensitivity will not be returned if provided. 
    If returnData is False then only the last five objects are returned.
    """

    import matplotlib.pyplot as plt
    import matplotlib

    prs_matrix = kwargs.get('prs_matrix')
    effectiveness = kwargs.get('effectiveness')
    sensitivity = kwargs.get('sensitivity')
    model = kwargs.pop('model')
    atoms = kwargs.get('atoms')
    returnData = kwargs.pop('returnData', False)

    if atoms is None:

        if prs_matrix is None:
            if model is None:
                raise ValueError('Please provide a PRS matrix or model.')
            else:
                prs_matrix = calcPerturbResponse(model=model)

        if effectiveness is None or sensitivity is None:
            effectiveness, sensitivity = calcPerturbResponseProfiles(prs_matrix)
        else:
            returnData = False

        showMatrix_returns = showAtomicMatrix(prs_matrix, effectiveness, sensitivity, **kwargs)

    else:
        if not isinstance(atoms, AtomGroup) and not isinstance(atoms, Selection):
            raise TypeError('atoms must be an AtomGroup instance')
        elif model is not None and atoms.numAtoms() != model.numAtoms():
            raise ValueError('model and atoms must have the same number atoms')

        if prs_matrix is None: 
            if model is None:
                raise ValueError('Please provide a PRS matrix or model.')
            atoms, prs_matrix = calcPerturbResponse(model=model,atoms=atoms)

        if effectiveness is None or sensitivity is None:
            atoms, effectiveness, sensitivity = calcPerturbResponseProfiles(prs_matrix,atoms)

        showMatrix_returns = showAtomicMatrix(prs_matrix, effectiveness, sensitivity, **kwargs)

    if not returnData:
        return showMatrix_returns
    elif kwargs.get('prs_matrix') is not None:
       if atoms is not None:
           return atoms, effectiveness, sensitivity, showMatrix_returns
       else:
           return effectiveness, sensitivity, showMatrix_returns
    else:
       if atoms is not None:
           return atoms, prs_matrix, effectiveness, sensitivity, showMatrix_returns
       else:
           return prs_matrix, effectiveness, sensitivity, showMatrix_returns

def showPerturbResponseProfiles(prs_matrix,atoms=None,**kwargs):
    """Plot as a line graph the average response to perturbation of
    a particular residue (a row of a perturbation response matrix)
    or the average effect of perturbation of a particular residue
    (a column of a normalized perturbation response matrix).

    If no PRS matrix or profiles are provided, these will be calculated first
    using the provided options with a provided model (e.g. ANM, GNM or EDA).
    So as to obtain different sensitivity and effectiveness, normMatrix=True by default.

    If no residue number is given then the effectiveness and sensitivity
    profiles will be plotted instead. These two profiles are also returned
    as arrays for further analysis if they aren't already provided.

    :arg prs_matrix: a perturbation response matrix
    :type prs_matrix: ndarray

    :arg atoms: a :class: `AtomGroup` instance for matching 
        residue numbers and chain IDs. 
    :type atoms: AtomGroup

    :arg effectiveness: an effectiveness profile from a PRS matrix
    :type effectiveness: list

    :arg sensitivity: a sensitivity profile from a PRS matrix
    :type sensitivity: list

    :arg model: any object with a calcCovariance method
        e.g. :class:`.ANM` instance
        *model* and *atoms* must have the same number of atoms.
    :type model: NMA

    :arg chain: chain identifier for the residue of interest
        default is to make a plot for each chain in the protein
    :type chain: str

    :arg resnum: residue number for the residue of interest
    :type resnum: int

    :arg direction: the direction you want to use to read data out
        of the PRS matrix for plotting: the options are 'effect' or 'response'.
        Default is 'effect'.
        A row gives the effect on each residue of peturbing the specified 
        residue.
        A column gives the response of the specified residue to perturbing 
        each residue.
        If no residue number is provided then this option will be ignored
    :type direction: str

    :arg returnData: whether to return profiles for further analysis
        default is False
    :type returnProfiles: bool
    """
    from .perturb import PRSMatrixParseError

    model = kwargs.get('model')
    if not type(prs_matrix) is np.ndarray:
        if prs_matrix is None:
            if model is None:
                raise ValueError('Please provide a PRS matrix or model.')
            else:
                if kwargs.get('normMatrix') is None:
                    kwargs.set('normMatrix',True)
                prs_matrix = calcPerturbResponse(**kwargs)
        else:
            raise TypeError('Please provide a valid PRS matrix (as array).')

    if atoms is None:
        raise ValueError('Please provide an AtomGroup object for matching ' \
                         'residue numbers and chain IDs.')
    else:
        if not isinstance(atoms, AtomGroup) and not isinstance(atoms, Selection):
            raise TypeError('atoms must be an AtomGroup instance')
        elif model is not None and atoms.numAtoms() != model.numAtoms():
            raise ValueError('model and atoms must have the same number atoms')

    chain = kwargs.get('chain')
    hv = atoms.getHierView()
    chains = []
    for i in range(len(list(hv))):
        chainAg = list(hv)[i]
        chains.append(chainAg.getChids()[0])

    chains = np.array(chains)
    if chain is None:
        chain = ''.join(chains)

    resnum = kwargs.get('resnum', None)
    direction = kwargs.get('direction','effect')

    if resnum is not None: 
        timesNotFound = 0
        for n in range(len(chain)):
            if not chain[n] in chains:
                raise PRSMatrixParseError('Chain {0} was not found in chains'.format(chain[n]))

            chainNum = int(np.where(chains == chain[n])[0])
            chainAg = list(hv)[chainNum]
            if not resnum in chainAg.getResnums():
                LOGGER.info('A residue with number {0} was not found' \
                            ' in chain {1}. Continuing to next chain.' \
                            .format(resnum, chain[n]))
                timesNotFound += 1
                continue

        profiles = []
        for n in range(len(chain)):
            chainNum = int(np.where(chains == chain[n])[0])
            i = np.where(atoms.getResnums() == resnum)[0][chainNum-timesNotFound] 
            if direction is 'effect':
                profiles.append(prs_matrix[i,:])
            else:
                profiles.append(prs_matrix[:,i])

    else:
        effectiveness = kwargs.get('effectiveness')
        sensitivity = kwargs.get('sensitivity')
        if effectiveness is None or sensitivity is None:
            effectiveness, sensitivity = calcPerturbResponseProfiles(prs_matrix)
        profiles = [effectiveness, sensitivity]

    for profile in profiles:
        show = showAtomicLine(profile,atoms=atoms,**kwargs)

    returnData = kwargs.get('returnData',False)
    if returnData:
        return show, profiles
    else:
        return show

def _checkDomainBarParameter(domain_bar, defpos, atoms, label):
    show = atoms is not None
    pos = defpos

    if not show:
        return show, pos, atoms

    # check if the user wants to show or not
    from numbers import Number
    if isinstance(domain_bar, bool):
        show &= domain_bar
        pos = defpos
    elif isinstance(domain_bar, Number):
        show &= True    # this line does nothing but is left for readability
        pos = domain_bar

    # check if the domain bar can be shown or not
    try:
        data = atoms.getData(label)
        uniq = np.unique(data)
        if domain_bar is None:
            show &= len(uniq) > 1
    except:
        if domain_bar is None:
            show &= False
        if show:
            raise ValueError('A {0} bar can only be generated if '
                             'there is {0} data associated with '
                             'the atoms.'.format(label))

    return show, pos, data

def showAtomicMatrix(matrix, x_array=None, y_array=None, atoms=None, **kwargs):
    """Show a matrix using :meth:`~matplotlib.axes.Axes.imshow`. Curves on x- and y-axis can be added.
    The first return value is the :class:`~matplotlib.axes.Axes` object for the upper plot, and the second
    return value is equivalent object for the left plot. The third return value is 
    the :class:`~matplotlib.image.AxesImage` object for the matrix plot. The last return value is the 
    :class:`~matplotlib.axes.Axes` object for the color bar.

    :arg matrix: Matrix to be displayed.
    :type matrix: :class:`~numpy.ndarray`

    :arg x_array: Data to be plotted above the matrix.
    :type x_array: :class:`~numpy.ndarray`

    :arg y_array: Data to be plotted on the left side of the matrix.
    :type y_array: :class:`~numpy.ndarray`

    :arg percentile: A percentile threshold to remove outliers, i.e. only showing data within *p*-th 
                     to *100-p*-th percentile.
    :type percentile: float

    :arg atoms: a :class: `AtomGroup` instance for matching 
        residue numbers and chain identifiers. 
    :type atoms: :class: `AtomGroup`

    :arg chain_bar: display a bar at the bottom to show chain separations. 
                    If set to `None`, it will be decided depends on whether *atoms* 
                    is provided. 
                    Default is `None`.
    :type chain_bar: bool

    :arg domain_bar: the same with *chain_bar* but show domain separations instead. 
                    *atoms* needs to have *domain* data associated to it.
                    Default is `None`.
    :type domain_bar: bool

    :arg figure: if set to `None`, then a new figure will be created if *auto_show* 
                is `True`, otherwise it will be plotted on the current figure. If set 
                to a figure number or a :class:`~matplotlib.figure.Figure` instance, 
                no matter what 'auto_show' value is, plots will be drawn on the *figure*.
                Default is `None`.
    :type figure: :class:`~matplotlib.figure.Figure`, int, str
    """ 

    from prody.utilities import showMatrix
    from matplotlib.pyplot import figure, xlim, ylim, plot, text
    from matplotlib.figure import Figure
    from matplotlib import ticker

    chain_bar = kwargs.pop('chain_bar', None)
    domain_bar = kwargs.pop('domain_bar', None)
    chain_text_loc = kwargs.pop('chain_text_loc', 'above')
    domain_text_loc = kwargs.pop('domain_text_loc', 'below')
    show_text = kwargs.pop('show_text', True)
    show_domain_text = kwargs.pop('show_domain_text', show_text)
    show_chain_text = kwargs.pop('show_chain_text', show_text)
    fig = kwargs.pop('figure', None)

    if isinstance(fig, Figure):
        fig_num = fig.number
    elif fig is None or isinstance(fig, (int, str)):
        fig_num = fig
    else:
        raise TypeError('figure can be either an instance of matplotlib.figure.Figure '
                        'or a figure number.')
    if SETTINGS['auto_show']:
        figure(fig_num)
    elif fig_num is not None:
        figure(fig_num)

    n_row, n_col = matrix.shape
    ticklabels = None
    sides = []
    if atoms is not None:
        n_atoms = atoms.numAtoms()
        if n_atoms == n_row: sides.append('y') 
        if n_atoms == n_col: sides.append('x')
        if not sides:
            raise ValueError('The number of atoms ({0}) is inconsistent with the shape '
                             'of the matrix ({1}, {2}).'.format(n_atoms, n_row, n_col))
        hv = atoms.getHierView()
        if hv.numChains() == 0:
            raise ValueError('atoms should contain at least one chain.')
        elif hv.numChains() == 1:
            if chain_bar is None:
                chain_bar = False
            ticklabels = atoms.getResnums()
        else:
            chids = atoms.getChids()
            resnums = atoms.getResnums()
            ticklabels = ['%s:%d'%(c, n) for c, n in zip(chids, resnums)]

    im, lines, colorbar = showMatrix(matrix, x_array, y_array, ticklabels=ticklabels, **kwargs) 
    
    ## draw domain & chain bars
    show_chain, chain_pos, chids = _checkDomainBarParameter(chain_bar, 0., atoms, 'chain')

    bars = []
    texts = []
    if show_chain:
        b, t = showDomainBar(chids, loc=chain_pos, axis=sides[-1], 
                             text_loc=chain_text_loc, text_color='w', show_text=show_chain_text)
        bars.extend(b)
        texts.extend(t)

    # force turnning off domain_bar if chain_bar and only one side is 
    # available
    if len(sides) < 2:
        if show_chain:
            if domain_bar is not None:
                LOGGER.warn('There is only one side of the matrix matches with atoms so domain bar '
                            'will not be shown. Turn off chain_bar if you want to show the domain bar.')
            domain_bar = False
            
    show_domain, domain_pos, domains = _checkDomainBarParameter(domain_bar, 0., atoms, 'domain')

    if show_domain:
        b, t = showDomainBar(domains, loc=domain_pos, axis=sides[0], 
                             text_loc=domain_text_loc, text_color='w', show_text=show_domain_text)
        bars.extend(b)
        texts.extend(t)

    if SETTINGS['auto_show']:
        showFigure()

    return im, lines, colorbar, texts

def showAtomicLine(y, atoms=None, linespec='-', **kwargs):
    """
    Show a plot with the option to include chain color bars using provided atoms.
    
    :arg atoms: a :class: `AtomGroup` instance for matching 
        residue numbers and chain identifiers. 
    :type atoms: :class: `AtomGroup`

    :arg chain_bar: display a bar at the bottom to show chain separations. 
                    If set to `None`, it will be decided depends on whether *atoms* 
                    is provided. 
                    Default is `None`.
    :type chain_bar: bool

    :arg domain_bar: the same with *chain_bar* but show domain separations instead. 
                    *atoms* needs to have *domain* data associated to it.
                    Default is `None`.
    :type domain_bar: bool

    :arg figure: if set to `None`, then a new figure will be created if *auto_show* 
                is `True`, otherwise it will be plotted on the current figure. If set 
                to a figure number or a :class:`~matplotlib.figure.Figure` instance, 
                no matter what 'auto_show' value is, plots will be drawn on the *figure*.
                Default is `None`.
    :type figure: :class:`~matplotlib.figure.Figure`, int, str
    """
    
    chain_bar = kwargs.pop('chain_bar', None)
    domain_bar = kwargs.pop('domain_bar', None)
    chain_text_loc = kwargs.pop('chain_text_loc', 'above')
    domain_text_loc = kwargs.pop('domain_text_loc', 'below')
    zero_line = kwargs.pop('show_zero', False)
    show_text = kwargs.pop('show_text', True)
    show_domain_text = kwargs.pop('show_domain_text', show_text)
    show_chain_text = kwargs.pop('show_chain_text', show_text)

    from prody.utilities import showLine
    from matplotlib.pyplot import figure, xlim, ylim, plot, text
    from matplotlib.figure import Figure
    from matplotlib import ticker

    fig = kwargs.pop('figure', None)

    if isinstance(fig, Figure):
        fig_num = fig.number
    elif fig is None or isinstance(fig, (int, str)):
        fig_num = fig
    else:
        raise TypeError('figure can be either an instance of matplotlib.figure.Figure '
                        'or a figure number.')
    if SETTINGS['auto_show']:
        figure(fig_num)
    elif fig_num is not None:
        figure(fig_num)

    try:
        y = np.array(y)
    except:
        raise TypeError('y should be an array-like instance.')
    
    ticklabels = None
    if atoms is not None:
        hv = atoms.getHierView()
        if hv.numChains() == 0:
            raise ValueError('atoms should contain at least one chain.')
        elif hv.numChains() == 1:
            if chain_bar is None:
                chain_bar = False
            ticklabels = atoms.getResnums()
        else:
            chids = atoms.getChids()
            resnums = atoms.getResnums()
            ticklabels = ['%s:%d'%(c, n) for c, n in zip(chids, resnums)]

    lines, polys = showLine(y, linespec, ticklabels=ticklabels, **kwargs)
    if zero_line:
        l = xlim()
        plot(l, [0, 0], '--', color='gray')

    bars = []
    texts = []
    if chain_bar is None:
        chain_bar = atoms is not None

    show_chain, chain_pos, chids = _checkDomainBarParameter(chain_bar, 0., atoms, 'chain')
     
    if show_chain:
        b, t = showDomainBar(atoms.getChids(), loc=chain_pos, axis='x', 
                             text_loc=chain_text_loc, show_text=show_chain_text)
        bars.extend(b)
        texts.extend(t)

    show_domain, domain_pos, domains = _checkDomainBarParameter(domain_bar, 1., atoms, 'domain')
    if show_domain:
        b, t = showDomainBar(domains, loc=domain_pos, axis='x', 
                             text_loc=domain_text_loc,  show_text=show_domain_text)
        bars.extend(b)
        texts.extend(t)

    if SETTINGS['auto_show']:
        showFigure()
    return lines, polys, bars, texts

def showDomainBar(domains, loc=0., axis='x', **kwargs):
    """
    Plot a bar on top of the current axis which is colored based 
    on domain separations.
    
    :arg domains: a list of domain labels 
    :type domains: list, tuple, :class:~numpy.ndarray

    :arg loc: relative position of the domain bar. **0** means at 
              bottom/left and **1** means at top/right
    :type loc: float

    :arg axis: on which axis the bar will be plotted. It can be 
               either **x** or **y**
    :type axis: str

    :arg show_text: whether show the text or not. Default is ``True``
    :type show_text: bool

    :arg text_loc: location of text labels. It can be either 
                   **above** or **below**
    :type text_loc: str

    :arg text_color: color of the text labels
    :type text_color: str or tuple or list
    """

    from matplotlib.pyplot import plot, text, xlim, ylim

    show_text = kwargs.pop('show_text', True)
    text_color = kwargs.pop('text_color', 'k')

    text_loc = kwargs.pop('text_loc', 'above')
    if not isinstance(text_loc, str):
        raise TypeError('text_loc should be a str')
    
    text_loc = text_loc.lower().strip()
    if not text_loc in ['above', 'below']:
        raise ValueError('text_loc can only be either "above" or "below"')

    halign = 'left' if text_loc == 'below' else 'right'
    valign = 'top' if text_loc == 'below' else 'bottom'

    if len(domains) == 0:
        raise ValueError('domains should not be empty')
    if PY3K:
        domains = np.asarray(domains, dtype='U')
    EMPTY_CHAR = domains[0][:0]
    uni_domids = np.unique(domains)
    uni_domids = uni_domids[uni_domids!=EMPTY_CHAR]

    if axis == 'y':
        lim = xlim
    elif axis == 'x':
        lim = ylim
    else:
        raise ValueError('axis can be either "x" or "y"')

    L = lim()
    d_loc = L[0] + loc * (L[1] - L[0])
    D = []
    bars = []
    texts = []

    for domid in uni_domids:
        d = domains == domid
        D.append(d)
    if not D:
        return bars, texts
    D = np.vstack(D).T
    F = np.zeros(D.shape)
    F[~D] = np.nan
    F[D] = d_loc

    if show_text:
        for i, chid in enumerate(uni_domids):
            locs = np.where(D[:, i])[0]
            pos = np.median(locs)
            if axis == 'y':
                txt = text(d_loc, pos, chid, rotation='vertical', 
                                            color=text_color,
                                            horizontalalignment=halign, 
                                            verticalalignment='center')
            else:
                txt = text(pos, d_loc, chid, color=text_color,
                                            horizontalalignment='center', 
                                            verticalalignment=valign)
            texts.append(txt)
    if axis == 'y':
        _y = np.arange(len(domains))
        Y = np.tile(_y, (len(uni_domids), 1)).T
        bar = plot(F, Y, linewidth=5)
    else:
        bar = plot(F, linewidth=5)

    bars.extend(bar)
    lim(L, auto=True)
    return bars, texts

def showTree(tree, format='ascii', **kwargs):
    """ Given a tree, creates visualization in different formats. 
    arg tree: Tree needs to be unrooted and should be generated by tree 
    generator from Phylo in biopython. 
    type tree: Bio.Phylo.BaseTree.Tree
    arg format: Depending on the format, you will see different forms of trees. 
    Acceptable formats are `plt`, `ascii` and `networkx`.
    type format: str
    arg font_size: Font size for branch labels
    type: float
    arg line_width: The line width for each branch
    type: float
    """
    try: 
        from Bio import Phylo
    except ImportError:
        raise ImportError('Phylo module could not be imported. '
            'Reinstall ProDy or install Biopython '
            'to solve the problem.')
    font_size = float(kwargs.get('font_size', 8.0))
    line_width = float(kwargs.get('line_width', 1.5))

    if format == 'ascii':
        Phylo.draw_ascii(tree)
        return

    elif format == 'plt': 
        try:
            import pylab
        except:
            raise ImportError("Pylab or matplotlib is not installed.")
        pylab.rcParams["font.size"]=font_size
        pylab.rcParams["lines.linewidth"]=line_width
        Phylo.draw(tree, do_show=False, **kwargs)
        pylab.xlabel('distance')
        pylab.ylabel('proteins')
        return

    elif format == 'networkx':
        node_size = kwargs.pop('node_size', 20)
        node_color = kwargs.pop('node_color', 'red')
        node_shape = kwargs.pop('node_shape', 'o')
        withlabels = kwargs.pop('withlabels', True)
        scale = kwargs.pop('scale', 1.)
        iterations = kwargs.pop('iterations', 500)
        k = kwargs.pop('k', None)
        obj = showTree_networkx(tree, node_size=node_size, node_color=node_color, 
                                node_shape=node_shape, withlabels=withlabels, 
                                scale=scale, iterations=iterations, k=k, **kwargs)

        return obj
    
    else:
        raise ValueError('format should be ascii or plt or networkx.')

def showTree_networkx(tree, node_size=20, node_color='red', node_shape='o', withlabels=True, scale=1., iterations=500, k=None, **kwargs):
    from Bio import Phylo
    import matplotlib.pyplot as mpl

    try:
        import networkx
    except ImportError:
        raise ImportError('Please install networkx to use this function.')

    G = Phylo.to_networkx(tree)
    labels = {}
    colors = []
    sizes = []
    shape_types = 'so^>v<dph8'
    shape_groups = {}
    for s in shape_types:
        shape_groups[s] = []

    nodes = []
    for i, node in enumerate(G.nodes()):
        lbl = node.name
        if lbl is None:
            lbl = ''
            colors.append('black')
            sizes.append(0)
            shape_groups['o'].append(i)
        else:
            sizes.append(node_size)
            if isinstance(node_color, str):
                nc = node_color
            else:
                nc = node_color[lbl] if lbl in node_color else 'red'
            colors.append(nc)

            if isinstance(node_shape, str):
                ns = node_shape
            else:
                ns = node_shape[lbl] if lbl in node_shape else 'o'
            shape_groups[ns].append(i)
        labels[node] = lbl
        nodes.append(node)

    if SETTINGS['auto_show']:
        mpl.figure()

    layout = networkx.spring_layout(G, scale=scale, iterations=iterations, k=k)
    #networkx.draw(G, pos=layout, withlabels=False, node_size=sizes, node_color=colors)
    networkx.draw_networkx_edges(G, pos=layout)
    
    if np.isscalar(node_shape):
        networkx.draw_networkx_nodes(G, pos=layout, withlabels=False, node_size=sizes, 
                                        node_shape=node_shape, node_color=colors)
    else:
        for shape in shape_groups:
            nodelist = [nodes[i] for i in shape_groups[shape]]
            nodesizes = [sizes[i] for i in shape_groups[shape]]
            nodecolors = [colors[i] for i in shape_groups[shape]]
            if not nodelist: continue
            networkx.draw_networkx_nodes(G, pos=layout, withlabels=False, node_size=nodesizes, 
                                        node_shape=shape, node_color=nodecolors, 
                                        nodelist=nodelist)

    if withlabels:
        fontdict = kwargs.pop('fontdict', None)
        if fontdict is None:
            fontsize = kwargs.pop('font_size', 6)
            fontcolor = kwargs.pop('font_color', 'black')
            fontdict = {'size': fontsize, 'color': fontcolor}

        for node, pos in layout.iteritems():
            mpl.text(pos[0], pos[1], labels[node], fontdict=fontdict)

    if SETTINGS['auto_show']:
        showFigure()

    return mpl.gca()
