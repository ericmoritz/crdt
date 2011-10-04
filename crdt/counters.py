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
    payload = property(get_payload, set_payload)


    def clone(self):
        new = super(GCounter, self).clone()

        # Copy the client id
        new.client_id = self.client_id
        return new


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

    def __cmp__(self, other):
        return self.value.__cmp__(other.value)


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
        (∀i ∈ [0, n − 1] : X.P [i] ≤ Y.P [i] ∧
        ∀i ∈ [0, n − 1] : X.N[i] ≤ Y.N[i]
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

    def __cmp__(self, other):
        return self.value.__cmp__(other.value)
