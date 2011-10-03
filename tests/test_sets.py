# -*- coding: utf-8 -*-
from crdt.sets import GSet, TwoPSet, ORSet, LWWSet
from crdt import sets
import time

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


def test_lwwset():
    A = LWWSet()
    
    fake_time = 1

    def mock_time():
        return fake_time
    old_time = sets.time
    sets.time = mock_time

    A.add("eric")

    B = A.clone()
    C = A.clone()

    # Test that concurrent updates favor add
    fake_time = 2
    B.add("eric")
    C.remove("eric")

    D = LWWSet.merge(B, C)

    assert D.value == set(["eric"])

    sets.time = old_time


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
