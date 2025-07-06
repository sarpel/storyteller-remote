# StorytellerPi Web Interface Fix Guide

## 🚨 **Quick Fix for HTTP 500 Errors**

The web interface is showing HTTP 500 errors because it can't find `systemctl` or manage services properly. Here's how to fix it:

### **Step 1: Run the Automatic Fix**

```bash
# Apply automatic fixes
python3 fix_web_interface.py

# Diagnose any remaining issues
python3 debug_web_interface.py
```

### **Step 2: Start the Web Interface**

```bash
# Start with the enhanced startup script
python3 start_web_interface.py
```

---

## 🔧 **Manual Fix Steps**

If the automatic fix doesn't work, follow these manual steps:

### **1. Fix systemctl Path Issues**

The error `No such file or directory: 'systemctl'` means the web interface can't find systemctl.

**Option A: Set Proper PATH**
```bash
# Find systemctl location
which systemctl
# Usually: /usr/bin/systemctl or /bin/systemctl

# Set environment variable
export PATH="/usr/bin:/bin:/usr/local/bin:/sbin:/usr/sbin:$PATH"
```

**Option B: Create Symbolic Link**
```bash
# If systemctl is in /usr/bin but web interface looks in /bin
sudo ln -s /usr/bin/systemctl /bin/systemctl
```

**Option C: Use Manual Service Management**
The web interface now includes fallback methods that don't require systemctl.

### **2. Fix Environment Variables**

Create or update `.env` file:

```bash
# Create .env file with required variables
cat > .env << EOF
INSTALL_DIR=/opt/storytellerpi
SERVICE_NAME=storytellerpi
LOG_DIR=/opt/storytellerpi/logs
WEB_SECRET_KEY=storytellerpi-secret-key-change-me
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_DEBUG=false
EOF
```

### **3. Install Missing Dependencies**

```bash
# Install required Python packages
pip3 install flask flask-socketio psutil python-dotenv

# Or install from requirements
pip3 install -r requirements.txt
```

### **4. Fix File Permissions**

```bash
# Make scripts executable
chmod +x debug_web_interface.py
chmod +x fix_web_interface.py
chmod +x start_web_interface.py
chmod +x main/web_interface.py
```

### **5. Create Missing Directories**

```bash
# Create required directories
mkdir -p logs
mkdir -p main/static
mkdir -p main/templates
```

---

## 🌐 **Starting the Web Interface**

### **Method 1: Enhanced Startup Script (Recommended)**

```bash
python3 start_web_interface.py
```

This script:
- ✅ Checks all prerequisites
- ✅ Creates missing files/directories
- ✅ Provides detailed error logging
- ✅ Handles service management gracefully

### **Method 2: Direct Flask App**

```bash
cd main
python3 web_interface.py
```

### **Method 3: With Custom Settings**

```bash
# Set custom host/port
export WEB_HOST=192.168.1.37
export WEB_PORT=5000
python3 start_web_interface.py
```

---

## 🔍 **Troubleshooting**

### **Problem: HTTP 500 on Service Start/Stop**

**Cause:** systemctl not found or insufficient permissions

**Solution:**
1. The web interface now uses fallback methods
2. Check service status with: `python3 debug_web_interface.py`
3. Service management will work in "manual" mode

### **Problem: "Service Unknown" Status**

**Cause:** Service not installed as systemd service

**Solution:**
1. The web interface will show process-based status
2. Service control buttons will start/stop the process directly
3. This is normal for development setups

### **Problem: Cannot Connect to Web Interface**

**Check these:**
```bash
# 1. Check if web interface is running
ps aux | grep web_interface

# 2. Check if port is open
netstat -an | grep :5000

# 3. Check firewall
sudo ufw status

# 4. Test local connection
curl http://localhost:5000
```

### **Problem: Service Control Buttons Don't Work**

**Solutions:**
1. Use manual mode - web interface will start/stop processes directly
2. Check logs: `tail -f logs/web_interface.log`
3. The enhanced service manager provides better error messages

---

## 📋 **Service Management Methods**

The web interface now supports multiple service management methods:

### **1. Systemd Method (Preferred)**
- Uses `systemctl` commands
- Provides auto-start capability
- Shows enabled/disabled status

### **2. Process Method (Fallback)**
- Directly manages StorytellerPi processes
- Works without systemd
- Manual start/stop only

### **3. Manual Method (Development)**
- Starts processes directly
- Good for testing and development
- No service management overhead

---

## 🎯 **Expected Behavior After Fix**

1. **Web Interface Starts:** No HTTP 500 errors on startup
2. **Service Status:** Shows current status (running/stopped/unknown)
3. **Service Control:** Start/Stop/Restart buttons work
4. **System Monitoring:** CPU, memory, disk usage displayed
5. **Error Handling:** Graceful degradation when services unavailable

---

## 🛠 **Development Mode**

For development and testing:

```bash
# Enable debug mode
export WEB_DEBUG=true
python3 start_web_interface.py

# Or edit .env file
echo "WEB_DEBUG=true" >> .env
```

Debug mode provides:
- Detailed error messages
- Auto-reload on code changes
- Enhanced logging

---

## 📁 **File Structure Check**

Ensure these files exist:

```
storyteller-remote/
├── .env                           # Environment variables
├── debug_web_interface.py         # Diagnostic tool
├── fix_web_interface.py          # Automatic fix script
├── start_web_interface.py        # Enhanced startup script
├── main/
│   ├── web_interface.py          # Main web application
│   ├── templates/
│   │   ├── base.html            # Base template
│   │   └── dashboard.html       # Dashboard page
│   └── static/                  # Static files
└── logs/                        # Log files
```

---

## 🎉 **Success Indicators**

When everything is working correctly:

1. ✅ Web interface starts without errors
2. ✅ Dashboard loads at http://YOUR_IP:5000
3. ✅ Service status shows current state
4. ✅ Control buttons respond (even if service management is manual)
5. ✅ System information displays correctly
6. ✅ No HTTP 500 errors in browser console

---

## 🆘 **Need More Help?**

If issues persist:

1. **Run Diagnostics:**
   ```bash
   python3 debug_web_interface.py > diagnostic_report.txt
   ```

2. **Check Logs:**
   ```bash
   tail -f logs/web_interface.log
   ```

3. **Test Individual Components:**
   ```bash
   # Test service manager
   python3 -c "from main.web_interface import service_manager; print(service_manager.get_service_status())"
   
   # Test system monitor  
   python3 -c "from main.web_interface import system_monitor; print(system_monitor.get_system_info())"
   ```

The web interface is now much more robust and should handle system variations gracefully!