from base import StateCRDT
from copy import deepcopy
from collections import MutableSet


class GSet(StateCRDT, MutableSet):
    def __init__(self):
        self._payload = set()

    @classmethod
    def merge(cls, X, Y):
        merged = GSet()
        merged._payload = X._payload.union(Y._payload)

        return merged

    def descends_from(self, other):
        return other._payload.issubset(self._payload)

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
    A = GSet()
    B = GSet()

    A1 = A.clone()

    A1.add("eric")
    assert A1.descends_from(A)
    assert A1.value == set(["eric"])

    B1 = B.clone()
    
    B1.add("glenn")
    assert B1.descends_from(B)
    assert B1.value == set(["glenn"])

    assert A1.descends_from(B1) == False

    C = GSet.merge(A1, B1)

    assert C.descends_from(A1)
    assert C.descends_from(B1)

    assert C.value == set(["eric", "glenn"])


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

    def descends_from(self, other):
        A_descends = self.A.descends_from(other.A)
        R_descends = self.R.descends_from(other.R)
        
        return A_descends and R_descends

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
    A = TwoPSet()
    B = TwoPSet()

    A1 = A.clone()

    A1.add("eric")
    assert A1.descends_from(A)
    assert A1.value == set(["eric"])

    B1 = B.clone()
    
    B1.add("glenn")
    assert B1.descends_from(B)
    assert B1.value == set(["glenn"])

    assert A1.descends_from(B1) == False

    C = TwoPSet.merge(A1, B1)

    assert C.descends_from(A1)
    assert C.descends_from(B1)

    assert C.value == set(["eric", "glenn"])
