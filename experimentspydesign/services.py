from numpy import ndarray, array, max, str_
from re import search


class FormattedDict(dict):
    def __init__(self, *args, **kwargs):
        name = kwargs.pop('name', None)
        super().__init__(*args, **kwargs)
        if name is not None:
            self.name = name
        if len(self) is not 0:
            self._index_width = max([len(str(k)) for k in super().keys()])
            self._column_width = max([len(str(v)) for v in super().values()])
        else:
            self._index_width = 1
            self._column_width = 1
        self._index_fmt = ['{:>', 's}']
        self._column_fmt = ['{:^', 's}']

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._index_width = len(str(key))
        if isinstance(type(value), FormattedDict):
            self._column_width = value._column_width + value._index_width
        else:
            self._column_width = max([self._index_width, len(str(value))])

    @property
    def index_fmt(self):
        return self._index_fmt[0] + str(self._index_width) + self._index_fmt[1]

    @index_fmt.setter
    def index_fmt(self, fmt):
        s = search('({:0{0, 1})(\d+)(\w{0, 1}})', fmt)
        if s is None:
            raise ValueError('invalid str.format')
        else:
            self._index_width = int(s.group(2))
            self._index_fmt = [s.group(1), s.group(3)]

    @property
    def column_fmt(self):
        return self._column_fmt[0] + str(self._column_width) + self._column_fmt[1]

    @column_fmt.setter
    def column_fmt(self, fmt):
        s = search('({:\^{0, 1}0{0, 1})(\d+)(\w{0, 1}})', fmt)
        if s is None:
            raise ValueError('invalid str.format')
        else:
            self._column_width = int(s.group(2))
            self._column_fmt = [s.group(1), s.group(3)]

    @property
    def index_width(self):
        return self._index_width

    @index_width.setter
    def index_width(self, width):
        if type(width) is int:
            self._index_width = max([self._index_width, width])
        else:
            raise ValueError('index_width property must be of type int')

    @property
    def column_width(self):
        return self._column_width

    @column_width.setter
    def column_width(self, width):
        if type(width) is int:
            self._column_width = max([self._column_width, width])
        else:
            raise ValueError('column_width property must be of type int')

    def _string_rows(self, keys):
        row_ = self.index_fmt + '  ' + self.column_fmt

        return [row_.format(str(k), str(self[k])) for k in keys]

    def _get_header(self):
        if hasattr(self, 'name'):
            column_fmt = '{:^' + str(self._column_width) + 's}'
            return ' ' * self._index_width + '  ' + column_fmt.format(self.name)
        else:
            return ''

    def display(self, n_rows=50, header=True):
        keys = list(self.keys())
        n = len(self)
        rows = [self._get_header()] if header else []

        if n > n_rows + 1:
            rows += self._string_rows(keys[:n_rows // 2]) + ['...'] + self._string_rows(keys[-n_rows // 2:])
        else:
            rows += self._string_rows(keys)
        return '\n'.join(rows)

    def __repr__(self):
        return self.display(n_rows=20, header=True)


class IterMapFunc(object):
    """Create a mapping function that will cascade mappings down nested
    iterable arguments, returning the same type(s) and structure of the
    input argument

    EXAMPLE:
    >> data = [2, 5, 3, {'one': 6, 'two': 5, 'numbers': np.array([5, 3])}]
    >> mapper = IterMapFunc({5: 0, 3: 5}) # DEFAULT identity=True
    >> mapper(data)
    [Out] [2, 0, 5, {'one': 6, 'two': 0, 'numbers': array([0, 5])}]
    >> mapper = IterMapFunc({5: 0, 3: 5}, identity=False)
    >> mapper(data) # Raises KeyError because elements in the list weren't defined in domain of the mapping
    [Out] KeyError: 2

    """
    def __init__(self, re_map, reverse=False, identity=True):
        """Create a method that will iterate down an input data structure
        and map elements as defined by argument re_map

        :param re_map: dict; definition of map, keys are domain inputs and
            values are range outputs
        :param reverse: bool; reverse the mapping if True, default=False
        :param identity: bool; default True, any element not in domain of map
            will be mapped to itself, when False a KeyError will be raised
        :return callable object: callable which will convert elements in input
            as defined by instance's map while preserving container structure
        """
        self.re_map = re_map
        self.identity = identity
        if reverse:
            self.reverse()

    def __call__(self, k):
        """Convert domain elements in input as defined by instance's map
        and return same structure with mapped range elements

        :param k, just about anything?"""
        if type(k) is dict:
            keys = list(k.keys())
            values = list(k.values())
            values = self(values)
            return dict(zip(keys, values))
        elif type(k) is ndarray:
            return array([self(k_i) for k_i in k])
        elif hasattr(k, '__iter__') and type(k) not in [str, type, str_]:
            return type(k)([self(k_i) for k_i in k])
        else:
            try:
                return self.re_map[k]
            except KeyError as error:
                if self.identity:
                    return k
                else:
                    raise error

    def reverse(self):
        """Reverse the map of the instance; makes an inverse map/function"""
        self.re_map = {v: k for k, v in self.re_map.items()}