# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod, abstractproperty
from copy import deepcopy
import base64
import random


def random_client_id():
    """Returns a random client identifier"""
    return 'py_%s' % base64.b64encode(str(random.randint(1, 0x40000000)))


class StateCRDT(object):
    __metaclass__ = ABCMeta

    #
    # Abstract methods
    #

    @abstractmethod
    def __init__(self):
        pass

    @abstractproperty
    def value(self):
        """Returns the expected value generated from the payload"""
        pass

    @abstractproperty
    def payload(self):
        """This is a deepcopy-able version of the CRDT's payload.

        If the CRDT is going to be serialized to storage, this is the
        data that should be stored.
        """
        pass

    @classmethod
    @abstractmethod
    def merge(cls, X, Y):
        """Merge two replicas of this CRDT"""
        pass

    #
    # Built-in methods
    #

    def __repr__(self):
        return "<%s %s>" % (self.__class__, self.value)

    def clone(self):
        """Create a copy of this CRDT instance"""
        return self.__class__.from_payload(deepcopy(self.payload))

    @classmethod
    def from_payload(cls, payload, *args, **kwargs):
        """Create a new instance of this CRDT using a payload.  This
        is useful for creating an instance using a deserialized value
        from a datastore."""
        new = cls(*args, **kwargs)
        new.payload = payload
        return new
