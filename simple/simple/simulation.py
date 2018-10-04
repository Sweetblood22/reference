import datetime as dt


class Action(object):
    def __init__(self, date, process, inputs=(), owner=None, step=0):
        self._date = date
        self._process = process
        self._inputs = inputs
        self._owner = owner
        self._step = step

        MAIN_ACTIONS.append(self)

    @property
    def date(self):
        return self._date

    def __call__(self):
        return self._process(inputs=self._inputs, owner=self._owner, step=self._step)

    def __lt__(self, other):
        if type(other) is not Action:
            raise TypeError("'Action' type objects can not be compared to '{}' types".format(type(other).__name__))
        return self.date < other.date

    def __repr__(self):
        return '{} - {}'.format(self._process.name, self._date)


class SimulationClock(list):
    RES = {'d': 1,
           'y': 365.25,
           'w': 7,
           'h': 1 / 24,
           'm': 1 / 24 / 60,
           's': 1 / 24 / 3600}

    STAMP = {'d': 1 / 24 / 3600,
             'y': 1 / 24 / 3600 / 365.25,
             'w': 1 / 24 / 3600 / 7,
             'h': 1 / 3600,
             'm': 1 / 60,
             's': 1}

    def __init__(self, *args, **kwargs):
        step = kwargs.pop('step', 'd')
        super().__init__()
        try:
            initial = dt.datetime(*args, **kwargs)
        except TypeError:
            initial = dt.datetime.now()
        self._step = step
        self.append(initial)

    def to_timedelta(self, simstep):
        return dt.timedelta(simstep * self.RES[self._step])

    def to_datetime(self, simtime):
        return self[0] + self.to_timedelta(simtime)

    def to_simstep(self, timedelta):
        return timedelta.total_seconds() * self.STAMP[self._step]

    def to_simtime(self, datetime):
        return self.to_simstep(datetime - self[0])

    def to_steps(self):
        return [self.to_simtime(b) for b in self]

    def __call__(self):
        return self[-1]

    def __add__(self, delta):
        if type(delta) is dt.timedelta:
            return self[-1] + delta
        elif type(delta) is dt.datetime:
            return delta
        else:
            return self[-1] + self.to_timedelta(delta)


class SimulationQueue(list):
    """default behavior is to always have a reverse sorted list,
    this way the earliest item will be removed with the pop method
    """

    def __init__(self, *args, **kwargs):
        reverse = kwargs.pop('reverse', True)
        super().__init__(*args, **kwargs)
        self._reverse = reverse if type(reverse) is bool else False

    def sort(self, *args, key=None, reverse=True):
        if reverse is None:
            reverse = self._reverse
        else:
            reverse = reverse if type(reverse) is bool else False
        return super().sort(*args, key=key, reverse=reverse)

    def append(self, obj):
        super().append(obj)
        return super().sort(reverse=True)


CLOCK = SimulationClock()
MAIN_ACTIONS = SimulationQueue()
