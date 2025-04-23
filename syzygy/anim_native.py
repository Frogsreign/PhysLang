# See https://matplotlib.org/stable/api/animation_api.html for info on 
# matplotlib's animation scheme.


# FOR TESTING PURPOSES
# An version of the simulation class that uses matplotlib's default backend.

from syzygy.sim.sim_state import SimState

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation
import matplotlib.axes


# Next steps:
#   This should all take place in a `simulation` class with a `state` attribute,
#   and attributes for all of the various simulation parameters. This will make 
#   it possible to pause, resume, load and save states, etc.

class Simulation:
    def __init__(self, dt, steps_per_update, state: SimState):
        self._fig = plt.figure()
        self._ax = self._fig.add_subplot(projection='3d')
        self._dt = dt
        self._steps_per_update = steps_per_update
        self._state = state
        self._paused = False
        # Configure event handlers (this will eventually be done in its own function).
        self._fig.canvas.mpl_connect("button_press_event", self._toggle_pause)

    def _toggle_pause(self, event):
        if self._paused:
            self._animation.resume()
        else:
            self._animation.pause()
        self._paused = not self._paused


    def config_fig(self):
        # A `matplotlib.patches.Patch` is a 2D artist with a face color and an 
        # edge color.
        self._fig.patch.set_alpha(0.0)  # Make figure background transparent

    def config_bg(self):
      # TODO Ideally this should read from a config file.
      self._ax.set_axis_off()
      plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    def config_plot_limits(self, xlim, ylim, zlim, origin=(0,0,0)):
        # Center the plot at `origin`
        self._ax.set(xlim3d=(xlim[0] + origin[0], xlim[1] + origin[0]))
        self._ax.set(ylim3d=(ylim[0] + origin[1], ylim[1] + origin[1]))
        self._ax.set(zlim3d=(zlim[0] + origin[2], zlim[1] + origin[2]))

    def create_animation(self):
        # Initialize point objects.
        num_points = self._state.data_layout.num_particles()
        points = [self._ax.plot([], [], [], 'o', markersize=8)[0] for _ in range(num_points)]

        # Function to update the animation
        def update(frame):
            self._state.step(self._dt / self._steps_per_update, frame, 
                              steps=self._steps_per_update)
            for i, data in enumerate(self._state.positions()):
                points[i].set_data_3d(np.expand_dims(data, axis=1))
            return points

        self._animation = animation.FuncAnimation(
                self._fig, 
                update, 
                frames=np.arange(0, 10000), 
                interval=50, 
                blit=True, 
                repeat=True)

    def resume_animation(self):
        self._animation.event_source.resume()

    def pause_animation(self):
        self._animation.event_source.pause()

    def save_state(self):
        state_writer = open("data/current_state.json", "w")
        state_writer.write(self._state.to_json())

    def run_animation(self):
        # To be expanded on.
        plt.show()
