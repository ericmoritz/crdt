# -*- coding: utf-8 -*-
from base import StateCRDT, random_client_id
from copy import deepcopy
from collections import MutableSet
from counters import GCounter
from time import time
import uuid


class SetStateCRDT(StateCRDT, MutableSet):

    def __contains__(self, element):
        return self.value.__contains__(element)

    def __iter__(self):
        return self.value.__iter__()

    def __len__(self):
        return self.value.__len__()


class GSet(SetStateCRDT):
    def __init__(self):
        self._payload = set()

    @classmethod
    def merge(cls, X, Y):
        merged = GSet()
        merged._payload = X._payload.union(Y._payload)

        return merged

    def compare(self, other):
        return self.issubset(other)

    @property
    def value(self):
        return self._payload

    def get_payload(self):
        return list(self._payload)

    def set_payload(self, payload):
        self._payload = set(payload)

    payload = property(get_payload, set_payload)

    #
    # Set API
    #
    def add(self, element):
        self._payload.add(element)

    def discard(self, element):
        raise NotImplementedError("This is a grow-only set")


class LWWSet(SetStateCRDT):
    def __init__(self):
        self.A = {}
        self.R = {}

    def compare(self, other):
        pass

    @property
    def value(self):
        return set(e for (e, ts) in self.A.iteritems()
                   if ts >= self.R.get(e, 0))

    @classmethod
    def _merged_dicts(cls, x, y):
        new = {}
        keys = set(x) | set(y)
        for key in keys:
            new[key] = max(x.get(key,0), y.get(key, 0))

        return new

    @classmethod
    def merge(cls, X, Y):
        payload = {
            "A": cls._merged_dicts(X.A, Y.A),
            "R": cls._merged_dicts(X.R, Y.R),
            }

        return cls.from_payload(payload)

    def get_payload(self):
        return {
            "A": self.A,
            "R": self.R,
            }

    def set_payload(self, payload):
        self.A = payload['A']
        self.R = payload['R']

    payload = property(get_payload, set_payload)

    def add(self, element):
        self.A[element] = (time(), )
        
    def discard(self, element):
        if element in self.A:
            self.R[element] = (time(), )


class TwoPSet(SetStateCRDT):
    def __init__(self):
        self.A = GSet()
        self.R = GSet()

    @classmethod
    def merge(cls, X, Y):
        merged_A = GSet.merge(X.A, Y.A)
        merged_R = GSet.merge(X.R, Y.R)

        merged_payload = {
            "A": merged_A,
            "R": merged_R,
            }

        return TwoPSet.from_payload(merged_payload)

    def compare(self, other):
        """
        (S.A ⊆ T.A ∨ S.R ⊆ T.R)
        """
        A_compare = self.A.compare(other.A)
        R_compare = self.R.compare(other.R)

        return A_compare or R_compare

    @property
    def value(self):
        return self.A.value - self.R.value

    def get_payload(self):
        return {
            "A": self.A.payload,
            "R": self.R.payload,
            }

    def set_payload(self, payload):
        self.A = GSet.from_payload(payload['A'])
        self.R = GSet.from_payload(payload['R'])

    payload = property(get_payload, set_payload)

    def __contains__(self, element):
        return element in self.A and element not in self.R

    def __iter__(self):
        return self.value.__iter__(element)

    def __len__(self):
        return self.value.__len__(element)

    def add(self, element):
        self.A.add(element)

    def discard(self, element):
        if element in self:
            self.R.add(element)
