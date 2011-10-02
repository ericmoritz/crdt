# -*- coding: utf-8 -*-
from crdt.counters import GCounter, PNCounter

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
    assert ABB2.payload == {"a": 2, "b": 2}


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
