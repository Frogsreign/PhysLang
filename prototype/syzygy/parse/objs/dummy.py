import numpy as np

class Thing(object): pass

class TwoThing(Thing):
    def __init__(self, obj1, obj2):
        self.obj1 = obj1
        self.obj2 = obj2

class SimpleThing(Thing):
    def __init__(self, bit):
        self.bit = bit

def read(thing):
    if isinstance(thing, SimpleThing): return readOne(thing)
    elif isinstance(thing, TwoThing): return readTwo(thing)

def readOne(thing):
    return thing.bit

def readTwo(thing):
    return np.insert((read(thing.obj2)), 0, read(thing.obj1))

thing = TwoThing(TwoThing(SimpleThing(4), SimpleThing(1)), TwoThing(SimpleThing(2), SimpleThing(3)))
print(read(thing))