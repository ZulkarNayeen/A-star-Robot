import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button, Slider, RadioButtons
from matplotlib.patches import FancyBboxPatch
import matplotlib.colors as mcolors


from astar_logic import astar

# --- CONFIGURATION ---
GRID_SIZE = 100      # Map resolution
ROBOT_SPEED = 2      # Robot movement speed (Nodes per frame). Higher = Faster.
EXPLORE_SPEED = 25   # Exploration visualization speed (Nodes per frame).

class MazeApp:
    def __init__(self):
        self.grid_size = GRID_SIZE
        self.grid = np.zeros((self.grid_size, self.grid_size))
        self.start = (2, 2)
        self.goal = (self.grid_size - 3, self.grid_size - 3)
        self.brush_radius = 0
        self.mode = 'Draw' 
        self.ani = None
        self.draw_val = 1 
        self.drawing = False
        
        # --- UI Color Palette ---
        self.c_primary = '#11144C'   
        self.c_secondary = '#EDEEF7' 
        self.c_text_on_pri = 'white'
        self.c_text_on_sec = '#11144C'
        self.c_hover_pri = '#2a2d65'
        self.c_hover_sec = '#dce0f0'
        self.c_alert = '#D32F2F' 

        self.button_data = {} 

        # Setup Figure
        self.fig, self.ax = plt.subplots(figsize=(10, 10), facecolor=self.c_secondary)
        plt.subplots_adjust(bottom=0.25, left=0.25) 
        
        # Draw Map
        self.img = self.ax.imshow(self.grid, cmap='binary', origin='lower', vmin=0, vmax=1)
        self.set_title("Draw Maze (Click to Draw/Erase)")
        self.ax.axis('off')

        # Start/Goal Markers 
        self.marker_start, = self.ax.plot(self.start[1], self.start[0], 'go', markersize=10, label='Start')
        self.marker_goal, = self.ax.plot(self.goal[1], self.goal[0], 'ro', markersize=10, label='Goal')

        # Dynamic Elements
        self.scatter_explore = self.ax.scatter([], [], c='#3498db', s=10, alpha=0.6)
        self.line_path, = self.ax.plot([], [], color='#e74c3c', linewidth=3, alpha=0.8)
        self.robot_marker, = self.ax.plot([], [], 'bo', markersize=12, markeredgecolor='white', markeredgewidth=1.5)

        # --- UI WIDGETS ---
        
        # 1. Mode Selection
        ax_radio = plt.axes([0.02, 0.45, 0.18, 0.20], facecolor=self.c_secondary)
        self.radio = RadioButtons(ax_radio, ('Draw', 'Start', 'Goal'), activecolor=self.c_primary)
        
        for patch in ax_radio.patches:
            patch.set_radius(0.12)
        for label in self.radio.labels: 
            label.set_color(self.c_text_on_sec)
            label.set_fontsize(11)
            label.set_fontweight('bold')
        for spine in ax_radio.spines.values(): spine.set_visible(False)
        self.radio.on_clicked(self.change_mode)

        # 2. Slider
        ax_slider = plt.axes([0.35, 0.16, 0.5, 0.03], facecolor=self.c_secondary)
        self.s_brush = Slider(ax_slider, 'Brush Size  ', 1, 5, valinit=1, valstep=1, color=self.c_primary)
        self.s_brush.label.set_color(self.c_text_on_sec)
        self.s_brush.valtext.set_color(self.c_text_on_sec)
        for spine in ax_slider.spines.values(): spine.set_visible(False)
        self.s_brush.on_changed(self.update_brush_size)

        # 3. Buttons helper
        def setup_rounded_button(rect, text, is_primary, callback):
            ax_btn = plt.axes(rect, frameon=False)
            base_color = self.c_primary if is_primary else self.c_secondary
            hover_color = self.c_hover_pri if is_primary else self.c_hover_sec
            text_color = self.c_text_on_pri if is_primary else self.c_text_on_sec
            
            patch = FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.15",
                                   fc=base_color, ec=self.c_primary, lw=2,
                                   transform=ax_btn.transAxes, zorder=1)
            ax_btn.add_patch(patch)
            
            btn = Button(ax_btn, text, color='none', hovercolor='none')
            btn.label.set_color(text_color)
            btn.label.set_weight('bold')
            btn.on_clicked(callback)
            
            self.button_data[ax_btn] = {'patch': patch, 'base': base_color, 'hover': hover_color}
            return btn

        self.b_solve = setup_rounded_button([0.25, 0.05, 0.2, 0.07], 'SOLVE & RUN', True, self.solve)
        self.b_clear = setup_rounded_button([0.5, 0.05, 0.2, 0.07], 'Clear Path', False, self.clear_solution)
        self.b_reset = setup_rounded_button([0.75, 0.05, 0.2, 0.07], 'Reset Map', False, self.reset_map)

        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('motion_notify_event', self.handle_button_hover)

        plt.show()

    def set_title(self, text, color=None):
        if color is None: color = self.c_text_on_sec
        self.ax.set_title(text, color=color, fontsize=14, fontweight='bold')

    def change_mode(self, label):
        self.mode = label

    def handle_button_hover(self, event):
        needs_redraw = False
        for ax_btn, data in self.button_data.items():
            patch = data['patch']
            current_fc = mcolors.to_rgba(patch.get_facecolor())
            target_base = mcolors.to_rgba(data['base'])
            target_hover = mcolors.to_rgba(data['hover'])

            if event.inaxes == ax_btn:
                if current_fc != target_hover:
                    patch.set_facecolor(data['hover'])
                    needs_redraw = True
            else:
                if current_fc != target_base:
                    patch.set_facecolor(data['base'])
                    needs_redraw = True
        if needs_redraw: self.fig.canvas.draw_idle()

    def update_brush_size(self, val):
        self.brush_radius = int(val) - 1

    def apply_brush(self, event):
        if event.inaxes != self.ax: return
        cx, cy = int(event.xdata + 0.5), int(event.ydata + 0.5)
        if not (0 <= cx < self.grid_size and 0 <= cy < self.grid_size): return

        r = self.brush_radius
        x_min, x_max = max(0, cx - r), min(self.grid_size, cx + r + 1)
        y_min, y_max = max(0, cy - r), min(self.grid_size, cy + r + 1)
        
        self.grid[y_min:y_max, x_min:x_max] = self.draw_val
        self.grid[self.start] = 0
        self.grid[self.goal] = 0
        self.img.set_data(self.grid)
        self.fig.canvas.draw_idle()

    def on_press(self, event):
        if event.inaxes != self.ax: return
        cx, cy = int(event.xdata + 0.5), int(event.ydata + 0.5)
        if not (0 <= cx < self.grid_size and 0 <= cy < self.grid_size): return

        if self.mode == 'Draw':
            self.drawing = True
            current_val = self.grid[cy, cx]
            self.draw_val = 0 if current_val == 1 else 1
            self.apply_brush(event)
            self.set_title("Draw Maze (Click to Draw/Erase)")
        elif self.mode == 'Start':
            self.start = (cy, cx)
            self.marker_start.set_data([cx], [cy])
            self.grid[self.start] = 0
            self.set_title("Start Position Updated")
            self.fig.canvas.draw_idle()
        elif self.mode == 'Goal':
            self.goal = (cy, cx)
            self.marker_goal.set_data([cx], [cy])
            self.grid[self.goal] = 0
            self.set_title("Goal Position Updated")
            self.fig.canvas.draw_idle()

    def on_release(self, event):
        self.drawing = False

    def on_motion(self, event):
        if self.drawing and self.mode == 'Draw': self.apply_brush(event)

    def clear_solution(self, event):
        if self.ani and self.ani.event_source: self.ani.event_source.stop()
        self.scatter_explore.set_offsets(np.empty((0, 2)))
        self.line_path.set_data([], [])
        self.robot_marker.set_data([], [])
        self.set_title("Draw Maze (Click to Draw/Erase)")
        self.fig.canvas.draw_idle()

    def reset_map(self, event):
        self.clear_solution(event)
        self.grid = np.zeros((self.grid_size, self.grid_size))
        self.img.set_data(self.grid)
        self.fig.canvas.draw_idle()

    def solve(self, event):
        self.clear_solution(event)
        self.set_title(f"Solving...", color=self.c_text_on_sec)
        self.fig.canvas.draw_idle()
        
        # Call the imported logic
        path, explored = astar(self.grid, self.start, self.goal)
        
        if not path:
            self.set_title("NO PATH FOUND!", color=self.c_alert)
            if explored:
                pts = np.array([[n[1], n[0]] for n in explored])
                self.scatter_explore.set_offsets(pts)
            self.fig.canvas.draw_idle()
            return

        self.set_title("Path Found! Animating...")

        # --- ANIMATION LOGIC ---
        steps_per_frame_explore = max(1, len(explored) // EXPLORE_SPEED)
        frames_explore = (len(explored) // steps_per_frame_explore) + 5
        
        frames_robot = (len(path) // ROBOT_SPEED) + 10
        total_frames = frames_explore + frames_robot

        def animate(i):
            if i < frames_explore:
                explore_idx = min(i * steps_per_frame_explore, len(explored))
                if explore_idx > 0:
                    pts = np.array([[n[1], n[0]] for n in explored[:explore_idx]])
                    self.scatter_explore.set_offsets(pts)
            else:
                px, py = zip(*[(n[1], n[0]) for n in path])
                self.line_path.set_data(px, py)
                
                robot_frame = i - frames_explore
                path_idx = min(robot_frame * ROBOT_SPEED, len(path) - 1)
                
                if path_idx >= 0:
                    cur_pos = path[path_idx]
                    self.robot_marker.set_data([cur_pos[1]], [cur_pos[0]])

            return self.scatter_explore, self.line_path, self.robot_marker

        self.ani = animation.FuncAnimation(self.fig, animate, frames=total_frames, interval=20, blit=True, repeat=False)
        self.fig.canvas.draw_idle()

if __name__ == "__main__":
    MazeApp()
