#!/usr/bin/python3

# Convert json to an array and a data map.

import numpy
import json

class OffsetMap:
    def __init__(self, particle_name_to_idx, prop_name_to_idx, prop_offsets, prop_sizes, num_particles, particle_size):
        self._particle_name_to_idx = particle_name_to_idx
        self._prop_name_to_idx = prop_name_to_idx
        self._particle_size = particle_size
        self._prop_offsets = prop_offsets
        self._prop_sizes = prop_sizes
        self._num_particles = num_particles

    def idx_of(self, particle_name, prop_name, index=0):
        particle_offset = self._particle_size * self._particle_name_to_idx[particle_name]
        prop_offset = self._prop_offsets[self._prop_name_to_idx[prop_name]]
        return particle_offset + prop_offset + index

    def prop_offset(self, prop_name) -> int:
        return self._prop_offsets[self._prop_name_to_idx[prop_name]]

    def prop_size(self, prop_name) -> int:
        return self._prop_sizes[self._prop_name_to_idx[prop_name]]

    def prop_idx_all_particles(self, prop_name):
        prop_offset = self._prop_offsets[self._prop_name_to_idx[prop_name]]
        return [particle_idx * self._particle_size + prop_offset 
                for particle_idx in range(self.num_particles())]

    def sim_dim(self) -> int:
        return self.prop_size("pos")

    def num_particles(self) -> int:
        return self._num_particles

    def particle_size(self):
        return self._particle_size

    def sim_size(self):
        return self.particle_size() * self.num_particles()


def create_offset_map(particles_list):
    """
    A builder function for the OffsetMap class. Builds an OffsetMap 
    from a simulation json path.

    Args:
        particles_list (list): A list of dicts, each representing a 
        particle.

    Returns:
        OffsetMap: an OffsetMap object whose particles and properties 
        are those of `particles_list`.
    """
    num_particles = len(particles_list)
    particle_names = get_particle_names(particles_list) # Make names unique, etc.
    prop_names = get_prop_names(particles_list)
    # Invert prop, particle lists.
    particle_name_to_idx = list_inverse(particle_names)
    prop_name_to_idx = list_inverse(prop_names)
    # Get sizes and offsets.
    prop_sizes = get_prop_sizes(particles_list, prop_name_to_idx)
    prop_offsets, particle_size_without_net_force = get_prop_offsets(prop_sizes)
    # Add `net-force` property. Update prop_sizes, prop_offsets, 
    # prop_names and prop_to_idx
    net_force_idx = len(prop_names)
    pos_size = get_pos_size(prop_name_to_idx, prop_sizes) 
    prop_name_to_idx["net-force"] = net_force_idx
    prop_names.append("net-force")
    prop_sizes.append(pos_size)
    prop_offsets.append(particle_size_without_net_force)
    particle_size = particle_size_without_net_force + pos_size
    # Sort properties alphabetically (TODO).
    # Create the offset map.
    offset_map = OffsetMap(
            particle_name_to_idx, 
            prop_name_to_idx, 
            prop_offsets, 
            prop_sizes, 
            num_particles,
            particle_size)
    return offset_map
    

def get_pos_size(prop_name_to_idx, prop_sizes) -> int:
    """
    Output the size of the `pos` property.
    """
    # size of pos?
    if "pos" not in prop_name_to_idx:
        raise RuntimeError("particles must have a \"pos\" property")
    pos_idx = prop_name_to_idx["pos"]
    return prop_sizes[pos_idx]


def read_sim_json(sim_json_path):
    reader = open(sim_json_path, "r")
    sim_json = json.JSONDecoder().decode(reader.read())
    return sim_json


def get_particle_names(particles):
    """
    Creates a list of particle names.
    """
    # TODO: Come up with a scheme for making particle names unique 
    # while preserving their original names.
    # FOR NOW: Assumes names are unique.
    particle_names = set()
    for particle in particles:
        particle_name = particle["name"]
        particle_names.add(particle_name)
    return sorted(list(particle_names))


def list_inverse(l) -> dict:
    """
    Creates a map from property names to their indices in 
    `props_list`.

    Args:
        props_list (list): A list of property names.

    Returns: 
        dict: A map from property names to indices.
    """
    return {item: idx for idx, item in enumerate(l)}


def get_prop_names(particles):
    """
    Return all properties, sorted.

    Args:
        particles (list): A list of particles represented as dict 
        instances.

    Returns:
        list: A list of all properties in this particle group, sorted 
        by name alphabetically.
    """
    props_set = set()
    for particle in particles:
        for prop_name in particle["props"].keys():
            props_set.add(prop_name)
    return sorted(list(props_set))


def check_prop_size(prop_idx, prop_val, prop_sizes):
    prop_size = 1
    # Does not check if the list is homogeneous or 1D.
    # This will be done later on.
    if isinstance(prop_val, list):
        prop_size = len(prop_val)
    # All particles in the same group must have the same sized
    # properties.
    if prop_sizes[prop_idx] != 0:
        if prop_sizes[prop_idx] != prop_size:
            raise ValueError(f"Inconsistent sizes for property"
                             f" {prop_idx}. Previously {prop_sizes[prop_idx]}, now {prop_size}")
    else:
        prop_sizes[prop_idx] = prop_size


def get_prop_sizes(particles, prop_to_idx):
    """
    Creates a list of property sizes, and ensures all instances of a 
    property are the same size.

    Args:
        particles (list): A list of particles represented as dict 
        instances.
        prop_to_idx (dict): A dict instance mapping property names to 
        indices.

    Returns:
        list: A list of property sizes.
    """
    prop_sizes = [0] * len(prop_to_idx)
    for particle in particles:
        for prop_name, prop_val in particle["props"].items():
            check_prop_size(prop_to_idx[prop_name], prop_val, 
                            prop_sizes)
    return prop_sizes


def get_prop_offsets(prop_sizes):
    """
    Creates a list of property offsets, defining a data layout for a 
    particle:

    idx(particle_idx, prop_idx) = obj_size * particle_idx + prop_idx
    
    Args:
        prop_sizes (list): A list of property sizes.

    Returns:
        list: A list of offsets from the beginning of an object's 
        memory.
        int: The size of an object.
    """
    prop_offsets = []
    obj_size = 0
    for prop_size in prop_sizes:
        prop_offsets.append(obj_size)
        obj_size += prop_size
    return prop_offsets, obj_size
