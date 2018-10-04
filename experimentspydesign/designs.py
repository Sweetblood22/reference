from copy import copy
from numpy import argmax, sqrt, power, vstack, corrcoef, array, arange, mod, zeros, prod, eye, unique
from numpy.random import permutation
from experimentspydesign.tools import latin_hyper_index
from experimentspydesign.factors import FactorBase, FactorDiscrete, FactorCombo
from experimentspydesign.services import FormattedDict


class Design(FormattedDict):
    """Helper dictionary that passes key names to FactorBase instances

    >>> d0 = dict(hardness=FactorDiscrete(3, 7))
    >>> d0['weight'] = FactorDiscrete(200, 500)
    >>> print([v.name for v in d0.values()])
    ['factor_01', 'factor_02']

    >>> d1 = Design(hardness=FactorDiscrete(3, 7))
    >>> d1['weight'] = FactorDiscrete(200, 500)
    >>> print([v.name for v in d1.values()])
    ['hardness', 'weight']
    """
    def __init__(self, *args, **kwargs):
        if len(args) > 0:
            kwargs.update(dict(args[0]))

        super().__init__({})
        for name in list(kwargs.keys()):
            self[name] = kwargs[name]

    def __setitem__(self, name, factor):
        super().__setitem__(name, factor)
        if isinstance(factor, FactorBase) and 'factor_' in factor.name:
            self[name].name = name


def ls(*design, by=None, def_scale='traditional'):
    """Create a Latin Square or Rectangle from factor definitions, sparse quick design for a large number of factors

    :param design: definitions of factors' levels in design, factors defined with an int will be
        scaled per the method selected with the def_scale argument
    :param by: str, name of factor to block experiment
    :param def_scale: str, paradigm for scaling factors that don't have a high and low defined
            'traditional' : scale output to [-1, 1]
            'standard' : scale output to [0, 1]
            'level_n' : scale output to [1, n]
    :return: numpy.ndarray, a table with experiment values for each factor
    """
    if isinstance(design[0], dict):
        design = design[0]
    else:
        design, n_factors, rescale = _parse_design(*design)
        design = dict([(i, factor) for i, factor in enumerate(design)])

    if by is not None:
        tables = []
        blocks = design[by].values
        des = copy(design)
        des.pop(by)
        for b in blocks:
            tables.append(ls(des))
            tables[-1][by] = b
        return tables  # concat(tables)

    sizes = []
    factors = []
    for factor in design.keys():
        if type(design[factor]) is int:
            sizes.append(design[factor])
        else:
            sizes.append(len(design[factor]))
        factors.append(factor)
    i_max = argmax(sizes)
    f_max = factors[i_max]

    factors.remove(f_max)
    table = []
    # switch to accommodate different factor definitions and ensure each type properly initializes the output table
    if type(design[f_max]) is int:
        # if just an integer for the number of levels is passed then create n levels from -1 to 1
        table.append(arange(design[f_max]))
    elif isinstance(design[f_max], FactorBase):
        table.append(array(design[f_max].levels.values()))
    elif isinstance(design[f_max], dict):
        table.append(array(design[f_max].values()))
    else:
        table.append(array(design[f_max]))

    for f_name in factors:
        hyper_ix = latin_hyper_index(design[f_max], design[f_name])
        # switch to accommodate different factor definitions
        if type(design[f_name]) is int:
            table.append(hyper_ix / hyper_ix.max() * 2 - 1)
        elif isinstance(design[f_name], FactorBase):
            latin = [design[f_name][hi].value for hi in hyper_ix]
        else:
            latin = [design[f_name][hi] for hi in hyper_ix]
        table.append(array(latin))
    # TODO include a way to re-sample the factors in the design
    # size = sizes[i_max] if size < sizes[i_max] else size
    return table  # vstack(table).T


def _parse_design(*design):
    if len(design) == 1:
        rescale = False
        if type(design[0]) is int:
            n_factors = design[0]
            design = []
        elif isinstance(design[0], dict):
            return _parse_design(*design[0].values())
        elif hasattr(design[0], '__iter__'):
            return _parse_design(*design[0])
    else:
        rescale = True
        n_factors = len(design)

    return design, n_factors, rescale


def lhs(*design, n_samples=None, def_scale='traditional'):
    """Randomly combine 'n_samples' evenly spaced values for each factor with
    other factor values to create a space filling design

    :param design: definitions of factors' levels in design, factors defined with an int will be
        scaled per the method selected with the def_scale argument
    :param n_samples: int, number of sample values to create
    :param def_scale: str, paradigm for scaling factors that don't have values defined
            'traditional' : scale output to [-1, 1]
            'standard' : scale output to [0, 1]
            'level_n' : scale output to [1, n]
    :return: numpy.ndarray, a table with experiment values for each factor
    """
    design, n_factors, rescale = _parse_design(*design)

    if n_samples is None:
        n_samples = n_factors * 2 + 1

    basis = arange(0, n_samples)
    hyper = vstack([permutation(basis) for _ in range(n_factors)]).T

    hyper = measure_scale(*design, raw_design=hyper / hyper.max(axis=0, keepdims=True) * 2 - 1, def_scale=def_scale)
    return hyper


def ccdesign(*design, face='ccc', alpha='rotatable', n_centers=None, def_scale='traditional'):
    """Central Composite a rotatable design useful for quadratic models with a small number of factors
    NOTE when including DiscreteFactors the design will not be rotatable

    :param design: definitions of factors' levels in design, factors defined with an int will be
        scaled per the method selected with the def_scale argument
    :param face: str, select paradigm for scaling star points
            'ccc' : default, circumscribe places star points outside of factor ranges
            'cci' : inscribed, star points will be at factors' max and min while the corners
                    are scaled down inside the factor's range
            'ccf' : face, place star point at factors' max and min, creating a cube rather than a ball
    :param alpha: str, default 'rotatable'
    :param n_centers: int, number of center points for design,
            default None calculates n_centers from number of other experiments in design
    :param def_scale: str, paradigm for scaling factors that don't have values defined
            'traditional' : scale output to [-1, 1]
            'standard' : scale output to [0, 1]
            'level_n' : scale output to [1, n]
    :return: numpy.ndarray, a table with experiment values for each factor
    """

    if len(design) == 1:
        if 'int' in type(design[0]).__name__:
            n_factors = design[0]
            design = [5] * n_factors
        elif isinstance(design[0], dict):
            return ccdesign(*list(design[0].values()), face=face, alpha=alpha, n_centers=n_centers)
        elif hasattr(design[0], '__iter__'):
            return ccdesign(*design[0], face=face, alpha=alpha, n_centers=n_centers)
        else:
            raise TypeError('Factor definition must be an iterable of Factor instances or an integer ')
    else:
        n_factors = len(design)

    if n_centers is None:
        n_centers = power(2 ** (n_factors - 1) + 2 * (n_factors - 1), 0.27).astype(int) + 4

    C = zeros((n_centers, n_factors))

    F = ff2n(n_factors)

    if face == 'ccf':
        # if Face-Centered then star points are on faces and nothing is scaled
        alpha = 1
    elif alpha == 'rotatable':
        alpha = power(len(F), 0.25)
    else:
        n = len(F)
        alpha = power((sqrt(2 * n_factors + n_centers) + n) - sqrt(n), 0.25)

    E = vstack([eye(n_factors), -eye(n_factors)]) * alpha

    d = vstack([F, E, C])

    if face == 'cci':
        d /= alpha

    d = measure_scale(*design, raw_design=d, def_scale=def_scale)

    return d


def measure_scale(*design, raw_design=None, def_scale='traditional'):
    """Scale a design to defined factor levels, factors which only have an int for number of levels
    will be scaled by the method selected with the def_scale argument

    :param design: definitions of factors' levels in design, factors defined with an int will be
        scaled per the method selected with the def_scale argument
    :param raw_design: numpy.ndarray with each column scaled to factor values of low=-1 and high=1
    :param def_scale: str, paradigm for scaling factors that don't have a high and low defined
            'traditional' : scale output to [-1, 1]
            'standard' : scale output to [0, 1]
            'level_n' : scale output to [1, n]
    :return: numpy.ndarray design with values scaled to factor ranges
    """
    # make a copy of the design and scale from [-1, 1] to [0, 1]
    d = raw_design / 2 + 0.5

    if raw_design is None:
        return [[]]
    elif len(design) == 1:
        return measure_scale(*design[0], raw_design=raw_design)
    elif len(design) == 0:
        if def_scale == 'traditional':
            return d * 2 - 1
        elif def_scale == 'level_n':
            m, n = d.shape
            ns = zeros((1, n), dtype=int)
            for i in range(n):
                ns[0, i] = len(unique(d[:, i]))
            return (d * ns).astype(int)
        else:
            return d

    all_ints = True
    for i in range(len(design)):
        to_int = False

        values = unique(d[:, i])
        if isinstance(design[i], int):
            # if argument for a factor is only an integer assume continuous and linear mapping then scale directly
            if def_scale == 'level_n':
                to_int = True
                low = 1
                high = len(unique(d[:, i]))
            elif def_scale == 'traditional':
                low = -1
                high = 1
            else:
                low = 0
                high = 1
            d[:, i] = _scale(d[:, i], high - low, low, to_int=to_int)
        elif len(design[i]) == len(values):
            d_i = d[:, i] + 0
            # if the number of defined levels in the argument matches the number in the design then directly
            # use the level values from argument in the design
            if isinstance(design[i], FactorBase):
                for v, level in zip(values, design[i].values()):
                    ix = d_i == v
                    d[ix, i] = array([level.value for _ in range(ix.sum())])
            elif isinstance(design[i], dict):
                for v, level in zip(values, design[i].values()):
                    ix = d_i == v
                    d[ix, i] = level
            elif hasattr(design[i], '__iter__'):
                for j, v in enumerate(values):
                    ix = d_i == v
                    d[ix, i] = design[i][j]
        else:
            # if number of defined level values in argument do not match number of values in design
            # assume a continuous and linear mapping and scale using the high and low values from argument
            if isinstance(design[i], FactorBase):
                low = min(design[i].values()).lower
                high = max(design[i].values()).upper
                to_int = isinstance(design[i], FactorDiscrete)
            elif isinstance(design[i], dict):
                low = min(design[i].values())
                high = max(design[i].values())
            elif hasattr(design[i], '__iter__'):
                low = min(design[i])
                high = max(design[i])
            d[:, i] = _scale(d[:, i], high - low, low, to_int=to_int)
        all_ints = all_ints and abs(d[:, i] - d[:, i].round()).sum() == 0

    return d.astype(int) if all_ints else d


def _scale(f, spread, low, to_int=False):
    x = f * spread + low
    if to_int:
        # if some integers end up halfway between two valid values then alternate between the values
        alt_ix = (x - x.round()) == 0.5
        x[alt_ix] = x[alt_ix] + mod(arange(alt_ix.sum()), 2) - 1 / 2
        x = x.round()
    return x


def bbdesign(*design, n_centers=None, def_scale='traditional'):
    """Box-Behnken an efficient rotatable design useful for quadratic models with a small to moderate number of factors
    NOTE when DiscreteFactors are included the design will not be rotatable

    :param design: definitions of factors' levels in design, factors defined with an int will be
        scaled per the method selected with the def_scale argument
    :param n_centers: int, number of center points for design,
            default None calculates n_centers from number of other experiments in design
    :param def_scale: str, paradigm for scaling factors that don't have a high and low defined
            'traditional' : scale output to [-1, 1]
            'standard' : scale output to [0, 1]
            'level_n' : scale output to [1, n]
    :return: numpy.ndarray design with values scaled to factor ranges
    """

    if len(design) == 1:
        if 'int' in type(design[0]).__name__:
            n_factors = design[0]
            design = [3] * n_factors
        elif isinstance(design[0], dict):
            return bbdesign(*list(design[0].values()), n_centers=n_centers)
        elif hasattr(design[0], '__iter__'):
            return bbdesign(*design[0], n_centers=n_centers)
    else:
        n_factors = len(design)

    if n_centers is None:
        n_centers = power(2 ** (n_factors - 3) + 2 * (n_factors - 3), 0.27).astype(int) + 4

    f_ = ff2n(2, def_scale='traditional')
    m, n = f_.shape
    v = n_factors * (n_factors - 1) // 2

    F = zeros((v * m, n_factors))

    for o, (i, j) in enumerate([(i, j) for i in range(n_factors) for j in range(n_factors) if j > i]):
        F[o * m:(o + 1) * m, i] = f_[:, 0]
        F[o * m:(o + 1) * m, j] = f_[:, 1]

    C = zeros((n_centers, n_factors))

    d = vstack([F, C])

    d = measure_scale(*design, raw_design=d, def_scale=def_scale)

    return d


def fullfact(*design, def_scale='traditional'):
    """Full Factorial design: all combinations of all factors' level values

    :param design: definitions of factors' levels in design, factors defined with an int will be
        scaled per the method selected with the def_scale argument
    :param def_scale: str, paradigm for scaling factors that don't have values defined
            'traditional' : scale output to [-1, 1]
            'standard' : scale output to [0, 1]
            'level_n' : scale output to [1, n]
    :return:
    """
    design, n_factors, rescale = _parse_design(*design)

    d = _full_fact(*design)
    # raw_designs have to be scaled [-1, 1] for the low, high values of the factor
    d = d / d.max(axis=0, keepdims=True) * 2 - 1
    d = measure_scale(*design, raw_design=d, def_scale=def_scale)

    return d


def _full_fact(*design):
    design, n_factors, rescale = _parse_design(*design)
    factors_n_levels = []
    for arg in design:
        if hasattr(arg, '__iter__'):
            factors_n_levels.append(len(arg))
        elif type(arg) is int:
            factors_n_levels.append(arg)

    basis = arange(prod(factors_n_levels))
    f = []
    for n in factors_n_levels:
        f.append(mod(basis, n))
        basis = basis // n

    return array(f).T


def ff2n(*design, def_scale='traditional'):
    """2k Factorial design: all combinations of all factors' high and low values

    :param design: definitions of factors' levels in design, factors defined with an int will be
        scaled per the method selected with the def_scale argument
    :param def_scale: str, paradigm for scaling factors that don't have values defined
            'traditional' : scale output to [-1, 1]
            'standard' : scale output to [0, 1]
            'level_n' : scale output to [1, n]
    :return:
    """
    design, n_factors, rescale = _parse_design(*design)
    d = _full_fact([2] * n_factors)
    # raw_designs have to be scaled [-1, 1] for the low, high values of the factor
    d = d / d.max(axis=0, keepdims=True) * 2 - 1

    if len(design) == 0:
        d = measure_scale(*[2] * n_factors, raw_design=d, def_scale=def_scale)
    else:
        d = measure_scale(*design, raw_design=d, def_scale=def_scale)

    return d


def orthogonal_maximin_lhs(*design, n_samples=None, omega=0.5, temperature=1, def_scale='traditional'):
    """Search the space of latin_hyper designs for a design that is better than the initial randomly selected design

    :param design: definitions of factors' levels in design, factors defined with an int will be
        scaled per the method selected with the def_scale argument
    :param n_samples:
    :param omega:
    :param temperature:
    :param def_scale: str, paradigm for scaling factors that don't have values defined
            'traditional' : scale output to [-1, 1]
            'standard' : scale output to [0, 1]
            'level_n' : scale output to [1, n]
    :return: numpy.ndarray, a table with experiment values for each factor
    """
    design, n_factors, rescale = _parse_design(*design)
    if n_samples is None:
        n_samples = n_factors * 2 + 1
    # TODO omega does not behave consistently as n_samples increases due to expected scale of rho and phi
    hyper = lhs(n_factors, n_samples=n_samples)

    rhos = get_rhos(hyper)
    phis = get_phis(hyper)

    phi_upper = phi_upper_bound(n_samples, n_factors)
    phi_lower = phi_lower_bound(n_samples, n_factors)
    phi_spread = phi_upper - phi_lower

    i_star = argmax(phis)
    j_star = argmax(rhos)

    return hyper


def _column_avg_rho(design, j):
    m, k = design.shape
    rho = 0
    for i in range(k):
        if i == j:
            continue
        rho += corrcoef(design[:, i], design[:, j]) ** 2

    return rho / (k - 1)


def _row_avg_distance(design, i):
    m, k = design.shape
    distance = 0.0
    for j in range(m):
        if i == j:
            continue
        distance += ((design[i, :] - design[j, :])[0, 1] ** 2).sum()
    return sqrt(distance)


def _inspect_rhos(design):
    m, k = design.shape

    rhos = []
    indices = []

    for i in range(k - 1):
        for j in range(i, k):
            indices.append((i, j))
            rhos.append(corrcoef(design[:, i], design[:, j])[0, 1] ** 2)
    return rhos, indices


def get_rhos(design):
    m, k = design.shape

    rhos = rho_matrix(design)
    return rhos.sum(axis=0) / (k - 1)


def get_phis(design):
    m, k = design.shape

    ds = distance_squared_matrix(design)

    phis = 1 / ds.ravel()[eye(m).ravel() == 0].reshape(m, m - 1)
    return sqrt(phis.sum(axis=0))


def design_correlation(design):
    m, k = design.shape

    rhos, _ = _inspect_rhos(design)

    return array(rhos).sum() / k / (k-1) * 2


def distance_matrix(points):
    return sqrt(distance_squared_matrix(points))


def distance_squared_matrix(points):
    m, k = points.shape
    dif = (points.reshape(1, m, k) - points.reshape(m, 1, k)) ** 2
    return dif.sum(axis=-1)


def phi_matrix(points):
    m, k = points.shape

    ds = distance_squared_matrix(points)

    return 1 / ds.ravel()[eye(m).ravel() == 0].reshape(m, m - 1)


def rho_matrix(design):
    m, k = design.shape
    rhos = zeros((k, k))
    for i in range(k):
        for j in range(k):
            rhos[i, j] = corrcoef(design[:, i], design[:, j])[0, 1] ** 2
    return rhos - eye(k)


def phi_lower_bound(m, k):
    d = (m + 1) * k / 3
    d_l = int(d)
    d_h = d_l + 1
    return sqrt(m * (m - 1) / 2 * ((d_h - d) / d_l ** 2 + (d - d_l) / d_h ** 2))


def phi_upper_bound(m, k):
    base = arange(1, m - 1)
    return sqrt(((m - base) / (base * k) ** 2).sum())
