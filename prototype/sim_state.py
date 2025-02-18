import json
from particle import Particle

# JSON Standards:
#   https://datatracker.ietf.org/doc/html/rfc7159.html
#   https://ecma-international.org/publications-and-standards/standards/ecma-404/

class SimState:
    def __init__(self, particles: list[Particle]) -> None:
        self._particles = particles

    def to_json(self) -> str:
        obj_list = [p._dict() for p in self._particles]
        par_json = Particle._cls_dict()
        return json.JSONEncoder().encode({"global": par_json, "particles": obj_list})
