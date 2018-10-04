from copy import copy
from simple.trees import AbstractTreeStrict
from simple.simulation import CLOCK
from numpy import argmax, argmin


class Component(AbstractTreeStrict):
    ID = 0
    ABBREVIATION = 'CP'

    def __init__(self,
                 model=None,
                 name=None,
                 date_ordered=None,
                 date_created=None,
                 components=(),
                 process=()):
        super().__init__()
        self._model = model
        if name is not None:
            self._name = name
        if date_created is not None:
            self._date_created = date_created
        else:
            self._date_created = CLOCK()
        self._date_ordered = date_ordered

        self._date_expired = self.date_created + CLOCK.to_timedelta(model.life_time_steps)
        self._components = None
        self.install_components(components)
        self._process = process
        # self._date_next_maintenance = self.date_created + self.get_maintenance_period()
        self._owner = None
        self._test = 1

    @property
    def model(self):
        return self._model

    @property
    def date_ordered(self):
        return self._date_ordered

    @property
    def date_created(self):
        return self._date_created

    @property
    def date_expired(self):
        return self._date_expired

    @property
    def id(self):
        return self._id

    @property
    def owner(self):
        return self._owner

    # @property
    # def date_next_maintenance(self):
    #     return self._date_next_maintenance

    # def get_maintenance_period(self):
    #     return min(self._maintenance)

    def assign_owner(self, owner):
        self._owner = owner

    def install_components(self, *components):
        if len(components) == 1 and hasattr(components[0], '__iter__'):
            return self.install_components(*components[0])
        for c in components:
            self.add_child(c)
        return None


class MaintenanceSchedule(object):
    def __init__(self,
                 min_time=None,
                 max_time=None,
                 facility=None,
                 process=()):
        self._min_time = min_time
        self._max_time = max_time
        self._facility = facility
        self._process = process


class StorageComponent(object):
    ID = 0
    ABBREVIATION = 'SC'

    def __init__(self, model_type, capacity, paradigm=None, name=None):

        self._id = StorageComponent.ID + 0
        StorageComponent.ID += 1
        self._name = name if name is not None else '{}-{:05d}'.format(self.ABBREVIATION, self._id)
        self._owner = None
        self._inputs = []
        self._outputs = []
        self._storage = []
        self._model_type = model_type
        self._capacity = capacity
        if paradigm is None:
            self._selection_paradigm = lambda queue: 0 if len(queue) > 0 else None  # FIFO
        else:
            self._test_selection_paradigm(paradigm)
        self._count = 0
        self._changes = []

    @property
    def name(self):
        return self._name

    @property
    def model_type(self):
        return self._model_type

    @property
    def owner(self):
        return self._owner

    @property
    def count(self):
        return self._count

    @property
    def capacity(self):
        return self._capacity

    def assign_owner(self, owner):
        self._owner = owner

    def report(self):
        return self.__repr__() + ' ({}: {:d} / {:d})'.format(self.model_type, len(self._storage), self._capacity)

    def index(self, component):
        return self._storage.index(component)

    def store(self, component):
        if component.model.name != self.model_type:
            raise TypeError("'{}' of type '{}' can not be stored in StorageComponent '{}' which was "
                            "only defined to store component types "
                            "{}".format(component.name, component.model.name, self.name, self._model_type))
        self._storage.append(component)
        component.assign_owner(self)
        self._count += 1
        self._changes.append((CLOCK(), 1))

    def pluck(self, index=None, paradigm=None):

        if type(index) is not None:
            return self._storage.pop(index)

        if paradigm is None:
            paradigm = self._selection_paradigm
        index = paradigm(self._storage)
        self._count -= 1
        self._changes.append((CLOCK(), -1))
        return self._storage.pop(index)

    def _test_selection_paradigm(self, paradigm, n=50):
        storage = copy(self._storage)

        output = []
        for i in range(min(10, len(storage))):
            bad_indices = []
            max_index = len(storage) - 1
            for _ in range(n):
                test_index = paradigm(storage)
                if test_index < 0 or test_index > max_index:
                    bad_indices.append(test_index)
            if len(bad_indices) > 0:
                raise IndexError('selection paradigm chose {:d} bad indices of {:d} tries: {} which are outside of '
                                 'storage range {}'.format(len(bad_indices), n, str(bad_indices), str([0, max_index])))
            output.append(storage.pop(test_index))

    def __repr__(self):
        return self.name

    def __contains__(self, component):
        return component in self._storage


class ProcessingFacility(object):
    ID = 0
    ABBREVIATION = 'PF'

    def __init__(self,
                 name=None,
                 storage_types_capacities=(),
                 process_types_rates=()):
        self._id = ProcessingFacility.ID + 0
        ProcessingFacility.ID += 1
        self._name = name if name is not None else '{}-{:05d}'.format(self.ABBREVIATION, self._id)
        self._owner = None

        self._storage_in_paradigm = lambda valid_stores: argmin([c_s.count / c_s.capacity for c_s in valid_stores])
        self._storage_out_paradigm = lambda valid_stores: argmax([c_s.count / c_s.capacity for c_s in valid_stores])

        self._component_stores = []
        for t_c in storage_types_capacities:
            self.add_component_store(StorageComponent(*t_c))

        self._available_processes = []
        self._processing_lines = []
        for args in process_types_rates:
            if hasattr(args, '__iter__'):
                self.add_processing_line(*args)
            else:
                self.add_processing_line(args)

    @property
    def name(self):
        return self._name

    @property
    def owner(self):
        return self._owner

    @property
    def available_processes(self):
        return self._available_processes

    def assign_owner(self, owner):
        self._owner = owner

    def add_component_store(self, component_store):
        self._component_stores.append(component_store)
        component_store.assign_owner(self)

    def store(self, component):
        if hasattr(component, '__iter__'):
            for c in component:
                c_s = self.select_storage_in(c)
                c_s.store(c)
        elif type(component) is Component:
            c_s = self.select_storage_in(component)
            c_s.store(component)

    def get_valid_stores(self, thing):
        # thing can be a Component instance or a ComponentModel
        model_type = thing.model.name if type(thing) is Component else thing.name
        return [c_s for c_s in self._component_stores if model_type is c_s.model_type]

    def select_storage_in(self, component):
        valid_stores = self.get_valid_stores(component)
        index = self._storage_in_paradigm(valid_stores)
        return valid_stores[index]

    def select_storage_out(self, component):
        valid_stores = self.get_valid_stores(component)
        index = argmax([c_s.count / c_s.capacity for c_s in valid_stores])
        return valid_stores[index]

    def add_processing_line(self, *processes):
        if 'int' in type(processes[-1]).__name__ or 'float' in type(processes[-1]).__name__:
            multiplier = float(processes[-1])
            processes = processes[:-1]
        else:
            multiplier = 1.0
        if len(processes) == 0 and hasattr(processes[0], '__iter__'):
            processes = processes[0]

        self._processing_lines.append(ProcessingLine(processing_multiplier=multiplier, processes=processes))
        self._processing_lines[-1].assign_owner(self)

        for process in processes:
            if process.name not in self.available_processes:
                self._available_processes.append(process.name)

    def pull_component(self, comordel):
        if type(comordel) is Component:
            for c_s in self._component_stores:
                if comordel in c_s:
                    index = c_s.index(comordel)
                    return c_s.pluck(index)
            raise ValueError("Component '{}' is not in any of '{}'s component "
                             "stores".format(str(comordel), str(self)))
        elif type(comordel).__name__ is 'ComponentModel':
            c_s = self.select_storage_out(comordel)
            return c_s.pluck()

    def report(self):
        mat = '{:%d} - {:^%d} - {}' % (len(self.name) + 2, max(len('storage'), len('processes')))
        lines = list()

        if len(self._component_stores) > 0:
            lines.append(mat.format(self.name, 'storage', self._component_stores[0].report()))
            for c_s in self._component_stores[1:]:
                lines.append(mat.format('', '', c_s.report()))
        else:
            lines.append(mat.format(self.name, 'storage', str(None)))

        if len(self._processing_lines) > 0:
            lines.append(mat.format('', 'processes', self._processing_lines[0].report()))
            for p_l in self._processing_lines[1:]:
                lines.append(mat.format('', '', p_l.report()))
        else:
            lines.append(mat.format('', 'processes', str(None)))

        return '\n'.join(lines)


class ProcessingLine(object):
    ID = 0
    ABBREVIATION = 'PL'

    def __init__(self, name=None, processing_multiplier=1.0, processes=()):
        self._id = ProcessingLine.ID + 0
        ProcessingLine.ID += 1
        self._name = name if name is not None else '{}-{:05d}'.format(self.ABBREVIATION, self._id)
        self._processing_multiplier = processing_multiplier
        self._processes = []
        self._available_processes = []
        self._active_process = None
        self.add_processes(*processes)
        self._owner = None
        self._ = []

    @property
    def owner(self):
        return self._owner

    @property
    def available_processes(self):
        return self._available_processes

    def assign_owner(self, owner):
        self._owner = owner
        for process in self._processes:
            process.assign_owner(self._owner)

    def add_processes(self, *processes):
        if len(processes) == 0 and hasattr(processes[0], '__iter__'):
            processes = processes[0]

        for process in processes:
            self._processes.append(process)
            self._available_processes.append(process.name)

    def report(self):
        return self.__repr__() + ' (active process: {})'.format(self._active_process)

    def __repr__(self):
        return self._name


class Platform(object):
    ID = 0
    ABBREVIATION = 'PL'

    def __init__(self, name, storage_types_capacities):
        self._id = Platform.ID + 0
        Platform.ID += 1
        self._name = name if name is not None else '{}-{:05}'.format(self.ABBREVIATION, self._id)
        self._component_stores = [StorageComponent(*t_c) for t_c in storage_types_capacities]
        self._owner = None

    @property
    def owner(self):
        return self._owner

    def assign_owner(self, owner):
        self._owner = owner

    def detach(self):
        self._owner = None
