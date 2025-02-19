import numpy as np
from particle import Particle

def f_rand(a: Particle, b: Particle) -> float:
    "Random force between `a` and `b`"
    return np.random.rand()
    
def f_grav(a: Particle, b: Particle) -> float:
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

def f_elec(a: Particle, b: Particle) -> float:
    """
    Classical electrostatic force between `a` and `b`.
    """
    TOL = 1e-5
    ke = 8.99e9     # Gravitational constant                

    d = np.linalg.norm(b.get("pos") - a.get("pos")) 
    # Avoid unbounded acceleration. 
    if d > TOL:
        mag = ke * a.get("e_charge") * b.get("e_charge") / d**2
        return mag
    else:
        return 0
