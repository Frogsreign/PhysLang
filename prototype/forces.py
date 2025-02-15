import numpy as np
from particle import Particle

def f_rand(t, a: Particle, b: Particle):
    return np.random.rand()
    
def f_grav(t, a: Particle, b: Particle):
    """
    Classical gravitational pull between `a` and `b`.
    """
    TOL = 1e-5
    G = 6.67430e-11     # Gravitational constant                

    d = np.linalg.norm(b.get("pos") - a.get("pos")) 
    # Avoid unbounded acceleration. 
    if d > TOL:
        mag = G * a.get("mass") * b.get("mass") / d**2
        return mag
    else:
        return 0

def f_elec(t, a: Particle, b: Particle):
    """
    Classical electrostatic force between `a` and `b`.
    """
    TOL = 1e-5
    G = 6.67430e-11     # Gravitational constant                

    d = np.linalg.norm(b.get("pos") - a.get("pos")) 
    # Avoid unbounded acceleration. 
    if d > TOL:
        mag = G * a.get("e_charge") * b.get("e_charge") / d**2
        return mag
    else:
        return 0
