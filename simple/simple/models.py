from simple.trees import AbstractTreeStrict
from simple.objects import Component
from simple.processes import Process, Consume
from simple.simulation import CLOCK

DEFINED_TYPES = []


class ComponentType(str):
    """Class to define and track components so that duplicate names are not created

    """
    ID = 0
    ABBREVIATION = 'CT'

    def __init__(self, model_name):
        if hasattr(self, '_id'):
            return
        self._id = self.ID + 0
        type(self).ID += 1

        self._models = []
        self._components = []
        self._manifests = []
        for tracker in ['models', 'components', 'manifests']:
            setattr(self, 'track_' + tracker, lambda x: getattr(self, '_' + tracker).append(x))

        DEFINED_TYPES.append(self)

    def __new__(cls, model_name):
        if model_name in DEFINED_TYPES:
            return DEFINED_TYPES[DEFINED_TYPES.index(model_name)]
        else:
            return super().__new__(cls, model_name)

    @property
    def id(self):
        return self._id


class ComponentManifest(object):
    def __init__(self, model_name, minimum, maximum, enforce_minimum):
        if model_name in DEFINED_TYPES:
            self._model_name = DEFINED_TYPES[DEFINED_TYPES.index(model_name)]
        else:
            self._model_name = ComponentType(model_name)
        self._model_name.track_manifest(self)
        self._minimum = minimum
        self._maximum = maximum
        self._enforce_minimum = enforce_minimum

    @property
    def minimum(self):
        return self._minimum

    @property
    def maximum(self):
        return self._maximum

    @property
    def enforce_minimum(self):
        return self._enforce_minimum


class ComponentModel(AbstractTreeStrict):
    """A class to create blueprints/archetypes component models for objects in an inventory"""

    def __init__(self, model_name, life_time_steps, creation_time_steps, base_failure_rate):
        """

        :param model_name: str or ComponentType instance, name of component, passing a string will create a
                    ComponentType instance with the same 'model_name' in the DEFINED_TYPES master list
        :param life_time_steps: float, number of simulation time steps until the object expires/ages out
        :param creation_time_steps: float, number of simulation time steps it takes to create the object
        :param base_failure_rate: float (0, 1], probability of failure
        """
        super().__init__()
        self._model_name = ComponentType(model_name)
        self._life_time_steps = life_time_steps
        self._creation_time_steps = creation_time_steps
        self._base_failure_rate = base_failure_rate
        self._components = []
        self._expire_process = Process(Consume(inputs=(self,)), name='expire_' + model_name)

    @property
    def node_name(self):
        return self._model_name

    @property
    def name(self):
        return self._model_name

    @property
    def life_time_steps(self):
        return self._life_time_steps

    @property
    def creation_time_steps(self):
        return self._creation_time_steps

    @property
    def components(self):
        return self._components

    def add_component(self, component_model):
        super().add_child(component_model)
        # if type(component_model) is not ComponentModel:
        #     raise TypeError("Instances of type '{}' can not be a component of ComponentModels, "
        #                     "only other ComponentModel instances can be".format(type(component_model.__name__)))
        # self._components.append(component_model)

    def create(self):
        return Component(model=self, date_created=CLOCK())

    def get_expiry_process(self):
        return self._expire_process
