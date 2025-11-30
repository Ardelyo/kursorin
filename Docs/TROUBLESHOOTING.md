# 🔧 Troubleshooting Guide - Smart Cursor Stable

## 🚨 Common Issues & Solutions

### ❌ "Installation Failed" or "Dependencies Missing"

**Symptoms:**
- Launcher shows red error messages
- "Missing dependencies" in status

**Solutions:**
1. **Check Internet Connection** - Required for downloading packages
2. **Run as Administrator** - Right-click batch file → "Run as administrator"
3. **Manual Installation:**
   ```bash
   pip install opencv-python mediapipe pyautogui Pillow numpy mss pywin32
   ```
4. **Alternative Mirror:**
   ```bash
   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple opencv-python mediapipe pyautogui Pillow numpy mss pywin32
   ```

### 🖱️ "Can't Use Mouse" or "Mouse Not Moving"

**Symptoms:**
- Camera works but cursor doesn't move
- "Mouse: DISABLED" in GUI

**Solutions:**
1. **Enable Mouse Control** - Check the "Enable" checkbox in GUI
2. **Check Permissions** - Run as administrator
3. **Disable Antivirus** - Sometimes blocks mouse control
4. **Test Demo Mode** - Use "Run Demo Mode" to check camera

### 📹 "Camera Not Working"

**Symptoms:**
- "Cannot open webcam" error
- Black camera window

**Solutions:**
1. **Check Camera Access:**
   - Close other camera apps (Zoom, Skype, etc.)
   - Grant camera permissions in Windows Settings
   - Test camera in Windows Camera app

2. **Try Different Camera:**
   - External webcam if built-in fails
   - Check Device Manager for camera status

3. **Camera Settings:**
   - Good lighting required
   - Face/hands should fill frame
   - Clean camera lens

### 🐌 "System is Slow" or "Low FPS"

**Symptoms:**
- Laggy cursor movement
- Low FPS in status display

**Solutions:**
1. **Close Other Programs** - Free up CPU/memory
2. **Lower Camera Resolution:**
   ```python
   # In smart_cursor_stable.py, change:
   self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
   self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
   self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
   ```
3. **Disable Advanced Features** - Uncheck adaptive speed, gesture recognition

### 🚫 "Application Crashes" or "Errors"

**Symptoms:**
- System closes unexpectedly
- Error messages in console/logs

**Solutions:**
1. **Check Logs:**
   - `smart_cursor_stable.log`
   - `launcher_stable.log`

2. **Run Demo First:**
   - Use "Run Demo Mode" to test basic functionality
   - If demo works, issue is with advanced features

3. **Safe Mode:**
   - Disable voice feedback, adaptive features
   - Use basic hand tracking only

## 🔍 Diagnostic Steps

### Step 1: Test Demo Mode
1. Open launcher
2. Click "Run Demo Mode"
3. If this works → Camera is OK, issue with main system
4. If this fails → Camera/driver issue

### Step 2: Check Dependencies
1. Open Command Prompt
2. Run: `python -c "import cv2, mediapipe, pyautogui; print('OK')"`
3. If error → Missing dependencies
4. If OK → Dependencies are fine

### Step 3: Test Mouse Control
1. Run: `python -c "import pyautogui; pyautogui.moveTo(100, 100); print('Mouse OK')"`
2. If error → PyAutoGUI/permission issue
3. If OK → Mouse control should work

## 🛠️ Advanced Fixes

### Reset Settings
```bash
# Delete settings file to reset to defaults
del cursor_settings_stable.json
```

### Force Reinstall Dependencies
```bash
pip uninstall opencv-python mediapipe pyautogui Pillow numpy mss pywin32 -y
pip install opencv-python mediapipe pyautogui Pillow numpy mss pywin32
```

### Windows-Specific Fixes
1. **Update Windows** - Check for Windows updates
2. **Update Drivers** - Camera and display drivers
3. **Disable UAC** - Temporarily for testing
4. **Run in Compatibility Mode** - Windows 8/7 compatibility

## 📞 Getting Help

If issues persist:

1. **Collect Information:**
   - Error messages
   - Log files
   - System specs (Windows version, Python version)

2. **Try Safe Mode:**
   - Use demo mode only
   - Basic hand tracking
   - Mouse control disabled initially

3. **Community Help:**
   - Check GitHub issues
   - Post on forums with logs

## ✅ Success Checklist

- [ ] Camera opens without errors
- [ ] Demo mode shows video feed
- [ ] GUI launches successfully
- [ ] Mouse control can be enabled
- [ ] Cursor moves when hand is detected
- [ ] Clicking works (dwell or gesture)

**If all checkmarks are ✅ → System is working correctly!**

---

*Remember: Start with demo mode to verify camera works, then progress to full system.*
