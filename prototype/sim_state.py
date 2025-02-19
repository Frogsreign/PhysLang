import json
import numpy as np
from particle import Particle

# JSON Standards:
#   https://datatracker.ietf.org/doc/html/rfc7159.html
#   https://ecma-international.org/publications-and-standards/standards/ecma-404/

class SimState:
    def __init__(self, particles: list[Particle]) -> None:
        self._particles = particles

    def positions(self):
        """
        Return a list of positions where the index corresponds to the 
        particle's ID.

        Returns
            An iterable of numpy.ndarrays.
        """
        for particle in self._particles:
            yield particle.get("pos")

    def _step(self, dt, t, steps=1):
        """
        Iterate the state of the simulation.

        Args
            dt: Time elapsed between steps.
            t: Time since the start of the simulation.
            steps: Number of times to iterate the simulation state.
        """
        if not isinstance(steps, int):
            raise ValueError("`steps` must be an int")

        # Step `steps` times.
        for _ in range(steps):
            # Step once.
            for i in range(len(self._particles)):
                # Compute net force between each particle pair.
                df = np.zeros((3,))
                for j in range(len(self._particles)):
                    if j == i:
                        continue
                    df += self._particles[i].net_force_from(self._particles[j], t)

                self._particles[i].update_props(df, dt)

    def to_json(self) -> str: 
        """
        Output a serialized representation of the simulation state.
        """
        obj_list = [p._dict() for p in self._particles]
        return json.JSONEncoder().encode({"particles": obj_list})
