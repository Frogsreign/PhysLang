
import numpy as np
from collections.abc import Callable

class Particle:
    """
    Universal particle. All particles share all properties.
    """
    _forces: dict[str, Callable] = {}

    @classmethod
    def add_force(cls, force_name: str, force_func: Callable):
        cls._forces[force_name] = force_func

    def __init__(self, name=None):
        self._name = name
        self._props: dict = {}
        self._init_default()

    def _init_default(self):
        """
        By default, a particle is stationary at the origin.
        """
        self._props["pos"] = np.array([0,0,0])
        self._props["vel"] = np.array([0,0,0])
        self._props["acc"] = np.array([0,0,0])

    def net_force_from(self, other, t):
        """
        Calculate net force vector induced by `other`. 
        """
        net_force = 0
        for _, force in self._forces.items():
            net_force += force(t, self, other)

        unit_vec = (other.get("pos") - self.get("pos")) / np.linalg.norm(other.get("pos") - self.get("pos"))
        return net_force * unit_vec

    def set(self, prop_name, val):
        self._props[prop_name] = val
        
    def get(self, prop_name):
        return self._props[prop_name]

    def __str__(self):
        s = f"\"{self._name}\" ({id(self)})"
        s += "\n\tproperties:"
        for name, val in self._props.items():
            s += f"\n\t\t{name}: {val}"
        return s

