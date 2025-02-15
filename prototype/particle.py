
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

    _forces_global: dict[str, Callable] = {}
    _update_rules_global: dict[str, Callable] = {}
    _props_global: list = []

    @classmethod
    def add_prop_global(cls, prop_name: str):
        """
        Merely adds the name to a list that will always be checked during 
        simulation.
        """
        cls._props_global.append(prop_name)

    @classmethod
    def add_force_global(cls, force_name: str, force_func: Callable):
        cls._forces_global[force_name] = force_func

    @classmethod
    def add_update_rule_global(cls, update_rule_name: str, update_rule_func: Callable):
        cls._update_rules_global[update_rule_name] = update_rule_func

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
        self._props_local["pos"] = np.array([0,0,0])
        self._props_local["vel"] = np.array([0,0,0])
        self._props_local["acc"] = np.array([0,0,0])

    def net_force_from(self, other, t):
        """
        Calculate net force vector induced by `other`. 
        """
        net_force = 0
        # Forces applying to all instances
        for _, force in self._forces_global.items():
            try:
                net_force += force(t, self, other)
            except KeyError: # Throw errors unrelated to missing properties.
                pass
        # Forces applying only to this instance
        for _, force in self._forces_local.items():
            try:
                net_force += force(t, self, other)
            except KeyError: # Throw errors unrelated to missing properties.
                pass

        unit_vec = (other.get("pos") - self.get("pos")) / np.linalg.norm(other.get("pos") - self.get("pos"))
        return net_force * unit_vec

    def update_props(self, net_force, dt):
        for _, rule in self._update_rules_global.items():
            try:
                rule(self, net_force, dt)
            except KeyError: # Throw errors unrelated to missing properties.
                pass

    def add_force_local(self, force_name: str, force_func: Callable):
        self._forces_local[force_name] = force_func

    def add_update_rule_local(self, update_rule_name: str, update_rule_func: Callable):
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

