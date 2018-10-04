from collections import defaultdict
from simple.simulation import Action, CLOCK


class Process(object):
    ID = 0
    ABBREVIATION = 'PR'

    def __init__(self, *process_steps, name=None):
        if len(process_steps) == 1 and hasattr(process_steps[0], '__iter__'):
            process_steps = process_steps[0]

        if not all([isinstance(p_s, ProcessStep) for p_s in process_steps]):
            raise TypeError("A 'Process' instance can only be populated by 'ProcessStep' instances")
        self._id = Process.ID + 0
        Process.ID += 1
        self._name = name if name is not None else '{}-{:05d}'.format(self.ABBREVIATION, self._id)

        self._process_steps = []

        self._owner = None
        self._inputs = []
        self._outputs = []
        self._time_steps = sum([p_s.step_duration for p_s in self._process_steps])

        # assign each ProcessStep in the chain to instance, check that process has access to component
        # stores of the appropriate type
        for p_s in self._process_steps:
            p_s.assign_process(self)

        for p_s in process_steps:
            self.add_step(p_s)

    @property
    def name(self):
        return self._name

    @property
    def process_steps(self):
        return self._process_steps

    @property
    def inputs_models(self):
        # list of lists giving names of models required for each inputs at each step
        return [[model.name for model in p_s.inputs] for p_s in self._process_steps]

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        return self._outputs

    @property
    def time_steps(self):
        return self._time_steps

    def pull_input(self, model_name):
        return self._owner.pull_component(model_name)

    def assign_owner(self, owner):
        self._owner = owner

    def add_step(self, process_step):

        if len(self.process_steps) == 0:
            self._inputs.append(process_step.inputs)
        else:
            inputs, needed = process_step.parse_inputs(self._outputs[-1])
            self._inputs.append(needed)

        self._process_steps.append(process_step)

        self._outputs.append(process_step.outputs)

    def __call__(self, inputs, owner=None, step=0):
        in_types = [cm.model.name for cm in inputs]
        req_types = self.inputs_models
        if all([t in in_types for t in req_types]) and len(in_types) == len(req_types):
            return

        if owner is None:
            owner = self._owner

        p_s = self.process_steps[step]
        received, need, remaining = p_s.parse_inputs(inputs)
        retrieved = [self.pull_input(model_name) for model_name in need]
        outputs = p_s(received + retrieved)
        step += 1
        if step >= len(self._process_steps):

            for component in outputs:
                # should there be store actions?
                owner.store(component)
        else:
            # create new action for next step in process
            Action(CLOCK() + p_s.step_duration, self, inputs=remaining, step=step)

    def __repr__(self):
        return self.name


class ProcessStep(object):
    ID = 0
    ABBREVIATION = 'PS'

    def __init__(self, name=None, inputs=(), outputs=(), time_steps=0):

        self._id = type(self).ID + 0
        type(self).ID += 1
        self._name = name if name is not None else '{}-{:05d}'.format(self.ABBREVIATION, self._id)
        self._inputs = inputs
        self._outputs = outputs
        self._time_steps = time_steps
        self._process = None
        self._balanced = 0

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        return self._outputs

    @property
    def process(self):
        return self._process

    @property
    def step_duration(self):
        return self._time_steps

    def assign_process(self, process):
        self._process = process

    def parse_inputs(self, inputs):
        # if inputs do not satisfy ProcessStep's defined inputs then ask owning process to search
        # parent for StorageComponents which hold an instance which will satisfy the input
        required_models = defaultdict(int)
        for model in self.inputs:
            required_models[model.name] += 1

        have = []
        remain = []

        for component in inputs:
            if component.model.name not in required_models.keys():
                remain.append(component)
                # raise ValueError("Process step '{} {}' received a wrong component with model type it is not defined "
                #                  "to receive :'{}'".format(type(self).__name__, self.name, component.model.name))
            elif required_models[component.model.name] == 0:
                remain.append(component)
                # raise ValueError("Process step '{} {}' received an extra component with model type:"
                #                  "'{}'".format(type(self).__name__, self.name, component.model.name))
            else:
                have.append(component)
                required_models[component.model.name] -= 1
        # create a list of model names that are still needed
        need = []

        for model_name, number in required_models.items():
            need += [model_name] * number

        return have, need, remain

    def __call__(self, inputs):
        raise NotImplementedError()


class Disassemble(ProcessStep):
    ID = 0
    ABBREVIATION = 'DA'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __call__(self, inputs):
        passed, needed = self.parse_inputs(inputs)


class Assemble(ProcessStep):
    ID = 0
    ABBREVIATION = 'AS'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __call__(self, inputs):
        passed, needed = self.parse_inputs(inputs)


class Build(ProcessStep):
    ID = 0
    ABBREVIATION = 'BL'

    def __init__(self, **kwargs):
        if 'inputs' in kwargs.keys():
            if len(kwargs['inputs']) == 0:
                kwargs.pop('inputs')
            else:
                raise ValueError("'Build' ProcessStep instance should not have any 'inputs'")
        super().__init__(**kwargs)

    def __call__(self, inputs):
            raise ValueError("'Build' ProcessStep '{}' received inputs: "
                             "{}".format(self.name, str(inputs)))


class Create(ProcessStep):
    ID = 0
    ABBREVIATION = 'CR'

    def __init__(self, **kwargs):
        if 'inputs' in kwargs.keys():
            if len(kwargs['inputs']) == 0:
                kwargs.pop('inputs')
            else:
                raise ValueError("'Create' ProcessStep instance should not have any 'inputs'")
        super().__init__(**kwargs)

    def __call__(self, inputs):
        if len(inputs) > 0:
            raise ValueError("'Create' ProcessStep '{}' received inputs: "
                             "{}".format(self.name, str(inputs)))
        outputs = [c_m.create() for c_m in self.outputs]
        for c in outputs:
            if c.model.life_time_steps > 0:
                Action(CLOCK + c.model.life_time_steps, c.model.get_expiry_process(),
                       inputs=[c])

        return outputs


class Consume(ProcessStep):
    ID = 0
    ABBREVIATION = 'CS'

    def __init__(self, **kwargs):
        if 'outputs' in kwargs.keys():
            if len(kwargs['outputs']) == 0:
                kwargs.pop('outputs')
            else:
                raise ValueError("'Consume' ProcessStep instance should not have any 'outputs'")
        super().__init__(**kwargs)

    def __call__(self, inputs):
        received, need, remaining = self.parse_inputs(inputs)
        for component in received:
            owner_type = type(component.owner).__name__
            if owner_type is 'Platform':
                component.owner.detach(component)
            elif owner_type is 'Component':
                component.owner.remove_parent()
            else:
                # find a 'ProcessingFacility' owner in the owner chain
                # the 'ProcessingFacility' has a 'pull_component' method which will search its component stores
                root_owner = component.owner.owner
                owner_type = type(root_owner).__name__
                while owner_type is not 'ProcessingFacility':
                    root_owner = root_owner.owner
                    owner_type = type(root_owner).__name__
                root_owner.pull_component(component)
        return []
