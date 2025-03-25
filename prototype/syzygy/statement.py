class Statement(object):
    pass

class PointStatement(Statement):
    # Expects a position expression, and can accept several other universal property expressions
    def __init__(self, pos, vel=None, acc=None, m=None, e=None):
        self.pos = pos
        self.vel = vel
        self.acc = acc
        self.m = m
        self.e = e

    def toString(self): # yeahhh try not to think about it it's just a logic tree to cover 16 possibilities :(
        if self.vel is not None:
            if self.acc is not None:
                if self.m is not None:
                    if self.e is not None:
                        return f"Pos: {self.pos.toString()} Vel: {self.vel.toString()} Acc: {self.acc.toString()} M: {self.m.toString()}, E: {self.e.toString()}"
                    else: return f"Pos: {self.pos.toString()} Vel: {self.vel.toString()} Acc: {self.acc.toString()} M: {self.m.toString()}, E: None"
                elif self.e is not None:
                    return f"Pos: {self.pos.toString()} Vel: {self.vel.toString()} Acc: {self.acc.toString()} M: None, E: {self.e.toString()}"
                else:
                    return f"Pos: {self.pos.toString()} Vel: {self.vel.toString()} Acc: {self.acc.toString()} M: None, E: None"
            elif self.m is not None:
                if self.e is not None:
                        return f"Pos: {self.pos.toString()} Vel: {self.vel.toString()} Acc: None M: {self.m.toString()}, E: {self.e.toString()}"
                else: return f"Pos: {self.pos.toString()} Vel: {self.vel.toString()} Acc: None M: {self.m.toString()}, E: None"
            elif self.e is not None:
                    return f"Pos: {self.pos.toString()} Vel: {self.vel.toString()} Acc: None M: None, E: {self.e.toString()}"
            else:
                    return f"Pos: {self.pos.toString()} Vel: {self.vel.toString()} Acc: None M: None, E: None"
        elif self.acc is not None:
            if self.m is not None:
                if self.e is not None:
                        return f"Pos: {self.pos.toString()} Vel: None Acc: {self.acc.toString()} M: {self.m.toString()}, E: {self.e.toString()}"
                else: return f"Pos: {self.pos.toString()} Vel: None Acc: {self.acc.toString()} M: {self.m.toString()}, E: None"
            elif self.e is not None:
                    return f"Pos: {self.pos.toString()} Vel: None Acc: {self.acc.toString()} M: None, E: {self.e.toString()}"
            else:
                    return f"Pos: {self.pos.toString()} Vel: None Acc: {self.acc.toString()} M: None, E: None"
        elif self.m is not None:
            if self.e is not None:
                        return f"Pos: {self.pos.toString()} Vel: None Acc: None M: {self.m.toString()}, E: {self.e.toString()}"
            else: return f"Pos: {self.pos.toString()} Vel: None Acc: None M: {self.m.toString()}, E: None"
        elif self.e is not None:
                    return f"Pos: {self.pos.toString()} Vel: None Acc: None M: None, E: {self.e.toString()}"
        else:
            return f"Pos: {self.pos.toString()} Vel: None Acc: None M: None, E: None"

class ForceStatement(Statement):
    # Expects two object expressions (particles, particle groups) and a function expression
    def __init__(self, objA, objB, func):
        self.objA = objA
        self.objB = objB
        self.func = func

    def toString(self):
        return f"ObjA: {self.objA.toString()} ObjB: {self.objB.toString()} Func: {self.func.toString()}"

class UpdateStatement(Statement):
    # Not sure what to expect right now
    def __init__(self):
        pass