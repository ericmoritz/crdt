# CRDT toolbox

The CRDT toolbox provides a collection of basic Conflict-free
replicated data types as well as a common interface for defining your
own CRDTs

If you don't know what a CRDT is, watch
[this](http://research.microsoft.com/apps/video/dl.aspx?id=153540)

## Definitions
* CRDT - A Conflict-Free Replicated Data-Type as defined by the INRIA paper.
* Payload - A JSON serializable representation of the CRDT's internal state
* Value - The computed, usable value

## Goals

* Storage-Independence
* Standard API
* Compound CRDTs

### Storage-Independent

To accomplish storage independence, the payload is exposed publically
and as a simple JSON friendly data structures.

The public visibility of the payload allows the CRDTs to be loaded and
stored independent of how it is stored.

While there exists serialization formats that allow non-JSON friendly
structures -- such pickling a set -- targeting the lowest common
denominator of JSON allows the possibility to serialize into a large
number of formats.

### Standard API

#### base.StateCRDT API

The base.StateCRDT class defines the interface for State-based CRDTs

##### Abstract Methods/Properties

###### \_\_init\_\_(self)

Creates a new CRDT at it's initial state

##### @property payload

This is the serializable representation of the CRDT's internal state.
The data **SHOULD** be defined in simple types that can be represented
as JSON, i.e. strings, numbers, dicts and lists.
 
##### @property value
This is the computed value of the CRDT.

##### @classmethod merge(cls, X, Y)
This merges the two CRDT instances

#### Built-in Methods

##### clone(self)
Creates a new copy of the CRDT instance

##### @classmethod from_payload(cls, payload)
Create a new CRDT instance with the given payload


### Compound CRDTs
One property of CRDTs is that CRDTs made of CRDTs are automatically a
CRDT.  This enables Compound CRDTs.  Here is a sample implementation
of a friendship:

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
            assert self.user_key, \
              "Can not generate a payload without a user_key"

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

Now this object can easily be stored and retrieved

    import os
    import json
    from friendship import Friendship
    
    
    def load(user_key):
        filename = "./%s.friendship.json" % user_key
        if os.path.exists(filename):
            with open(filename) as fh:
                return Friendship.from_payload(json.load(fh))
        else:
            new = Friendship()
            new.user_key = user_key
            return new
    
    
    def store(friendship):
        filename = "./%s.friendship.json" % friendship.user_key
    
        with open(filename, "w") as fh:
            json.dump(friendship.payload, fh)
        
    
    def friend_glenn():
        eric = load("eric")
        glenn = load("glenn")
    
        eric.follow(glenn)
    
        store(eric)
        store(glenn)
    
    friend_glenn()
    
    eric = load("eric")
    
    print "Is eric following glenn?", "glenn" in eric.following

## References
* [Conﬂict-free Replicated Data Types](http://hal.inria.fr/docs/00/60/93/99/PDF/RR-7687.pdf)
* [A comprehensive study of Convergent and Commutative Replicated Data Types](http://hal.archives-ouvertes.fr/docs/00/55/55/88/PDF/techreport.pdf)
* [Marc Shapiro's talk @ Microsoft](http://research.microsoft.com/apps/video/dl.aspx?id=153540)
* [Logoot](https://gforge.inria.fr/docman/view.php/1646/6393/weiss09.pdf) - CRDT for a distributed peer-to-peer Document editing
