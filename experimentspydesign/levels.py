from numpy import array, max, min, log10
from numpy.random import uniform


class Level(object):
    def __init__(self, value):
        self._value = value
        self._paradigm = lambda l: l._value
        self._str_repr = self._get_str_repr(value)

    @property
    def name(self):
        return str(self)

    @property
    def value(self):
        return self._paradigm(self)

    @property
    def lower(self):
        return min(self._value)

    @property
    def upper(self):
        return max(self._value)

    @property
    def levels(self):
        if hasattr(self, '_levels'):
            return self._levels
        else:
            return [self]

    @staticmethod
    def _format_value(value, max_len=14):

        if type(value) is str:
            fmt = ('{:.' + str(min([len(value), max_len])) + '}').format(value)
        elif hasattr(value, '__iter__'):
            fmt = Level._get_str_repr(value)
        elif type(value) is int:
            fmt = str(value)
        elif value == 0.0:
            fmt = str(value)
        elif log10(abs(value)) > max_len - 1:
            print('getting to the right spot')
            fmt = '{:.2e}'.format(value)
        elif len(str(value)) > max_len:
            if int(value) == 0:
                int_len = 1
            else:
                int_len = int(log10(int(abs(value * 10))))
            decimal = min([len(str(value)) - 1 - int_len, max_len - 1 - int_len])
            fmt = ('{:' + str(int_len) + '.' + str(decimal) + 'f}').format(value)
        else:
            fmt = str(value)
        return fmt

    @staticmethod
    def _get_str_repr(value):
        if type(value) is not str and hasattr(value, '__iter__'):
            if len(value) == 2 and value[0] == value[1]:
                str_repr = Level._format_value(value[0])
            else:
                fmts = []
                for i in range(len(value)):
                    fmts.append(Level._format_value(value[i], 7))
                str_repr = '[' + ', '.join(fmts) + ']'
        else:
            str_repr = Level._format_value(value)

        return str_repr

    def _set_str_repr(self):
        if type(self._value) is not str and hasattr(self._value, '__iter__'):
            fmts = []
            for i in range(len(self._value)):
                fmts.append(self._format_value(self._value[i], 7))
            self._str_repr = '[' + ', '.join(fmts) + ']'
        else:
            self._str_repr = self._format_value(self._value)

    def __repr__(self):
        return self._str_repr

    def __lt__(self, other):
        if type(self) is not type(other):
            raise ValueError("An instance of class '{}' can only be compared to another instance "
                             "of the same class".format(type(self)))
        return self._value < other._value

    def __eq__(self, other):
        if all(array(self._value) == array(other._value)):
            if type(self) is type(other):
                return True
            else:
                # equal if continuous point and discrete point are equal
                return max(self._value) - min(other._value) == 0
        else:
            return False

    def __hash__(self):
        return hash(type(self).__name__ + str(self))


class LevelRange(Level):
    def __init__(self, bounds, paradigm='uniform'):
        super().__init__(bounds)
        self._dtype = float
        self._delta = self.upper - self.lower
        if self.lower == self.upper:
            self._paradigm = lambda l: l._value[0]
        elif paradigm == 'uniform':
            self._paradigm = lambda l: l.dtype(uniform() * l.delta + l.lower)
        else:
            self._paradigm = paradigm

    @property
    def delta(self):
        return self._delta

    @property
    def dtype(self):
        return self._dtype

    def __ge__(self, other):
        if self.lower == other.lower:
            return self.upper >= other.upper
        else:
            return self.lower >= other.lower

    def __le__(self, other):
        if self.lower == other.lower:
            return self.upper <= other.upper
        else:
            return self.lower <= other.lower

    def __gt__(self, other):
        return self.lower >= other.upper

    def __lt__(self, other):
        return self.upper <= other.lower


class LevelDatetime(LevelRange):
    def __init__(self, *args):
        # TODO everything
        pass


class LevelDiscrete(LevelRange):
    def __init__(self, *args):
        lower = self.dtype(min(args))
        upper = self.dtype(max(args))
        self._adjust_upper = lower != upper

        if lower == upper:
            super().__init__([lower, lower])
        else:
            super().__init__([lower, upper])
            # do not include upper bound since returning int types will only give integers from lower to upper - 1
            self._str_repr = self._get_str_repr([lower, upper - 1])

        self._delta = upper - lower

    @property
    def dtype(self):
        return int

    @property
    def upper(self):
        return super().upper - self._adjust_upper

    def __gt__(self, other):
        if other.dtype is int:
            return self.lower > other.upper
        else:
            return self.lower >= other.upper

    def __lt__(self, other):
        if other.dtype is int:
            return self.upper < other.lower
        else:
            return self.upper <= other.lower


class LevelCategory(Level):
    def __init__(self, label):
        super().__init__(label)
        if type(label) is not str:
            raise ValueError('class LevelCategory is only for str types')

    @property
    def dtype(self):
        return str


class LevelContinuous(LevelRange):
    def __init__(self, *args):
        if len(args) == 2:
            super().__init__([min(args), max(args)])
        elif 'int' in type(args[0]).__name__ or 'float' in type(args[0]).__name__:
            super().__init__([args[0], args[0]])
        elif hasattr(args[0], '__iter__') and len(args[0]) == 2:
            super().__init__([min(args[0]), max(args[0])])

        # def __gt__(self, other):
        #    if self._value[0] == other._value[0]:
        #        return self._value[1] > other._value[1]
        #    else:
        #        return self._value[0] > other._value[0]

        # def __lt__(self, other):
        #    if self._value[0] == other._value[0]:
        #        return self._value[1] < other._value[1]
        #    else:
        #        return self._value[0] < other._value[0]


class LevelCombo(Level):
    def __init__(self, *args):
        # TODO handle expansion of LevelCombo objects
        if len(args) == 1:
            args = args[0]
        levels = []
        values = []

        for i in range(len(args)):
            if isinstance(args[i], LevelCombo):
                levels += args[i].levels
                values += [l.value for l in args[i].levels]
            elif isinstance(args[i], Level):
                levels.append(args[i])
                values.append(args[i].value)
        # if len(levels) == 0:
        #    self = LevelCombo(*args[0])
        super().__init__(values)
        self._levels = levels

    @property
    def lower(self):
        return [l.lower for l in self._levels]

    @property
    def upper(self):
        return [l.upper for l in self._levels]

    @property
    def value(self):
        return [l.value for l in self._levels]

    @property
    def dtype(self):
        return LevelCombo

    def _consistent(self, other):
        if not self.name == other.name:
            raise TypeError("LevelCombo can only be compared to another "
                            "LevelCombo with the same factor ordering")

    def __eq__(self, other):
        if len(self.levels) != len(other.levels):
            return False
        return all([s_l == o_l for s_l, o_l
                    in zip(self.levels, other.levels)])

    def __lt__(self, other):
        self._consistent(other)

        depth = len(self._levels)
        i = 0
        while i < depth:
            if self.levels[i] == other.levels[i]:
                i += 1
            else:
                return self.levels[i] < other.levels[i]
        return False

    def __le__(self, other):
        depth = len(self.levels)
        i = 0
        while i < depth:
            if self.levels[i] == other.levels[i]:
                i += 1
            else:
                return self.levels[i] <= other.levels[i]
        return False

    def __gt__(self, other):
        depth = len(self.levels)
        i = 0
        while i < depth:
            if self.levels[i] == other.levels[i]:
                i += 1
            else:
                return self.levels[i] > other.levels[i]
        return False

    def __ge__(self, other):
        depth = len(self.levels)
        i = 0
        while i < depth:
            if self.levels[i] == other.levels[i]:
                i += 1
            else:
                return self.levels[i] >= other.levels[i]
        return False

    def __repr__(self):
        return str([l for l in self.levels])

    def __hash__(self):
        return hash(type(self).__name__ + str(self))
