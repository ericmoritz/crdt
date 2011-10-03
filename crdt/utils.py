# -*- coding: utf-8 -*-
import bisect

class SortedSet(MutableSet):
    def __init__(self, items):
        if items:
            self.items = sorted(items)
        else:
            self.items = []

    def __repr__(self):
        return "SortedSet(%s)" % (self.items, )

    def add(self, element):
        i = bisect.bisect_left(self.items, element)

        if i == len(self.items):
            self.items.append(element)
        elif self.items[i] != element:
            self.items.insert(i, element)

    def remove(self, element):
        try:
            i = self.items.index(element)
            del self.items[i]
        except ValueError:
            raise KeyError(element)

    def discard(self, element):
        try:
            i = self.items.index(element)
            del self.items[i]
        except ValueError:
            pass

    def __len__(self):
        return self.items.__len__()

    def __contains__(self, e):
        return self.items.__contains__(e)

    def __iter__(self):
        return iter(self.items)
