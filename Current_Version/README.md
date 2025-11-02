# 🖱️ Smart Cursor Control - Modular Version

A refactored, modular computer vision system for hands-free cursor control using your webcam.

## ✨ What's New in This Version

- **🔧 Modular Architecture**: Large files broken down into focused, maintainable modules
- **📦 Easy to Edit**: Each component has a single responsibility
- **🚀 Simplified Launch**: Single launcher with dependency checking
- **🧹 Clean Structure**: Removed duplicates and unnecessary files

## 📁 Project Structure

```
Current_Version/
├── Core/
│   ├── modules/           # Modular components
│   │   ├── settings_manager.py      # Settings loading/saving
│   │   ├── gui_components.py        # User interface
│   │   ├── cursor_control.py        # Cursor movement & clicking
│   │   ├── gesture_recognition.py   # Hand gesture detection
│   │   ├── tracking_engines.py      # Various tracking methods
│   │   ├── performance_optimizer.py # GPU acceleration & optimization
│   │   └── main_application.py      # Application coordinator
│   └── __pycache__/        # Python cache files
├── Config/                 # Configuration files
├── Docs/                   # Documentation
├── launch.py              # Main launcher with dependency checks
├── START.bat             # Windows launcher
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## 🚀 Quick Start

### For Windows Users:
1. Double-click `START.bat`
2. Follow the on-screen instructions

### For All Platforms:
1. Install dependencies: `pip install -r requirements.txt`
2. Run: `python launch.py`

## 🎮 How to Use

1. **Launch the application** using the launcher
2. **Choose a tracking mode** from the GUI:
   - 👆 **Finger Tracking**: Precise index finger control (recommended)
   - 👁️ **Eye Tracking**: Eye gaze control
   - 🎯 **Gaming**: Optimized for fast movement
   - ⌨️ **Typing**: Head tracking for accessibility

3. **Adjust settings** with the sliders:
   - **Dwell Time**: How long to hold cursor to click
   - **Sensitivity**: Tracking responsiveness
   - **Smoothing**: Cursor movement smoothness

4. **Use gestures** for clicking:
   - 🤏 **Pinch**: Left click
   - ✊ **Fist**: Right click
   - ✌️ **Peace**: Double click

5. **Press 'Q'** in the camera window to quit

## 🛠️ Development

### Adding New Features

Each module has a specific responsibility:

- **Settings**: Modify `settings_manager.py`
- **GUI**: Update `gui_components.py`
- **Cursor Logic**: Edit `cursor_control.py`
- **Gestures**: Enhance `gesture_recognition.py`
- **Tracking**: Add to `tracking_engines.py`
- **Performance**: Optimize in `performance_optimizer.py`

### Testing Changes

1. Run: `python launch.py`
2. Test your changes
3. Check logs in `smart_cursor.log`

## 🔧 Configuration

Settings are automatically saved to `cursor_settings.json`:

```json
{
  "dwell_time": 2.0,
  "tracking_sensitivity": 0.8,
  "smoothing": 0.7,
  "gesture_recognition": true,
  "voice_feedback": false
}
```

## 🐛 Troubleshooting

### Application won't start:
- Check `smart_cursor.log` for error messages
- Ensure your webcam is working
- Try reinstalling dependencies: `pip install -r requirements.txt`

### Cursor not moving:
- Check camera permissions
- Ensure good lighting
- Try different tracking modes
- Adjust sensitivity settings

### Performance issues:
- Close other applications
- Enable GPU acceleration in settings
- Lower camera resolution

## 📊 System Requirements

- **Python**: 3.7+
- **Camera**: Webcam with 640x480 resolution
- **RAM**: 4GB minimum
- **OS**: Windows, macOS, or Linux

### Optional (for better performance):
- CUDA-compatible GPU
- OpenCL drivers

## 🎯 Key Features

- **Multiple Tracking Methods**: Finger, hand, eye, head, and pose tracking
- **Gesture Recognition**: Click with hand gestures
- **Dwell Clicking**: Hold cursor still to click
- **Performance Optimization**: GPU acceleration support
- **Modular Design**: Easy to extend and maintain
- **Cross-Platform**: Works on Windows, macOS, and Linux

## 📝 License

This project is open source. Feel free to modify and distribute.

---

**🎮 Ready to control your cursor with gestures? Launch and start exploring!**
