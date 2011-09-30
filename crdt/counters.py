# -*- coding: utf8 -*-
from time import time
from copy import deepcopy
from base import StateCRDT


class GCounter(StateCRDT):
    def __init__(self):
        self._payload = {}

    #
    # State-based CRDT API
    #
    def clone(self):
        return GCounter.from_payload(deepcopy(self.payload))

    def get_payload(self):
        return self._payload

    def set_payload(self, newp):
        self._payload = newp

    payload = property(get_payload, set_payload)

    @property
    def value(self):
        return sum(c for (c, ts) in self.payload.itervalues())

    @staticmethod
    def from_payload(payload):
        new = GCounter()
        new.payload = payload
        return new
        
    @staticmethod
    def merge(X, Y):
        """
        let ∀i ∈ [0,n − 1] : Z.P[i] = max(X.P[i],Y.P[i])
        """
        
        keys = set(X.payload.iterkeys()) | set(Y.payload.iterkeys())
        
        gen = ((key, max(X.payload.get(key, 0), Y.payload.get(key, 0)))
               for key in keys)
        
        return GCounter.from_payload(dict(gen))

    def descends_from(self, other):
        """
        (∀i ∈ [0, n − 1] : X.P [i] ≤ Y.P [i])
        
        Return True if all values in X are less than Y
        """
        try:
            return all(self.payload[key] <= other.payload[key]
                       for key in other.payload)
        except KeyError:
            return False

    #
    # GCounter API
    #
    def increment(self, cid):
        try:
            (c, ts) = self.payload[cid]
        except KeyError:
            c = 0

        self.payload[cid] = (c+1, time())


class PNCounter(StateCRDT):
    def __init__(self):
        self.P = GCounter()
        self.N = GCounter()
    #
    # State-based CRDT API
    #
    @property
    def payload(self):
        return {
            "P": self.P.payload,
            "N": self.N.payload
            }

    @staticmethod
    def from_payload(payload):
        new = PNCounter()
        new.P.payload = payload['P']
        new.N.payload = payload['N']

        return new

    def clone(self):
        return PNCounter.from_payload(deepcopy(self.payload))

    @property
    def value(self):
        return self.P.value - self.N.value

    @staticmethod
    def merge(X, Y):
        merged_P = GCounter.merge(X.P, Y.P)
        merged_N = GCounter.merge(X.N, Y.N)

        merged_payload = {
            "P": merged_P.payload,
            "N": merged_N.payload,
            }
        return PNCounter.from_payload(merged_payload)

    def descends_from(self, other):
        """
        (∀i ∈ [0, n − 1] : X.P [i] ≤ Y.P [i])
        
        Return True if all values in X are less than Y
        """
        P_descends = self.P.descends_from(other.P)
        N_descends = self.N.descends_from(other.N)

        return P_descends and N_descends

    #
    # Counter API
    # 
    def increment(self, cid):
        self.P.increment(cid)

    def decrement(self, cid):
        self.N.increment(cid)


def test_gcounter():
    A = GCounter()
    assert A.value == 0

    B = GCounter()
    assert B.value == 0

    A1 = A.clone()
    A1.increment("a")
    assert A1.value == 1

    B1 = B.clone()
    B1.increment("b")
    assert B1.value == 1

    assert A1.descends_from(A)
    assert B1.descends_from(B)
    assert A1.descends_from(B1) == False
    
    A2 = A1.clone()
    A2.increment("a")
    assert A2.value == 2
    
    C = GCounter.merge(A2, B1)
    assert C.value == 3, C.value

    C.increment("c")
    assert C.value == 4, C.value

    assert C.descends_from(B1)
    assert C.descends_from(A2)


def test_pncounter():
    A = PNCounter()
    assert A.value == 0

    B = PNCounter()
    assert B.value == 0

    A1 = A.clone()
    A1.increment("a")
    assert A1.value == 1

    B1 = B.clone()
    B1.increment("b")
    assert B1.value == 1

    assert A1.descends_from(A)
    assert B1.descends_from(B)
    assert A1.descends_from(B1) == False
    
    A2 = A1.clone()
    A2.increment("a")
    assert A2.value == 2
    
    C = PNCounter.merge(A2, B1)
    assert C.value == 3, C.value

    C.increment("c")
    assert C.value == 4, C.value

    assert C.descends_from(B1)
    assert C.descends_from(A2)

    C.decrement("c")
    assert C.value == 3, C.value
    C.decrement("c")
    assert C.value == 2, C.value
    C.decrement("c")
    assert C.value == 1, C.value
    C.decrement("c")
    assert C.value == 0, C.value
    C.decrement("c")
    assert C.value == -1, C.value

    
if __name__ == '__main__':
    test_gcounter()
    test_pncounter()
