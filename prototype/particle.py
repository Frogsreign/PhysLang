import numpy as np
from collections.abc import Callable

class Particle:
    """
    Universal particle. All particles share all properties.
    """

    # Ultimately, we'll maintain a sort of dependency graph betwen properties 
    # and forces to accomodate a sparser structure (e.g. a scenario where 
    # only a few particles have a given property in a rigid body simulation).
    #
    # The `global` vs. `local` convention will allow a user to define both a 
    # sparse force-property-dependency graph and a dense graph for universal 
    # forces/properties.
    #
    # We'll also want to allow definitions of forces between n particles for 
    # any n. This is particularly useful when n = 1, as this case allows `on 
    # earth` simulations.

    def __init__(self, name=None):
        self._name = name
        self._props_local: dict = {}
        self._forces_local: dict = {}
        self._update_rules_local: dict = {}
        self._init_default()

    def _init_default(self):
        """
        By default, a particle is stationary at the origin.
        """
        self._props_local["pos"] = np.array([0,0,0], dtype=np.float64)
        self._props_local["vel"] = np.array([0,0,0], dtype=np.float64)
        self._props_local["acc"] = np.array([0,0,0], dtype=np.float64)

    def net_force_from(self, other, t) -> float:
        """
        Calculate net force vector induced by `other`.
        """
        net_force = 0
        for _, force in self._forces_local.items():
            try:
                net_force += force(self, other)
            except KeyError: # Throw errors unrelated to missing properties.
                pass

        unit_vec = (other.get("pos") - self.get("pos")) / np.linalg.norm(other.get("pos") - self.get("pos"))
        return net_force * unit_vec

    def update_props(self, net_force, dt):
        # Rules applying only to this instance
        for _, rule in self._update_rules_local.items():
            try:
                rule(self, net_force, dt)
            except KeyError: # Throw errors unrelated to missing properties.
                pass

    def add_force(self, force_name: str, force_func: Callable):
        self._forces_local[force_name] = force_func

    def add_update_rule(self, update_rule_name: str, update_rule_func: Callable):
        self._update_rules_local[update_rule_name] = update_rule_func

    def set(self, prop_name, val):
        """
        Setter for both global and local properties.
        """
        self._props_local[prop_name] = val
        
    def get(self, prop_name):
        """
        Getter for both global and local properties.
        """
        return self._props_local[prop_name]

    def __str__(self):
        s = f"\"{self._name}\" ({id(self)})"
        s += "\n\tproperties:"
        for name, val in self._props_local.items():
            s += f"\n\t\t{name}: {val}"
        return s

    def _dict(self):
        # FIXME
        # Band-aid solution. To work with JSON, we'll need to subclass any object we want to store.
        rep = {}
        rep["name"] = self._name
        props = {}
        for name, prop in self._props_local.items():
            if isinstance(prop, np.ndarray):
                props[name] = prop.tolist()
            else:
                props[name] = prop
        rep["props"] = props

        forces = {}
        for name, force in self._forces_local.items():
            # Callable...
            forces[name] = force.__name__
        rep["forces"] = forces

        update_rules = {}
        for name, rule in self._forces_local.items():
            # Callable...
            forces[name] = rule.__name__
        rep["update_rules"] = update_rules

        return rep
    
    def __getitem__(self, item):
        return self.get(item)

    def props(self):
        return self._props_local
