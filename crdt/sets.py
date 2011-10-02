# -*- coding: utf-8 -*-
from base import StateCRDT, random_client_id
from copy import deepcopy
from collections import MutableSet
from counters import GCounter
from time import time
import uuid


class GSet(StateCRDT, MutableSet):
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

    def __contains__(self, element):
        return self._payload.__contains__(element)

    def __iter__(self):
        return self._payload.__iter__()

    def __len__(self):
        return self._payload.__len__()


def test_gset():
    """
        {},{}
      /       \
  A{eric},{}   B{glenn},{}            +eric +glenn
    |               |
 A{eric mark},{}    |                 +mark
    |             /   \
    |           /      \
     \         /        \
      \       /     B2{glenn tom}     +tom
        \   /              \
   AB{eric mark glenn}      \         <<merge>>
            \               /
             \             /
      ABB2{eric mark tom glenn}   <<merge>>
    """
    A = GSet()
    B = GSet()

    A.add("eric")
    A.add("mark")
    B.add("glenn")
    B2 = B.clone()

    AB = GSet.merge(A, B)

    B2.add("tom")

    ABB2 = GSet.merge(AB, B2)
    assert ABB2.value == {"eric", "mark", "tom", "glenn"}, ABB2.value


class TwoPSet(StateCRDT, MutableSet):
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


def test_towpset():
    """
        {},{}
      /       \
  A{eric},{}   B{glenn},{}          +eric +glenn
    |             \
 A{eric mark},{} B{glenn tom},{}   +mark +tom
    |             /   \
    |           /      \
     \         /        \
      \       /     B2{glenn tom},{tom}   -tom
        \   /              \
   AB{eric mark tom glenn}  \   <<merge>>
            \               /
             \             /
    ABB2{eric mark tom glenn},{tom}   <<merge>>

    """
    A = TwoPSet()
    B = TwoPSet()

    A.add("eric")
    B.add("glenn")

    A.add("mark")
    B.add("tom")

    AB = TwoPSet.merge(A, B)

    B2 = B.clone()
    B2.remove("tom")

    ABB2 = TwoPSet.merge(AB, B2)
    assert ABB2.value == {"eric", "mark", "glenn"}, ABB2.value


class ORSet(TwoPSet):
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

    def __contains__(self, element):
        return self.value.__contains__(element)

    def __iter__(self):
        return self.value.__iter__(element)

    def __len__(self):
        return self.value.__len__(element)

    def add(self, element):
        item = (element, (time(), uuid.uuid4()))
        self.A.add(item)

    def discard(self, element):
        if element in self:  # This can probably be optimized
            for (e, u) in self.A:
                if element == e:
                    self.R.add((e, u))


def test_orset():
    A = ORSet()

    A.add("eric")

    # Do a concurrent add/removes.
    B = A.clone()
    C = A.clone()
    D = A.clone()

    B.add("eric")
    C.remove("eric")
    D.remove("eric")

    # With an ORSet, add trumps any concurrent removes
    BC = ORSet.merge(B, C)
    assert BC.value == {"eric"}

    # Test concurrent removes + serial add
    A = ORSet()
    A.add("eric")

    # Concurrently remove "eric"
    A1 = A.clone()
    A2 = A.clone()

    A1.remove("eric")
    assert "eric" not in A1

    A2.remove("eric")
    assert "eric" not in A2

    A1_2 = ORSet.merge(A1, A2)
    assert "eric" not in A1_2

    A1_2.add("eric")
    assert "eric" in A1_2
