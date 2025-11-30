"""
GUI Components Module
User interface components for the Smart Cursor Control system
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
from typing import Dict, Callable, Any


class ControlPanel:
    """Main control panel GUI for the Smart Cursor system"""

    def __init__(self, settings_manager, tracking_manager, on_mode_change: Callable = None, on_setting_change: Callable = None):
        self.settings_manager = settings_manager
        self.on_mode_change = on_mode_change
        self.on_setting_change = on_setting_change
        self.tracking_manager = tracking_manager

        self.gui = None
        self.status_labels = {}
        self.mode_buttons = {}
        self.current_mode = "normal"

        # Setting controls
        self.dwell_time_var = None
        self.tracking_sensitivity_var = None
        self.stabilizer_alpha_var = None

    def create_control_panel(self):
        """Create the main GUI control panel"""
        self.gui = tk.Tk()
        self.gui.title("Smart Cursor Control - Modular Version")
        self.gui.geometry("600x500")
        self.gui.configure(bg='#f0f0f0')

        # Make window always on top initially
        self.gui.attributes('-topmost', True)
        self.gui.after(1000, lambda: self.gui.attributes('-topmost', False))

        # Title
        title_label = ttk.Label(self.gui, text="🖱️ Smart Cursor Control",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)

        subtitle_label = ttk.Label(self.gui,
                                  text="Modular Version with Advanced Tracking & Gestures",
                                  font=('Arial', 10))
        subtitle_label.pack(pady=(0, 20))

        # Status section
        self._create_status_section()

        # Control buttons section
        self._create_control_section()

        # Settings section
        self._create_settings_section()

        # Action buttons
        self._create_action_buttons()

        return self.gui

    def _create_status_section(self):
        """Create the system status display section"""
        status_frame = ttk.LabelFrame(self.gui, text="System Status", padding="10")
        status_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        self.status_labels = {}
        status_items = [
            ("Mode", "normal"),
            ("Detection", "Initializing"),
            ("FPS", "0"),
            ("Mouse", "Enabled")
        ]

        for label_text, default_value in status_items:
            frame = ttk.Frame(status_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"{label_text}:").pack(side=tk.LEFT)
            self.status_labels[label_text] = ttk.Label(frame, text=default_value)
            self.status_labels[label_text].pack(side=tk.RIGHT)

    def _create_control_section(self):
        """Create the mode control buttons section"""
        control_frame = ttk.LabelFrame(self.gui, text="Mode Control", padding="10")
        control_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Mode buttons
        modes = [
            ("👆 Finger Tracking", "normal"),
            ("👁️ Eye Tracking", "eye_tracking"),
            ("🎯 Gaming", "gaming"),
            ("⌨️ Typing", "typing")
        ]

        button_frame = ttk.Frame(control_frame)
        button_frame.pack()

        self.mode_buttons = {}
        for i, (text, mode) in enumerate(modes):
            btn = ttk.Button(button_frame, text=text,
                           command=lambda m=mode: self.set_mode(m))
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky=(tk.W, tk.E))
            self.mode_buttons[mode] = btn

    def _create_settings_section(self):
        """Create the quick settings section"""
        settings_frame = ttk.LabelFrame(self.gui, text="Quick Settings", padding="10")
        settings_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Dwell time slider
        dwell_frame = ttk.Frame(settings_frame)
        dwell_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dwell_frame, text="Dwell Time:").pack(side=tk.LEFT)
        self.dwell_time_var = tk.DoubleVar(value=self.settings_manager.get('dwell_time'))
        dwell_scale = ttk.Scale(dwell_frame, from_=0.5, to=3.0,
                               variable=self.dwell_time_var,
                               command=self._on_dwell_time_change)
        dwell_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        ttk.Label(dwell_frame, textvariable=self.dwell_time_var).pack(side=tk.RIGHT, padx=(5, 0))

        # Tracking sensitivity
        sensitivity_frame = ttk.Frame(settings_frame)
        sensitivity_frame.pack(fill=tk.X, pady=5)
        ttk.Label(sensitivity_frame, text="Sensitivity:").pack(side=tk.LEFT)
        self.tracking_sensitivity_var = tk.DoubleVar(value=self.settings_manager.get('tracking_sensitivity'))
        sensitivity_scale = ttk.Scale(sensitivity_frame, from_=0.1, to=1.0,
                                     variable=self.tracking_sensitivity_var,
                                     command=self._on_sensitivity_change)
        sensitivity_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        ttk.Label(sensitivity_frame, textvariable=self.tracking_sensitivity_var).pack(side=tk.RIGHT, padx=(5, 0))

        # Stabilizer alpha
        stabilizer_frame = ttk.Frame(settings_frame)
        stabilizer_frame.pack(fill=tk.X, pady=5)
        ttk.Label(stabilizer_frame, text="Smoothing:").pack(side=tk.LEFT)
        self.stabilizer_alpha_var = tk.DoubleVar(value=self.settings_manager.get('stabilizer_alpha'))
        stabilizer_scale = ttk.Scale(stabilizer_frame, from_=0.1, to=1.0,
                                    variable=self.stabilizer_alpha_var,
                                    command=self._on_stabilizer_change)
        stabilizer_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        ttk.Label(stabilizer_frame, textvariable=self.stabilizer_alpha_var).pack(side=tk.RIGHT, padx=(5, 0))

    def _create_action_buttons(self):
        """Create action buttons section"""
        action_frame = ttk.Frame(self.gui)
        action_frame.pack(fill=tk.X, padx=20, pady=10)

        # Left side buttons
        left_frame = ttk.Frame(action_frame)
        left_frame.pack(side=tk.LEFT)

        ttk.Button(left_frame, text="🔧 System Info",
                  command=self.show_system_info).pack(side=tk.LEFT, padx=(0, 5))

        # Right side buttons
        right_frame = ttk.Frame(action_frame)
        right_frame.pack(side=tk.RIGHT)

        ttk.Button(right_frame, text="⏹️ Stop System",
                  command=self.stop_system).pack(side=tk.RIGHT)

        ttk.Button(right_frame, text="🎯 Calibrate",
                  command=self.start_calibration).pack(side=tk.RIGHT, padx=(0, 5))

    def update_status_display(self, status_updates: Dict[str, str]):
        """Update status display labels"""
        for key, value in status_updates.items():
            if key in self.status_labels:
                self.status_labels[key].config(text=value)

    def set_mode(self, mode: str):
        """Set the current mode and update button highlighting"""
        self.current_mode = mode

        # Update button styles
        for mode_name, button in self.mode_buttons.items():
            if mode_name == mode:
                button.config(style='Accent.TButton')
            else:
                button.config(style='TButton')

        if self.on_mode_change:
            self.on_mode_change(mode)

    def _on_dwell_time_change(self, value):
        """Handle dwell time slider change"""
        self.settings_manager.set('dwell_time', float(value))
        if self.on_setting_change:
            self.on_setting_change('dwell_time', float(value))

    def _on_sensitivity_change(self, value):
        """Handle sensitivity slider change"""
        self.settings_manager.set('tracking_sensitivity', float(value))
        if self.on_setting_change:
            self.on_setting_change('tracking_sensitivity', float(value))

    def _on_stabilizer_change(self, value):
        """Handle stabilizer alpha slider change"""
        self.settings_manager.set('stabilizer_alpha', float(value))
        if self.on_setting_change:
            self.on_setting_change('stabilizer_alpha', float(value))

    def show_system_info(self):
        """Show system information dialog"""
        info_window = tk.Toplevel(self.gui)
        info_window.title("System Information")
        info_window.geometry("400x300")

        text_area = scrolledtext.ScrolledText(info_window, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add system info
        info_text = f"""Smart Cursor Control - Modular Version

Settings:
- Dwell Time: {self.settings_manager.get('dwell_time')}s
- Sensitivity: {self.settings_manager.get('tracking_sensitivity')}
- Smoothing: {self.settings_manager.get('stabilizer_alpha')}
- Mode: {self.current_mode}

Performance:
- GPU Acceleration: {self.settings_manager.get('gpu_acceleration')}
- Voice Feedback: {self.settings_manager.get('voice_feedback')}
- Sound Feedback: {self.settings_manager.get('sound_feedback')}

For more detailed information, check the logs and documentation.
"""
        text_area.insert(tk.END, info_text)
        text_area.config(state=tk.DISABLED)

    def start_calibration(self):
        """Start calibration process"""
        if self.current_mode != "eye_tracking":
            if messagebox.askyesno("Switch Mode", "Calibration requires Eye Tracking mode. Switch now?"):
                self.set_mode("eye_tracking")
            else:
                return

        calibration_window = CalibrationWindow(self.gui, self.settings_manager, self.tracking_manager)
        calibration_window.start()


class CalibrationWindow:
    """Full-screen calibration window for eye tracking"""

    def __init__(self, parent, settings_manager, tracking_manager):
        self.parent = parent
        self.settings_manager = settings_manager
        self.tracking_manager = tracking_manager
        self.window = tk.Toplevel(parent)
        self.window.title("Eye Tracking Calibration")
        self.window.attributes('-fullscreen', True)
        self.window.configure(bg='black')
        
        # Calibration points (normalized coordinates)
        self.points = [
            (0.1, 0.1), (0.5, 0.1), (0.9, 0.1),
            (0.1, 0.5), (0.5, 0.5), (0.9, 0.5),
            (0.1, 0.9), (0.5, 0.9), (0.9, 0.9)
        ]
        self.current_point_idx = 0
        self.calibration_data = []
        
        # UI Elements
        self.canvas = tk.Canvas(self.window, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.instruction_label = tk.Label(self.window, 
                                         text="Look at the red circle until it turns green",
                                         font=('Arial', 24), fg='white', bg='black')
        self.instruction_label.place(relx=0.5, rely=0.05, anchor=tk.N)
        
        # Bind escape to exit
        self.window.bind('<Escape>', lambda e: self.close())

    def start(self):
        """Begin the calibration sequence"""
        self.show_next_point()

    def show_next_point(self):
        """Display the next calibration point"""
        if self.current_point_idx >= len(self.points):
            self.finish_calibration()
            return
            
        self.canvas.delete("all")
        
        # Get current point coordinates
        nx, ny = self.points[self.current_point_idx]
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        x = int(nx * screen_width)
        y = int(ny * screen_height)
        
        # Draw point (Red initially)
        r = 20
        self.point_id = self.canvas.create_oval(x-r, y-r, x+r, y+r, fill='red', outline='white')
        
        # Simulate calibration delay (in real implementation, this would wait for stable eye detection)
        # For now, we just wait 1.5 seconds per point
        self.window.after(1000, lambda: self.record_point(x, y))

    def record_point(self, x, y):
        """Simulate recording a point (turn green then move on)"""
        self.canvas.itemconfig(self.point_id, fill='#00ff00') # Green
        
        # Capture raw gaze data
        raw_gaze = self.tracking_manager.get_raw_gaze()
        if raw_gaze:
            self.calibration_data.append({'target': (x, y), 'gaze': raw_gaze})
        else:
            # Fallback if no gaze detected (should handle this better in real app)
            logging.warning("No gaze detected during calibration point")
        
        self.current_point_idx += 1
        self.window.after(500, self.show_next_point)

    def finish_calibration(self):
        """Save data and close"""
        # Save dummy calibration data for now
        self.settings_manager.set('calibration_data', self.calibration_data)
        messagebox.showinfo("Calibration Complete", "Eye tracking calibrated successfully!")
        self.close()

    def close(self):
        """Close the calibration window"""
        self.window.destroy()

    def stop_system(self):
        """Stop the system"""
        if messagebox.askyesno("Stop System", "Are you sure you want to stop the Smart Cursor system?"):
            if self.gui:
                self.gui.quit()

    def run(self):
        """Start the GUI main loop"""
        if self.gui:
            self.gui.mainloop()
