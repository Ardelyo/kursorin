# Smart Cursor Control - Accessibility Edition

A cutting-edge cursor control system designed specifically for users with disabilities, featuring AI-powered intelligence, multiple control modes, and comprehensive accessibility features.

## ✨ Features

### 🎯 Smart Control Modes
- **Eye Tracking**: Control cursor with eye gaze for hands-free operation
- **Hand Tracking**: Precise hand gesture control with pinch-to-click
- **Web Mode**: Optimized for browsing with link detection
- **Gaming Mode**: Enhanced precision for gaming
- **Typing Mode**: Steady cursor for text input
- **Drawing Mode**: High-precision mode for creative work

### 🤖 AI Intelligence
- **Context Awareness**: Automatically detects screen content and switches modes
- **Learning System**: Learns your behavior patterns for better predictions
- **Adaptive Smoothing**: Adjusts cursor movement based on speed and context
- **Gesture Recognition**: Recognizes hand gestures for additional commands

### ♿ Accessibility Features
- **Voice Feedback**: Audio announcements for mode changes and actions
- **Sound Feedback**: Audio cues for clicks and interactions
- **Dwell Clicking**: Click by holding cursor still (customizable time)
- **High Contrast Mode**: Improved visibility for visually impaired users
- **Large Buttons**: Bigger GUI controls for easier interaction
- **Keyboard Shortcuts**: Full keyboard control (Ctrl+Shift+letter shortcuts)

### 🎮 Control Methods
- **GUI Control Panel**: User-friendly interface with all settings
- **Keyboard Shortcuts**: Quick mode switching without mouse
- **Voice Commands**: Speech recognition for hands-free control
- **Gesture Commands**: Hand gestures for clicks and actions

## 🚀 Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the System**:
   ```bash
   python smart_cursor_accessibility.py
   ```

## 🎛️ User Interface

### Main Control Panel
- **Status Display**: Real-time system information
- **Mode Buttons**: One-click mode switching
- **Settings Panel**: Accessibility options
- **Action Buttons**: Calibration, statistics, and help

### Keyboard Shortcuts
- `Ctrl+Shift+E`: Eye Tracking Mode
- `Ctrl+Shift+H`: Hand Tracking Mode
- `Ctrl+Shift+W`: Web Mode
- `Ctrl+Shift+G`: Gaming Mode
- `Ctrl+Shift+T`: Typing Mode
- `Ctrl+Shift+D`: Drawing Mode
- `Ctrl+Shift+S`: Save Settings
- `Ctrl+Shift+Q`: Quit System
- `Ctrl+Shift+C`: Start Calibration

## 🧠 How It Works

### AI Learning System
The system learns from your usage patterns to:
- Predict the best control mode for different applications
- Optimize cursor smoothing based on your movement style
- Suggest system improvements

### Context Detection
Automatically detects:
- Web browsers for browsing mode
- Code editors for typing mode
- Games for gaming mode
- General applications for normal mode

### Gesture Recognition
Recognizes:
- **Pinch**: Left click
- **Open Palm**: Right click
- **Fist**: Special actions (configurable)

## ⚙️ Configuration

Settings are automatically saved to `cursor_settings.json`:
```json
{
  "smoothing": 0.8,
  "sensitivity": 1.0,
  "dwell_time": 1.5,
  "voice_feedback": true,
  "sound_feedback": true,
  "high_contrast": false,
  "large_buttons": true,
  "gesture_recognition": true,
  "web_tracking": true,
  "adaptive_speed": true
}
```

## 🔧 Calibration

Run calibration to improve accuracy:
1. **Eye Calibration**: Look at screen corners
2. **Hand Calibration**: Move hand to camera view corners
3. **Screen Calibration**: Move cursor to screen corners

## 📊 System Requirements

- **Camera**: Webcam with at least 640x480 resolution
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **CPU**: Multi-core processor for AI processing
- **OS**: Windows 10/11, macOS, or Linux

## 🐛 Troubleshooting

### Common Issues
1. **Camera Not Detected**:
   - Check camera permissions
   - Try different camera index in code

2. **Poor Tracking**:
   - Ensure good lighting
   - Position camera at eye level
   - Run calibration

3. **Voice Not Working**:
   - Install system TTS engine
   - Check audio settings

4. **Slow Performance**:
   - Close other applications
   - Lower camera resolution
   - Disable AI features temporarily

### Logs
Check `smart_cursor_accessibility.log` for detailed error information.

## 🤝 Contributing

This system is designed to be extensible. Key areas for improvement:
- Additional gesture recognition
- More accessibility features
- Better AI algorithms
- Cross-platform support

## 📄 License

This project is open-source and designed for accessibility. Feel free to modify and distribute.

## 🆘 Support

For issues or questions:
1. Check the system logs
2. Review the help section in the GUI
3. Ensure all dependencies are installed
4. Try calibration and restart

---

**Made with ❤️ for accessibility and innovation**
