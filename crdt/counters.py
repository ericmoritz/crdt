# -*- coding: utf-8 -*-
from copy import deepcopy
from base import StateCRDT, random_client_id
from abc import ABCMeta


class GCounter(StateCRDT):
    def __init__(self, client_id=None):
        self._payload = {}
        self.client_id = client_id or random_client_id()
    #
    # State-based CRDT API
    #
    def get_payload(self):
        return self._payload

    def set_payload(self, newp):
        self._payload = newp

    def clone(self):
        new = super(GCounter, self).clone()

        # Copy the client id
        new.client_id = self.client_id
        return new

    payload = property(get_payload, set_payload)

    @property
    def value(self):
        return sum(self.payload.itervalues())


    def compare(self, other):
        """
        (∀i ∈ [0, n − 1] : X.P [i] ≤ Y.P [i])
        """
        return all(self.payload.get(key, 0) <= other.payload.get(key, 0)
                   for key in other.payload)

    @classmethod
    def merge(cls, X, Y):
        """
        let ∀i ∈ [0,n − 1] : Z.P[i] = max(X.P[i],Y.P[i])
        """
        keys = set(X.payload.iterkeys()) | set(Y.payload.iterkeys())
        
        gen = ((key, max(X.payload.get(key, 0), Y.payload.get(key, 0)))
               for key in keys)
        
        return GCounter.from_payload(dict(gen))
    #
    # Number API
    #
    def __str__(self):
        return self.value.__str__()
    #
    # GCounter API
    #
    def increment(self):
        try:
            c = self.payload[self.client_id]
        except KeyError:
            c = 0

        self.payload[self.client_id] = c + 1


class PNCounter(StateCRDT):
    def __init__(self, client_id=None):
        self.P = GCounter()
        self.N = GCounter()
        self.client_id = client_id or random_client_id()

    #
    # State-based CRDT API
    #
    def get_payload(self):
        return {
            "P": self.P.payload,
            "N": self.N.payload
            }

    def set_payload(self, payload):
        self.P.payload = payload['P']
        self.N.payload = payload['N']

    payload = property(get_payload, set_payload)

    def get_client_id(self):
        return self._cid
        
    def set_client_id(self, client_id):
        self._cid = client_id
        self.P.client_id = client_id
        self.N.client_id = client_id

    client_id = property(get_client_id, set_client_id)

    def clone(self):
        new = super(PNCounter, self).clone()

        # Copy the client id
        new.client_id = self.client_id
        return new


    @property
    def value(self):
        return self.P.value - self.N.value

    @classmethod
    def merge(cls, X, Y):
        merged_P = GCounter.merge(X.P, Y.P)
        merged_N = GCounter.merge(X.N, Y.N)

        merged_payload = {
            "P": merged_P.payload,
            "N": merged_N.payload,
            }
        return PNCounter.from_payload(merged_payload)

    def compare(self, other):
        """
        (∀i ∈ [0, n − 1] : X.P [i] ≤ Y.P [i] ∧ ∀i ∈ [0, n − 1] : X.N[i] ≤ Y.N[i]
        """
        P_compare = self.P.compare(other.P)
        N_compare = self.N.compare(other.N)
        
        return P_compare and N_compare

    #
    # Counter API
    # 
    def increment(self):
        self.P.increment()

    def decrement(self):
        self.N.increment()


def test_gcounter():
    """
     []
   /    \
 A[a:1] B[b:1]       +1, +1
   |     |  \
   |     |    \
   |    /      |
 AB[a:1, b:1]  |     merge 
   |           |
 AB[a:2, b:1]  |      +1
   |           |
    \      B2[b:2]    +1
     \         |
      \       /
    ABB2[a:2, b:2]    merge
    """

    A = GCounter(client_id="a")
    B = GCounter(client_id="b")
    
    A.increment()
    assert A.payload == {"a": 1}

    B.increment()
    assert B.payload == {"b": 1}

    B2 = B.clone()
    assert B2.payload == {"b": 1}

    B2.increment()
    assert B2.payload == {"b": 2}

    AB = GCounter.merge(A, B)
    AB.client_id = "a"
    assert AB.payload == {"a": 1, "b": 1}

    AB.increment()
    assert AB.payload == {"a": 2, "b": 1}
    
    ABB2 = GCounter.merge(AB, B2)
    assert ABB2.payload == {"a":2, "b":2}
    
def test_pncounter():
    """
        [ ] - [ ]
         /       \ 
  [a:1] - [ ]     [ ] - [b:1]   +1 -1
        |           |
  [a:1] - [a:1]   [ ] - [b:2]   -1 -1
        |          / \
         \       /     \ 
          \     /       |
  [a:1] - [a:1 b:2]     |      merge
        |               |
        |         [ ] - [b:3]   -1
         \             /
        [a:1] - [a:1 b:3]         merge
        """

    A = PNCounter(client_id="a")
    B = PNCounter(client_id="b")

    A.increment()
    B.decrement()
    
    A.decrement()
    B.decrement()

    AB = PNCounter.merge(A, B)

    B2 = B.clone()
    B2.decrement()
    
    ABB2 = PNCounter.merge(AB, B2)
    
    assert ABB2.value == -3

if __name__ == '__main__':
    test_gcounter()
    test_pncounter()
