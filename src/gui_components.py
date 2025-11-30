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

    def __init__(self, settings_manager, on_mode_change: Callable = None, on_setting_change: Callable = None):
        self.settings_manager = settings_manager
        self.on_mode_change = on_mode_change
        self.on_setting_change = on_setting_change

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
        # Placeholder for calibration logic
        messagebox.showinfo("Calibration", "Calibration feature coming soon!")

    def stop_system(self):
        """Stop the system"""
        if messagebox.askyesno("Stop System", "Are you sure you want to stop the Smart Cursor system?"):
            if self.gui:
                self.gui.quit()

    def run(self):
        """Start the GUI main loop"""
        if self.gui:
            self.gui.mainloop()
