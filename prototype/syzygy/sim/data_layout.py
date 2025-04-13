#!/usr/bin/python3
#
# @author Jacob Leider
#
#
# A helper class for the SimState class. DataLayout maps properties to indices 
# in a global data array.


import numpy
import json


class DataLayout:
    def __init__(self, particles_list):
      self.particle_metadata = ParticleMetadata(particles_list)


    def idx_of(self, particle_name=None, prop_name=None, index=0):
      idx = 0
      if particle_name is not None:
        particle_idx = self.particle_metadata.particle_name_to_idx[particle_name]
        idx += self.particle_size() * particle_idx
      if prop_name is not None:
        idx += self.prop_offset(prop_name)
      idx += index
      return idx


    def assign_list(self, particle_name, prop_name, prop_data, data):
      for prop_idx, prop_val in enumerate(prop_data):
        data[self.idx_of(particle_name, prop_name, prop_idx)] = prop_val


    def assign_element(self, particle_name, prop_name, prop_data, data):
      data[self.idx_of(particle_name, prop_name)] = prop_data


    def init_data(self, data, particles):
        """
        Fill empty data buffer with particle data.
        """
        for particle in particles:
          particle_name = particle["name"]
          particle_data = particle["props"]
          for prop_name, prop_data in particle_data.items():
            prop_size = self.prop_size(prop_name)
            if prop_size == 1:
              self.assign_element(particle_name, prop_name, prop_data, data)
            elif prop_size > 1:
              self.assign_list(particle_name, prop_name, prop_data, data)


    def idx_as_str(self, particle_id="A", prop_name="pos", index=0):
        idx = self.prop_offset(prop_name) + index
        return f"{idx} + {particle_id} * {self.particle_size()}"


    def prop_offset(self, prop: str | int) -> int:
        return self.particle_metadata.prop_offset(prop)


    def prop_size(self, prop: str | int) -> int:
        return self.particle_metadata.prop_size(prop)


    def prop_idx_all_particles(self, prop_name):
        """The list of all indices in the data array corresponding to the 
        property `prop_name`"""
        prop_offset = self.prop_offset(prop_name)
        out = numpy.array([
            range(i * self.particle_size() + prop_offset, 
                  i * self.particle_size() + prop_offset + 3) 
            for i in range(self.num_particles())])
        return out


    def num_particles(self) -> int:
        """Number of particles in the simulation"""
        return self.particle_metadata.num_particles


    def particle_size(self):
        """Number of words per particle. The size of a word depends on the type 
        of data array passed to init_data."""
        return self.particle_metadata.particle_size


    def sim_dim(self) -> int:
        return self.prop_size("pos")


    def sim_size(self):
        return self.particle_size() * self.num_particles()


class ParticleMetadata:
    def __init__(self, particles_list):
        self.num_particles = len(particles_list)
        self.particle_names = get_particle_names(particles_list) # Make names unique, etc.
        self.prop_names = get_prop_names(particles_list)
        # Invert prop, particle lists.
        self.particle_name_to_idx = list_inverse(self.particle_names)
        self.prop_name_to_idx = list_inverse(self.prop_names)
        # Get sizes and offsets.
        self.prop_sizes = get_prop_sizes(particles_list, self.prop_name_to_idx)
        self.prop_offsets, particle_size_without_net_force = get_prop_offsets(self.prop_sizes)
        # Add `net-force` property. Update prop_sizes, prop_offsets, 
        # prop_names and prop_to_idx
        net_force_idx = len(self.prop_names)
        pos_size = get_pos_size(self.prop_name_to_idx, self.prop_sizes) 
        self.prop_name_to_idx["net-force"] = net_force_idx
        self.prop_names.append("net-force")
        self.prop_sizes.append(pos_size)
        #for i, name in enumerate(self.prop_names): print(f"\t{i}) {name}: {self.prop_sizes[self.prop_name_to_idx[name]]}")
        self.prop_offsets.append(particle_size_without_net_force)
        self.particle_size = particle_size_without_net_force + pos_size


    def prop_size(self, prop: int | str):
        if isinstance(prop, int):
            return self.prop_sizes[prop]
        elif isinstance(prop, str):
            return self.prop_sizes[self.prop_name_to_idx[prop]]


    def prop_offset(self, prop: int | str):
        if isinstance(prop, int):
            return self.prop_offsets[prop]
        elif isinstance(prop, str):
            return self.prop_offsets[self.prop_name_to_idx[prop]]


def create_data_layout(particles_list):
    """
    A builder function for the DataLayout class. Builds an DataLayout 
    from a simulation json path.

    Args:
        particles_list (list): A list of dicts, each representing a 
        particle.

    Returns:
        DataLayout: an DataLayout object whose particles and properties 
        are those of `particles_list`.
    """
    return NotImplemented
    

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
    particle_names = {}
    unique_particle_names = []
    for particle in particles:
        particle_name = particle["name"]
        if particle_name in particle_names:
            ct = particle_names[particle_name]
            particle_name += f"-{ct}"
            particle_names[particle_name] += 1
        else:
            particle_names[particle_name] = 1

        unique_particle_names.append(particle_name)
    return sorted(unique_particle_names)


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
