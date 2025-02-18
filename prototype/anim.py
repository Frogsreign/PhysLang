# See https://matplotlib.org/stable/api/animation_api.html for info on 
# matplotlib's animation scheme.

from sim_state import SimState

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
        self._paused = True 
        # Configure event handlers (this will eventually be done in its own function).
        self._fig.canvas.mpl_connect("button_press_event", self._toggle_pause)

    def _toggle_pause(self):
        if self._paused:
            self._animation.resume()
        else:
            self._animation.pause()
        self._paused = not self._paused

    def _step(self, t):
        for i in range(len(self._state._particles)):
            # Compute net force between each particle pair.
            df = np.zeros((3,))
            for j in range(len(self._state._particles)):
                if j == i:
                    continue
                df += self._state._particles[i].net_force_from(self._state._particles[j], t)

            self._state._particles[i].update_props(df, self._dt / self._steps_per_update)

    # Outputted update.
    def _update_pos(self, t):
        for _ in range(self._steps_per_update):
            # Inner update.
            self._step(t)
        for particle in self._state._particles:
            yield particle.get("pos")

    def config_fig(self):
        # A `matplotlib.patches.Patch` is a 2D artist with a face color and an 
        # edge color.
        self._fig.patch.set_alpha(0.0)  # Make figure background transparent

    def config_bg(self):
      # TODO Ideally this should read from a config file.
      self._ax.set_axis_off()
      plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
      # Remove ticks.
      # self._ax.set_xticks([])
      # self._ax.set_yticks([])
      # self._ax.set_zticks([])
      # Remove labels.
      # self._ax.set_xlabel('')
      # self._ax.set_ylabel('')
      # self._ax.set_zlabel('')
      # self._ax.grid(False)
      # Make background transparent.
      # self._ax.set_facecolor((1.0, 1.0, 1.0, 0.0))
      # self._fig.patch.set_facecolor((1.0, 1.0, 1.0, 1.0))
      # Hide 3D panes.
      # self._ax.xaxis.pane.fill = False
      # self._ax.yaxis.pane.fill = False
      # self._ax.zaxis.pane.fill = False
      # Set matplotlib.patches.Polygon (pane) edge colors.
      # self._ax.xaxis.pane.set_edgecolor((1.0, 1.0, 1.0, 0.0))
      # self._ax.yaxis.pane.set_edgecolor((1.0, 1.0, 1.0, 0.0))
      # self._ax.zaxis.pane.set_edgecolor((1.0, 1.0, 1.0, 0.0))
      # Hide axis lines.
      # self._ax.xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
      # self._ax.yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
      # self._ax.zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))


    def config_plot_limits(self, xlim, ylim, zlim, origin=(0,0,0)):
        # Center the plot at `origin`
        self._ax.set(xlim3d=(xlim[0] + origin[0], xlim[1] + origin[0]))
        self._ax.set(ylim3d=(ylim[0] + origin[1], ylim[1] + origin[1]))
        self._ax.set(zlim3d=(zlim[0] + origin[2], zlim[1] + origin[2]))


    def create_animation(self):
        # Initialize point objects.
        particles = self._state._particles
        num_points = len(particles)
        points = [self._ax.plot([], [], [], 'o', markersize=8)[0] for _ in range(num_points)]

        # Function to update the animation
        def update(frame):
            for i, data in enumerate(self._update_pos(frame)):
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

    def _save_state(self):
        state_writer = open("data/current_state.json", "w")
        state_writer.write(self._state.to_json())

    def run_animation(self):
        # To be expanded on.
        plt.show()
