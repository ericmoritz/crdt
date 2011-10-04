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

