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


class ORSet(SetStateCRDT):
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

        return cls.from_payload(merged_payload)

    def compare(self, other):
        """
        (S.A ⊆ T.A ∨ S.R ⊆ T.R)
        """
        A_compare = self.A.compare(other.A)
        R_compare = self.R.compare(other.R)

        return A_compare or R_compare

    def get_payload(self):
        return {
            "A": self.A.payload,
            "R": self.R.payload,
            }

    def set_payload(self, payload):
        self.A = GSet.from_payload(payload['A'])
        self.R = GSet.from_payload(payload['R'])

    payload = property(get_payload, set_payload)

    @property
    def value(self):
        S = self.A.value - self.R.value
        return set(e for (e, u) in S)

    def add(self, element):
        item = (element, (time(), uuid.uuid4()))
        self.A.add(item)

    def discard(self, element):
        if element in self:  # This can probably be optimized
            for (e, u) in self.A:
                if element == e:
                    self.R.add((e, u))
