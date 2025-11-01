#!/usr/bin/env python3
"""
Advanced UI/UX Control Panel for Camera Cursor System
Phase 3 Implementation: PyQt6 Interface with Modern Design
"""

import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QSlider, QProgressBar,
                             QGroupBox, QTabWidget, QListWidget, QTextEdit, QCheckBox,
                             QMessageBox, QSystemTrayIcon, QMenu, QSpinBox, QColorDialog)
from PyQt6.QtCore import (Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve,
                          QRect, QPoint)
from PyQt6.QtGui import (QFont, QPalette, QColor, QIcon, QPixmap, QAction, QPainter,
                         QBrush, QPen, QLinearGradient)
import psutil
import time
import subprocess
import signal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

# Import our camera system components
try:
    from camera_cursor_v4 import IntelligenceEngine
except ImportError:
    IntelligenceEngine = None

class PerformanceMonitor(QThread):
    """Thread for monitoring system performance"""
    update_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.running = True
        self.process = None

    def run(self):
        while self.running:
            try:
                # Get system performance data
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                fps_data = self.get_camera_fps()

                performance_data = {
                    'cpu': cpu_percent,
                    'memory': memory.percent,
                    'fps': fps_data.get('fps', 0),
                    'detection_status': fps_data.get('detection', 'Unknown'),
                    'uptime': time.time()
                }

                self.update_signal.emit(performance_data)

            except Exception as e:
                self.update_signal.emit({'error': str(e)})

            time.sleep(2)  # Update every 2 seconds

    def get_camera_fps(self):
        """Get FPS data from camera system (placeholder)"""
        # This would be replaced with actual inter-process communication
        return {'fps': 30, 'detection': 'OK'}

    def stop(self):
        self.running = False

class ParticleEffect(QWidget):
    """Custom particle effect widget for visual feedback"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(16)  # ~60 FPS

        # Set transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def add_particle(self, x, y, color=QColor(0, 255, 0)):
        """Add a particle at position"""
        particle = {
            'x': x,
            'y': y,
            'vx': np.random.uniform(-2, 2),
            'vy': np.random.uniform(-2, 2),
            'life': 100,
            'color': color,
            'size': np.random.uniform(2, 6)
        }
        self.particles.append(particle)

    def update_particles(self):
        """Update particle positions and remove dead particles"""
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            particle['size'] *= 0.98  # Shrink over time

            if particle['life'] <= 0:
                self.particles.remove(particle)

        self.update()

    def paintEvent(self, event):
        """Draw particles"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for particle in self.particles:
            alpha = int(255 * (particle['life'] / 100))
            color = QColor(particle['color'])
            color.setAlpha(alpha)

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color, 0))
            painter.drawEllipse(
                int(particle['x'] - particle['size']/2),
                int(particle['y'] - particle['size']/2),
                int(particle['size']),
                int(particle['size'])
            )

class PerformanceChart(FigureCanvas):
    """Real-time performance chart using matplotlib"""
    def __init__(self, parent=None, width=5, height=3, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

        self.cpu_data = []
        self.memory_data = []
        self.fps_data = []
        self.time_data = []

        self.axes.set_title('System Performance')
        self.axes.set_xlabel('Time (s)')
        self.axes.set_ylabel('Usage (%)')
        self.axes.set_ylim(0, 100)
        self.axes.grid(True)

    def update_chart(self, data):
        """Update chart with new performance data"""
        current_time = time.time()

        self.cpu_data.append(data.get('cpu', 0))
        self.memory_data.append(data.get('memory', 0))
        self.fps_data.append(data.get('fps', 0))
        self.time_data.append(current_time)

        # Keep only last 50 data points
        if len(self.cpu_data) > 50:
            self.cpu_data.pop(0)
            self.memory_data.pop(0)
            self.fps_data.pop(0)
            self.time_data.pop(0)

        # Update plot
        self.axes.clear()
        self.axes.set_title('System Performance')
        self.axes.set_xlabel('Time (s)')
        self.axes.set_ylabel('Usage (%)')
        self.axes.set_ylim(0, 100)
        self.axes.grid(True)

        if self.time_data:
            times = [t - self.time_data[0] for t in self.time_data]

            self.axes.plot(times, self.cpu_data, 'r-', label='CPU %', linewidth=2)
            self.axes.plot(times, self.memory_data, 'b-', label='Memory %', linewidth=2)
            self.axes.plot(times, [f * 3.33 for f in self.fps_data], 'g-', label='FPS (scaled)', linewidth=2)  # Scale FPS for visibility

        self.axes.legend()
        self.draw()

class ThemeManager:
    """Manages application themes"""
    def __init__(self):
        self.themes = {
            'Dark': {
                'background': '#2b2b2b',
                'foreground': '#ffffff',
                'accent': '#00ff00',
                'secondary': '#555555'
            },
            'Light': {
                'background': '#ffffff',
                'foreground': '#000000',
                'accent': '#007acc',
                'secondary': '#f0f0f0'
            },
            'Blue': {
                'background': '#1e3a5f',
                'foreground': '#ffffff',
                'accent': '#00d4ff',
                'secondary': '#2d5a8c'
            },
            'Purple': {
                'background': '#2d1b3d',
                'foreground': '#ffffff',
                'accent': '#ba55d3',
                'secondary': '#4b2e5f'
            }
        }
        self.current_theme = 'Dark'

    def apply_theme(self, app, theme_name):
        """Apply theme to application"""
        if theme_name not in self.themes:
            return

        self.current_theme = theme_name
        theme = self.themes[theme_name]

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(theme['background']))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(theme['foreground']))
        palette.setColor(QPalette.ColorRole.Base, QColor(theme['secondary']))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(theme['background']))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(theme['foreground']))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(theme['foreground']))
        palette.setColor(QPalette.ColorRole.Text, QColor(theme['foreground']))
        palette.setColor(QPalette.ColorRole.Button, QColor(theme['secondary']))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme['foreground']))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(theme['accent']))

        app.setPalette(palette)

        # Save theme preference
        self.save_theme_preference(theme_name)

    def save_theme_preference(self, theme_name):
        """Save theme preference to file"""
        try:
            with open('ui_settings.json', 'w') as f:
                json.dump({'theme': theme_name}, f)
        except:
            pass

    def load_theme_preference(self):
        """Load theme preference from file"""
        try:
            with open('ui_settings.json', 'r') as f:
                data = json.load(f)
                return data.get('theme', 'Dark')
        except:
            return 'Dark'

class GestureTrainingWidget(QWidget):
    """Widget for training custom gestures"""
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Gesture list
        gesture_group = QGroupBox("Available Gestures")
        gesture_layout = QVBoxLayout()

        self.gesture_list = QListWidget()
        self.gesture_list.addItems([
            "Hand Tracking (Default)",
            "Eye Tracking",
            "Pinch to Click",
            "Fist to Drag",
            "Two Finger Scroll",
            "Palm Open Menu"
        ])
        gesture_layout.addWidget(self.gesture_list)

        # Training controls
        train_group = QGroupBox("Gesture Training")
        train_layout = QVBoxLayout()

        self.record_btn = QPushButton("🎥 Start Recording")
        self.record_btn.clicked.connect(self.start_recording)
        train_layout.addWidget(self.record_btn)

        self.save_btn = QPushButton("💾 Save Gesture")
        self.save_btn.clicked.connect(self.save_gesture)
        self.save_btn.setEnabled(False)
        train_layout.addWidget(self.save_btn)

        self.test_btn = QPushButton("🧪 Test Gesture")
        self.test_btn.clicked.connect(self.test_gesture)
        train_layout.addWidget(self.test_btn)

        train_group.setLayout(train_layout)
        gesture_group.setLayout(gesture_layout)

        layout.addWidget(gesture_group)
        layout.addWidget(train_group)
        self.setLayout(layout)

        self.recording = False
        self.gesture_data = []

    def start_recording(self):
        """Start recording a gesture"""
        if not self.recording:
            self.recording = True
            self.record_btn.setText("⏹️ Stop Recording")
            self.record_btn.setStyleSheet("background-color: red; color: white;")
            self.gesture_data = []
            self.save_btn.setEnabled(False)
        else:
            self.recording = False
            self.record_btn.setText("🎥 Start Recording")
            self.record_btn.setStyleSheet("")
            if self.gesture_data:
                self.save_btn.setEnabled(True)

    def save_gesture(self):
        """Save recorded gesture"""
        if self.gesture_data:
            gesture_name = f"Custom Gesture {len(self.gesture_data)}"
            self.gesture_list.addItem(gesture_name)
            QMessageBox.information(self, "Success", f"Gesture '{gesture_name}' saved!")
            self.gesture_data = []
            self.save_btn.setEnabled(False)

    def test_gesture(self):
        """Test gesture recognition"""
        QMessageBox.information(self, "Test", "Gesture testing would analyze recorded patterns here.")

class CameraCursorUI(QMainWindow):
    """Main UI window for Camera Cursor System control"""

    def __init__(self):
        super().__init__()
        self.camera_process = None
        self.performance_monitor = PerformanceMonitor()
        self.theme_manager = ThemeManager()
        self.intelligence_engine = IntelligenceEngine() if IntelligenceEngine else None

        self.init_ui()
        self.setup_tray_icon()
        self.load_settings()

        # Connect performance monitoring
        self.performance_monitor.update_signal.connect(self.update_performance_display)
        self.performance_monitor.start()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Camera Cursor Control Center")
        self.setGeometry(100, 100, 1000, 700)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left panel - Controls
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel, 1)

        # Right panel - Monitoring and visualization
        monitor_panel = self.create_monitor_panel()
        main_layout.addWidget(monitor_panel, 2)

        # Apply initial theme
        self.theme_manager.apply_theme(QApplication.instance(), self.theme_manager.current_theme)

    def create_control_panel(self):
        """Create the control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # System Control Group
        system_group = QGroupBox("System Control")
        system_layout = QVBoxLayout()

        # Start/Stop buttons
        self.start_btn = QPushButton("🚀 Start Camera System")
        self.start_btn.clicked.connect(self.start_camera_system)
        self.start_btn.setStyleSheet("font-size: 14px; padding: 10px;")
        system_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹️ Stop Camera System")
        self.stop_btn.clicked.connect(self.stop_camera_system)
        self.stop_btn.setEnabled(False)
        system_layout.addWidget(self.stop_btn)

        # Mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Auto (AI)", "Manual", "Browsing", "Gaming", "Typing", "Eye Tracking"])
        self.mode_combo.currentTextChanged.connect(self.change_mode)
        mode_layout.addWidget(self.mode_combo)
        system_layout.addLayout(mode_layout)

        system_group.setLayout(system_layout)
        layout.addWidget(system_group)

        # Settings Group
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()

        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(self.theme_manager.themes.keys()))
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_combo)
        settings_layout.addLayout(theme_layout)

        # Sensitivity slider
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(QLabel("Sensitivity:"))
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(1, 10)
        self.sensitivity_slider.setValue(7)
        self.sensitivity_slider.valueChanged.connect(self.change_sensitivity)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        settings_layout.addLayout(sensitivity_layout)

        # Visual effects
        effects_layout = QVBoxLayout()
        self.particle_checkbox = QCheckBox("Enable Particle Effects")
        self.particle_checkbox.setChecked(True)
        effects_layout.addWidget(self.particle_checkbox)

        self.trail_checkbox = QCheckBox("Show Cursor Trail")
        self.trail_checkbox.setChecked(True)
        effects_layout.addWidget(self.trail_checkbox)

        settings_layout.addLayout(effects_layout)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Gesture Training Tab
        gesture_group = QGroupBox("Gesture Training")
        gesture_layout = QVBoxLayout()
        self.gesture_training = GestureTrainingWidget()
        gesture_layout.addWidget(self.gesture_training)
        gesture_group.setLayout(gesture_layout)
        layout.addWidget(gesture_group)

        # AI Insights Button
        ai_btn = QPushButton("🧠 View AI Insights")
        ai_btn.clicked.connect(self.show_ai_insights)
        layout.addWidget(ai_btn)

        layout.addStretch()
        return panel

    def create_monitor_panel(self):
        """Create the monitoring panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Performance Group
        perf_group = QGroupBox("Performance Monitor")
        perf_layout = QVBoxLayout()

        # Performance bars
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        perf_layout.addWidget(QLabel("CPU Usage:"))
        perf_layout.addWidget(self.cpu_bar)

        self.memory_bar = QProgressBar()
        self.memory_bar.setRange(0, 100)
        perf_layout.addWidget(QLabel("Memory Usage:"))
        perf_layout.addWidget(self.memory_bar)

        self.fps_label = QLabel("FPS: --")
        perf_layout.addWidget(self.fps_label)

        self.detection_label = QLabel("Detection: Unknown")
        perf_layout.addWidget(self.detection_label)

        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)

        # Performance Chart
        chart_group = QGroupBox("Performance Chart")
        chart_layout = QVBoxLayout()
        self.performance_chart = PerformanceChart()
        chart_layout.addWidget(self.performance_chart)
        chart_group.setLayout(chart_layout)
        layout.addWidget(chart_group)

        # Particle Effect Demo
        effect_group = QGroupBox("Visual Effects Demo")
        effect_layout = QVBoxLayout()
        self.particle_effect = ParticleEffect()
        self.particle_effect.setMinimumHeight(200)
        self.particle_effect.mousePressEvent = self.add_demo_particle
        effect_layout.addWidget(self.particle_effect)
        effect_group.setLayout(effect_layout)
        layout.addWidget(effect_group)

        return panel

    def setup_tray_icon(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("camera_icon.png"))  # Placeholder icon

        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        hide_action = QAction("Hide to Tray", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def load_settings(self):
        """Load user settings"""
        try:
            with open('ui_settings.json', 'r') as f:
                settings = json.load(f)
                theme = settings.get('theme', 'Dark')
                self.theme_combo.setCurrentText(theme)
                self.theme_manager.apply_theme(QApplication.instance(), theme)
        except:
            pass

    def start_camera_system(self):
        """Start the camera cursor system"""
        try:
            self.camera_process = subprocess.Popen([sys.executable, 'camera_cursor_v4.py'])
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.start_btn.setText("▶️ System Running")

            # Add some demo particles
            for _ in range(10):
                self.add_demo_particle(None)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start camera system: {e}")

    def stop_camera_system(self):
        """Stop the camera cursor system"""
        if self.camera_process:
            try:
                self.camera_process.terminate()
                self.camera_process.wait(timeout=5)
            except:
                self.camera_process.kill()

            self.camera_process = None
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.start_btn.setText("🚀 Start Camera System")

    def change_mode(self, mode):
        """Change system mode"""
        # This would send signal to camera process
        QMessageBox.information(self, "Mode Changed", f"Switched to {mode} mode")

    def change_theme(self, theme):
        """Change application theme"""
        self.theme_manager.apply_theme(QApplication.instance(), theme)

    def change_sensitivity(self, value):
        """Change system sensitivity"""
        # This would adjust camera system parameters
        pass

    def update_performance_display(self, data):
        """Update performance display with new data"""
        if 'error' in data:
            self.detection_label.setText(f"Error: {data['error']}")
            return

        self.cpu_bar.setValue(int(data.get('cpu', 0)))
        self.memory_bar.setValue(int(data.get('memory', 0)))
        self.fps_label.setText(f"FPS: {data.get('fps', 0):.1f}")
        self.detection_label.setText(f"Detection: {data.get('detection', 'Unknown')}")

        # Update chart
        self.performance_chart.update_chart(data)

    def add_demo_particle(self, event):
        """Add demo particle effect"""
        if hasattr(self, 'particle_effect'):
            rect = self.particle_effect.rect()
            x = np.random.randint(0, rect.width())
            y = np.random.randint(0, rect.height())
            self.particle_effect.add_particle(x, y)

    def show_ai_insights(self):
        """Show AI insights dialog"""
        if self.intelligence_engine:
            try:
                subprocess.Popen([sys.executable, 'ai_insights.py'])
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open AI insights: {e}")
        else:
            QMessageBox.information(self, "AI Insights", "AI Engine not available. Please install required packages.")

    def closeEvent(self, event):
        """Handle window close event"""
        if self.camera_process:
            reply = QMessageBox.question(self, 'Confirm Exit',
                                        "Camera system is running. Stop it and exit?",
                                        QMessageBox.StandardButton.Yes |
                                        QMessageBox.StandardButton.No,
                                        QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                self.stop_camera_system()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def quit_application(self):
        """Quit the entire application"""
        self.stop_camera_system()
        QApplication.quit()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Camera Cursor Control Center")
    app.setApplicationVersion("4.0")
    app.setOrganizationName("AI Cursor Systems")

    # Create and show main window
    window = CameraCursorUI()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
