# -*- coding: utf-8 -*-
from base import StateCRDT, random_client_id
from copy import deepcopy
from collections import MutableSet
from counters import GCounter
import uuid

class GSet(StateCRDT, MutableSet):
    def __init__(self):
        self._payload = set()

    def __str__(self):
        return "GSet(%s)" % (list(self.value))

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

    def __str__(self):
        return "TwoPSet(%s)" % (list(self.value))

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


class EMSet(StateCRDT, MutableSet):
    def __init__(self, client_id=None):
        self.client_id = client_id or random_client_id()
        self._payload = {}

    @classmethod
    def _get_counters(cls, emset, element):
        if element in emset.payload:
            a, r = emset.payload[element]
            return (GCounter.from_payload(a, client_id=emset.client_id),
                    GCounter.from_payload(r, client_id=emset.client_id))
        else:
            return (GCounter(client_id=emset.client_id),
                    GCounter(client_id=emset.client_id))

    def add(self, element):
        A, R = self._get_counters(self, element)

        # if the A counter is less than or equal to the R counter,
        # increment the R counter and replace the A payload making A > R
        if A <= R:
            newA = R.clone()
            newA.increment()

            self.payload[element] = (newA.payload, R.payload)

        # We don't have to do anything if the A_counter is already
        # creater than the R counter

    def discard(self, element):
        A, R = self._get_counters(self, element)
        
        # If the R value is less than the A value
        # take the A value, increment it and replace R
        if R < A:
            newR = A.clone()
            newR.increment()
            self.payload[element] = (A.payload, newR.payload)

    @property
    def value(self):
        def gen():
            for element in self.payload:
                A, R = self._get_counters(self, element)
                if A > R:
                    yield element

        return set(gen())

    def get_payload(self):
        return self._payload

    def set_payload(self, payload):
        self._payload = payload

    payload = property(get_payload, set_payload)

    @classmethod
    def merge(cls, X, Y):
        payload = {}

        elements = set(X.payload) | set(Y.payload)

        for element in elements:
            Ax, Rx = cls._get_counters(X, element)
            Ay, Ry = cls._get_counters(Y, element)

            newA = GCounter.merge(Ax, Ay)
            newR = GCounter.merge(Rx, Ry)

            payload[element] = (newA.payload, newR.payload)

        return cls.from_payload(payload)

    def compare(self, other):
        pass

    def __contains__(self, element):
        A, R = self._get_counters(self, element)
        return A > R

    def __iter__(self):
        return self.value.__iter__()
    
    def __len__(self):
        return self.value.__len__()

def test_emset():
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
    A = EMSet()
    B = EMSet()
    
    A.add("eric")
    B.add("glenn")
    
    A.add("mark")
    B.add("tom")

    AB = EMSet.merge(A, B)

    B2 = B.clone()
    B2.remove("tom")

    ABB2 = EMSet.merge(AB, B2)
    assert ABB2.value == {"eric", "mark", "glenn"}, ABB2.value

    B2.add("tom")
    
    ABB2 = EMSet.merge(ABB2, B2)
    assert ABB2.value == {"eric", "mark", "glenn", "tom"}, ABB2.value

