from particle import Particle 

def pos_update(p: Particle, net_force, dt):
    """
    Increments position by the change in time times the velocity.
    """
    p.set("pos", p.get("pos") + dt * p.get("vel"))
    print(p._name, " Pos: ", p.get("pos"))

def vel_update(p: Particle, net_force, dt):
    """
    Increments velocity by the change in time times the acceleration.
    """
    p.set("vel", p.get("vel") + dt * p.get("acc"))

def acc_update(p: Particle, net_force, dt):
    """
    Sets the acceleration to the net force applied divided by the mass.
    """
    p.set("acc", net_force / p.get("mass"))
    print(p._name, " Acc: ", net_force / p.get("mass"))
