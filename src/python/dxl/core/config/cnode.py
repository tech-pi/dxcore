from typing import Dict
from enum import Enum


class QueryKey:
    def __init__(self, keys):
        """
        `key`: All possible value which is converatble to key.
        """
        if not isinstance(keys, (list, tuple)):
            raise TypeError(
                "Expected keys to be list or tuple, got {}.".format(keys))
        self._keys = tuple(keys)

    def head(self):
        return self._keys[0]

    def tail(self):
        return QueryKey(self._keys[1:])

    def last(self):
        return QueryKey(tuple(self._keys[-1]))

    def __len__(self):
        return len(self._keys)


class CNode:
    def __init__(self, config=None):
        """
        `config`: initial configs, which should be a dict of CNode/value.
        """
        self._children = {}
        self._values = {}
        if config is None:
            config = {}
        for k, v in config.items():
            if isinstance(v, CNode):
                self._children[k] = v
            else:
                self._values[k] = v

    def read(self, key: QueryKey):
        """
        Find value curresponding to key.
        if len(key) == 1, then find it in self._values,
        else find it in self._children recuresivly.
        """
        if len(key) == 1:
            if key.head() in self._values:
                return self._values.get(key.head())
            else:
                return self._children.get(key.head())
        else:
            if not key.head() in self._children:
                return None
            return self._children.get(key.head()).read(key.tail())

    @property
    def children(self):
        return self._children

    @property
    def values(self):
        return self._values

    def __getitem__(self, key):
        if key in self._children:
            return self._children[key]
        elif key in self._values:
            return self._values[key]
        else:
            raise KeyError(key)

    def __iter__(self):
        return iter(list(self._children.keys()) + list(self._values.keys()))

    def assign(self, key: str, node_or_value, *, allow_existed=True):
        if isinstance(node_or_value, CNode):
            if not allow_existed and key in self._children:
                raise ValueError("Key {} alread existed.".format(key))
            if key in self._values:
                raise ValueError("Duplicated key {} in value.".format(key))
            self._children[key] = node_or_value
        else:
            if not allow_existed and key in self._values:
                raise ValueError("Key {} alread existed.".format(key))
            if key in self._children:
                raise ValueError("Duplicated key {} in children.".format(key))
            self._values[key] = node_or_value

    def create(self, key: QueryKey, node_or_value):
        """
        Create a new child node or value.
        """
        if len(key) == 1:
            self.assign(key.head(), node_or_value, allow_existed=False)
        else:
            if key.head() in self:
                raise ValueError("Key {} alread existed.".format(key.head()))
            c = CNode()
            c.create(key.tail(), node_or_value)
            self._children[key.head()] = c

    def is_ancestor_of(self, n):
        for _, v in self._children.items():
            if v is n or v.is_ancestor_of(n):
                return True
        return False

    # def update(self, key:QueryKey, node_or_value):
    #     if len(key) == 1:
    #         self.assign(key.head())
    #     else:
    #         self._children[key.head()].update(key.tail(), node)


class Keywords:
    EXPAND = '__expand__'


def from_dict(config_dict):
    def need_expand(v):
        if not isinstance(v, dict):
            return False
        if Keywords.EXPAND in v:
            return v[Keywords.EXPAND]
        return True

    config_parsed = {}
    for k, v in config_dict.items():
        if need_expand(v):
            config_parsed[k] = from_dict(v)
        else:
            config_parsed[k] = v
    return CNode(config_parsed)


class DefaultConfig:
    _current = None

    def __init__(self, cnode):
        pass

    @property
    def node(self):
        return self._current