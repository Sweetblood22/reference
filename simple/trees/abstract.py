from collections import defaultdict


class AbstractTree(object):
    ID = 0
    ABBREVIATION = 'TN'

    def __init__(self):
        self._children = []
        self._parent = None
        self._repr_attr = 'name'

        self._id = type(self).ID + 0
        type(self).ID += 1
        self._name = '{}-{:05d}'.format(type(self).ABBREVIATION, self._id)

    @property
    def name(self):
        return self._name

    @property
    def is_root(self):
        return self._parent is None

    @property
    def children(self):
        return self._children

    @property
    def repr_attr(self):
        return self._repr_attr

    @repr_attr.setter
    def repr_attr(self, value):
        if not hasattr(self, value):
            raise AttributeError("This '{}' instance does not have a '{}' attribute to be "
                                 "represented by".format(type(self).__name__, value))
        else:
            self._repr_attr = value

    def add_child(self, node):
        if not isinstance(node, AbstractTree):
            raise TypeError("'{}' of type '{}' can only have a children which are an instance of an "
                            "'AbstractTree' but an object with inheritance of {} was "
                            "passed".format(self.name, type(self).__name__, [c.__name__ for c in type(node).__mro__]))

        node.parent = self
        self._children.append(node)

    def remove_child(self, node):
        node.remove_parent()
        return self.children.remove(node)

    def assign_parent(self, node):
        if not isinstance(node, AbstractTree):
            raise TypeError("'{}' of type '{}' can only have a parent which is an instance of an "
                            "'AbstractTree' but an object with inheritance of {} was "
                            "passed".format(self.name, type(self).__name__, [c.__name__ for c in type(node).__mro__]))

        self._parent = node
        node.children.append(self)

    def remove_parent(self):
        if self._parent is not None:
            self._parent.remove_child(self)
            self._parent = None

    def _child_name_length(self, repr_attr=None):
        if repr_attr is None:
            repr_attr = self._repr_attr
        return max([len(getattr(ch, repr_attr)) for ch in self._children])

    def __repr__(self, width=None, repr_attr=None):
        if repr_attr is None:
            repr_attr = self._repr_attr

        if width is None:
            width = len(getattr(self, repr_attr))
        if len(self._children) == 0:
            # force the repr attribute to be a string for printing
            return str(getattr(self, repr_attr))
        child_width = self._child_name_length(repr_attr=repr_attr)
        nested_lines = [node.__repr__(width=child_width, repr_attr=repr_attr).split('\n') for node in self._children]
        new_lines = []
        fill = ' ' * (width + 3)
        f = '{:^' + str(width) + '} - '
        for i, lines in enumerate(nested_lines):
            for j, line in enumerate(lines):
                if i + j == 0:
                    new_lines.append(f.format(getattr(self, repr_attr)) + line)
                else:
                    new_lines.append(fill + line)

        return '\n'.join(new_lines)

    def get_ancestors(self):
        if self.is_root:
            return []
        else:
            return [self._parent] + self._parent.get_ancestors()

    def get_depth(self):
        return len(self.get_ancestors())

    def get_root(self):
        return self.get_ancestors()[-1]

    def node_count_by_attr(self, attr=None):
        if attr is None:
            attr = self._repr_attr

        counts = defaultdict(int)
        counts[getattr(self, attr)] += 1
        for node in self._children:
            for cm, n in node.node_count_by_attr(attr=attr).items():
                counts[cm] += n
        return counts

    def nodes_with_attr_value(self, value, attr=None):
        if attr is None:
            attr = self._repr_attr
        nodes = [self] if getattr(self, attr) == value else []
        if len(self.children) == 0:
            return nodes
        else:
            return nodes + [child for child in self.children if getattr(child, attr) == value]


class AbstractTreeStrict(AbstractTree):
    ID = 0
    ABBREVIATION = 'SN'

    def __init__(self):
        super().__init__()

    def add_child(self, node):
        if type(node) is not type(self):
            raise TypeError("'{}' is a AbstractTreeStrict instance and thus can not have a child of different type: "
                            "'{}'".format(type(self).__name__, type(node).__name__))
        else:
            super().add_child(node)

    def assign_parent(self, node):
        if type(node) is not type(self):
            raise TypeError("'{}' is a AbstractTreeStrict instance and thus can not have a parent of different type: "
                            "'{}'".format(type(self).__name__, type(node).__name__))

        else:
            super().assign_parent(self)
