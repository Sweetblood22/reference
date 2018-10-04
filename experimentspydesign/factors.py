from numpy import (array, linspace, min, max)
from experimentspydesign.levels import (LevelDiscrete, LevelContinuous,
                                        LevelCategory, LevelCombo)
from experimentspydesign.tools import factorial_indices as _factorial_indices
from experimentspydesign.services import FormattedDict
# from experimentspydesign.services import IterMapFunc


class FactorBase(FormattedDict):
    """FactorBase provides a basic interface for factors of different types
    it is not intended to instanced on its own.

    """

    COUNTER = 0

    def __init__(self, levels, name=None, **kwargs):
        """

        :param levels: list-like, of Level objects
        :param name: str, name to identify factor in a design
        :param kwargs:
        """
        if name is None:
            FactorBase.COUNTER += 1
        name = name if name is not None else 'factor_{:02d}'.format(FactorBase.COUNTER)

        super().__init__([(i, l) for i, l in enumerate(levels)])
        self._name = name
        self._n_levels = len(self)

    def _apply(self, f):
        return FormattedDict([(k, f(v)) for k, v in self.items()], name=self.name)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def levels(self):
        return self._apply(lambda l: l.value)

    @property
    def lowers(self):
        return self._apply(lambda l: l.lower)

    @property
    def uppers(self):
        return self._apply(lambda l: l.upper)

    @property
    def names(self):
        if hasattr(self, '_names'):
            return self._names
        else:
            return [self.name]

    @staticmethod
    def _parse_positional_args(args):
        """A single string will be assumed to be levels that are defined by each character

        :param args:
        :return:
        """
        # parse positional args
        if len(args) == 1:
            args = args[0]

        if not hasattr(args, '__iter__'):
            # this will happen if only one value for a level is passed
            args = [args]
        return args

    def __mul__(self, other):
        s_ix, o_ix = _factorial_indices(self, other)
        combos = [LevelCombo(self[s], other[o]) for s, o in zip(s_ix, o_ix)]
        return FactorCombo(combos, names=[self.name, other.name])

    def __ge__(self, other):
        s_ix, o_ix = _factorial_indices(self, other)
        keep = array([self[s] >= other[o] for s, o in zip(s_ix, o_ix)])
        combos = [LevelCombo(self[s], other[o]) for s, o in zip(s_ix[keep], o_ix[keep])]
        return FactorCombo(combos, names=[self.name, other.name])

    def __gt__(self, other):
        s_ix, o_ix = _factorial_indices(self, other)
        keep = array([self[s] > other[o] for s, o in zip(s_ix, o_ix)])
        combos = [LevelCombo(self[s], other[o]) for s, o in zip(s_ix[keep], o_ix[keep])]
        return FactorCombo(combos, names=[self.name, other.name])

    def __lt__(self, other):
        s_ix, o_ix = _factorial_indices(self, other)
        keep = array([self[s] < other[o] for s, o in zip(s_ix, o_ix)])
        combos = [LevelCombo(self[s], other[o]) for s, o in zip(s_ix[keep], o_ix[keep])]
        return FactorCombo(combos, names=[self.name, other.name])

    def __le__(self, other):
        s_ix, o_ix = _factorial_indices(self, other)
        keep = array([self[s] <= other[o] for s, o in zip(s_ix, o_ix)])
        combos = [LevelCombo(self[s], other[o]) for s, o in zip(s_ix[keep], o_ix[keep])]
        return FactorCombo(combos, names=[self.name, other.name])

    def get(self, item, default=None):
        if item in self.keys():
            return super().get(item, default=default)
        elif hasattr(item, '__iter__') and type(item) is not str:
            return dict([(k, self.get(k, default=default)) for k in item])

    def __getitem__(self, item):
        if item in self.keys():
            return super().__getitem__(item)
        elif hasattr(item, '__iter__') and type(item) is not str:
            return dict([(k, self[k]) for k in item])

    def _get_header(self):
        return (' ' * self._index_width + '  {:^' + str(self._column_width) + 's}').format(self.name)

    # def to_series(self):
    #     return Series(self.levels, name=self.name)

    # def to_frame(self):
    #     return DataFrame(self.levels, index=[self.name]).T


class FactorContinuous(FactorBase):
    """Class used for Factors with continuous levels, either float point values or ranges of float values

    EXAMPLES:

        >>> FactorContinuous([i/2 for i in range(5)])
           factor_01
        0  0.0
        1  0.5
        2  1.0
        3  1.5
        4  2.0

        >>> FactorContinuous(27, 81, n_levels=3)
            factor_02
        0  [27.0, 45.0]
        1  [45.0, 63.0]
        2  [63.0, 81.0]

        >>> FactorContinuous(2, 4, 25, name='hardness')
           hardness
        0  2
        1  4
        2  25
    """
    def __init__(self, *args, n_levels=None, name=None, **kwargs):
        args = self._parse_positional_args(args)
        if not all([type(a) in [float, int] for a in args]):
            raise TypeError('class {} only accepts float and int types for defining the '
                            'instances levels'.format(type(self).__name__))

        lower = min(args)
        upper = max(args)

        if n_levels is None:
            levels = [LevelContinuous(a) for a in args]

        elif n_levels == 1 and lower == upper:
            levels = [LevelContinuous(lower)]
        elif n_levels == 1 and upper > lower:
            levels = [LevelContinuous(lower, upper)]

        else:  # if len(args) > 0: #  and n_levels >= 1:
            knots = linspace(lower, upper, n_levels + 1)
            levels = [LevelContinuous(l, u) for l, u in zip(knots[:-1], knots[1:])]

        super().__init__(levels, name=name, **kwargs)


class FactorDiscrete(FactorBase):
    """Class used for Factors with integer levels, either int point values or ranges of int values

    EXAMPLES:

        >>> FactorDiscrete(80, 3452, name='parsecs')
           parsecs
        0   80
        1  3462
        >>> days = FactorDiscrete([4, 8], n_levels=2, name='days')
        >>> days
            days
        0  [4, 5]
        1  [6, 8]
        >>> days.levels
           days
        0  5
        1  6
        >>> days.levels
           days
        0  4
        1  7
        >>> FactorDiscrete([7, 11, 13])
           factor_07
        0  7
        1  11
        2  13
    """
    def __init__(self, *args, n_levels=None, name=None, **kwargs):
        args = self._parse_positional_args(args)
        if not all([type(a) is int for a in args]):
            raise TypeError('class FactorDiscreteBase only accepts int types for defining the instances levels')

        lower = min(args)
        upper = max(args)

        if n_levels is None:
            levels = [LevelDiscrete(a) for a in args]

        elif n_levels == 1 and lower == upper:
            levels = [LevelDiscrete(lower)]
        elif n_levels == 1 and upper > lower:
            upper += 1
            levels = [LevelDiscrete(lower, upper)]

        else:  # if len(args) > 0: #  and n_levels >= 1:
            knots = linspace(lower, upper + 1, n_levels + 1).astype(int)
            levels = [LevelDiscrete(l, u) for l, u in zip(knots[:-1], knots[1:])]

        super().__init__(levels, name=name, **kwargs)


class FactorCategorical(FactorBase):
    """Can affect the weighting of a level by passing it multiple times, only effective when creating a design with
    other levels which are ranges

    FactorCategoricalBase('abcaba') """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FactorDatetime(FactorBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FactorCombo(FactorBase):
    """Class to group Factors together

    """
    def __init__(self, *args, **kwargs):
        names = kwargs.pop('names', [])

        if len(names) > 0:
            self._name = '__'.join(names)

        super().__init__(*args, name='__'.join(names), **kwargs)
        self._names = names

    # def to_series(self, transpose=False):
    #     df = self._as_frame().T if transpose else self._as_frame()
    #     return [df[col] for col in df.columns]

    # def _as_frame(self):
    #     return DataFrame(self.levels, index=self.names).T

    # def to_frame(self, transpose=False):
    #     return self._as_frame().T if transpose else self._as_frame()
