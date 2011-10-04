from crdt.sets import LWWSet
from crdt.base import StateCRDT


class Friendship(StateCRDT):
    def __init__(self):
        # The user key is considered constant among replicas
        # so no CRDT is needed
        self.user_key  = None
        self.following = LWWSet()
        self.followers = LWWSet()

    def get_payload(self):
        assert self.user_key, "Can not generate a payload without a user_key"
        return {
            "user_key": self.user_key,
            "following": self.following.payload,
            "followers": self.followers.payload,
        }

    def set_payload(self, payload):
       self.following = LWWSet.from_payload(payload['following'])
       self.followers = LWWSet.from_payload(payload['followers'])

       self.user_key  = payload['user_key']

    payload = property(get_payload, set_payload)

    @property
    def value(self):
        return {
            "user_key": self.user_key,
            "following": self.following.value,
            "followers": self.followers.value,
            }
    
    @classmethod
    def merge(cls, X, Y):
        assert X.user_key == Y.user_key, "User keys do not match"
        assert X.user_key is not None, "user_key must be set"

        following = LWWSet.merge(X.following, Y.following)
        followers = LWWSet.merge(X.following, Y.following)

        new = cls()
        new.user_key = X.user_key
        new.following = following
        new.followers = followers
        
        return new

    #
    # Friendship API
    # 
    def follow(self, friend):
        self.following.add(friend.user_key)
        friend.followers.add(self.user_key)

    def unfollow(self, friend):
        self.following.discard(friend.user_key)
        friend.followers.discard(self.user_key)
