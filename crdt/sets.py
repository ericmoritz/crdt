
class GSet(object):
    def __init__(self, payload=None):
        self.payload = payload || set()

    @property
    def value(self):
        return self.payload
