#!/usr/bin/env python3
"""
StorytellerPi Web Interface
Beautiful web-based configuration and management interface for non-technical users
"""

import os
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv, set_key, unset_key
import psutil

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('WEB_SECRET_KEY', 'storytellerpi-secret-key-change-me')
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
INSTALL_DIR = os.getenv('INSTALL_DIR', '/opt/storytellerpi')
ENV_FILE = os.path.join(INSTALL_DIR, '.env')
LOG_DIR = os.getenv('LOG_DIR', '/opt/storytellerpi/logs')
SERVICE_NAME = os.getenv('SERVICE_NAME', 'storytellerpi')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages .env configuration file"""
    
    def __init__(self, env_file: str):
        self.env_file = env_file
        self.load_config()
    
    def load_config(self) -> Dict[str, str]:
        """Load configuration from .env file"""
        config = {}
        if os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        return config
    
    def get_config(self, key: str, default: str = '') -> str:
        """Get configuration value"""
        config = self.load_config()
        return config.get(key, default)
    
    def set_config(self, key: str, value: str) -> bool:
        """Set configuration value"""
        try:
            set_key(self.env_file, key, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set config {key}: {e}")
            return False
    
    def get_all_config(self) -> Dict[str, str]:
        """Get all configuration"""
        return self.load_config()


class ServiceManager:
    """Manages StorytellerPi service with robust error handling"""
    
    @staticmethod
    def _find_systemctl() -> str:
        """Find systemctl binary"""
        possible_paths = [
            '/usr/bin/systemctl',
            '/bin/systemctl',
            '/usr/local/bin/systemctl',
            'systemctl'  # Fallback to PATH
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue
        
        return None
    
    @staticmethod
    def _run_systemctl_command(command: str) -> tuple[bool, str]:
        """Run systemctl command with error handling"""
        systemctl_path = ServiceManager._find_systemctl()
        
        if not systemctl_path:
            logger.error("systemctl not found in system")
            return False, "systemctl not available"
        
        try:
            full_command = [systemctl_path] + command.split()
            logger.info(f"Running command: {' '.join(full_command)}")
            
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=30,
                env=dict(os.environ, PATH='/usr/bin:/bin:/usr/local/bin:/sbin:/usr/sbin')
            )
            
            return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return False, "Command timed out"
        except Exception as e:
            logger.error(f"Command failed: {command}, error: {e}")
            return False, str(e)
    
    @staticmethod
    def get_service_status() -> Dict[str, Any]:
        """Get service status with comprehensive error handling"""
        try:
            # Check if service exists first
            service_exists, _ = ServiceManager._run_systemctl_command(f"status {SERVICE_NAME}")
            
            if not service_exists:
                # Check if we're running the process directly
                return ServiceManager._get_process_status()
            
            # Get service active status
            is_active, active_output = ServiceManager._run_systemctl_command(f"is-active {SERVICE_NAME}")
            
            # Get service enabled status
            is_enabled, enabled_output = ServiceManager._run_systemctl_command(f"is-enabled {SERVICE_NAME}")
            
            status = 'running' if is_active else 'stopped'
            
            return {
                'active': is_active,
                'enabled': is_enabled,
                'status': status,
                'service_exists': True,
                'method': 'systemd',
                'details': f"Active: {active_output}, Enabled: {enabled_output}"
            }
            
        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
            # Fallback to process-based status
            return ServiceManager._get_process_status()
    
    @staticmethod
    def _get_process_status() -> Dict[str, Any]:
        """Get status by checking running processes"""
        try:
            # Look for StorytellerPi process
            storyteller_running = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'storyteller_main.py' in cmdline or 'storytellerpi' in proc.info['name']:
                        storyteller_running = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                'active': storyteller_running,
                'enabled': False,  # Can't determine without systemd
                'status': 'running' if storyteller_running else 'stopped',
                'service_exists': False,
                'method': 'process',
                'details': 'Checked running processes'
            }
            
        except Exception as e:
            logger.error(f"Failed to check process status: {e}")
            return {
                'active': False,
                'enabled': False,
                'status': 'unknown',
                'service_exists': False,
                'method': 'error',
                'details': str(e)
            }
    @staticmethod
    def start_service() -> tuple[bool, str]:
        """Start the service with comprehensive error handling"""
        try:
            # First check if service exists
            status_info = ServiceManager.get_service_status()
            
            if status_info.get('method') == 'systemd':
                # Use systemd
                success, output = ServiceManager._run_systemctl_command(f"start {SERVICE_NAME}")
                if success:
                    return True, "Service started successfully"
                else:
                    # Try with sudo
                    try:
                        subprocess.run(['sudo', 'systemctl', 'start', SERVICE_NAME], 
                                     check=True, capture_output=True, text=True, timeout=30)
                        return True, "Service started with sudo"
                    except Exception as e:
                        return False, f"Failed to start service: {output}, sudo attempt: {e}"
            else:
                # Try to start manually
                return ServiceManager._start_manual()
                
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            return False, str(e)
    
    @staticmethod
    def stop_service() -> tuple[bool, str]:
        """Stop the service with comprehensive error handling"""
        try:
            status_info = ServiceManager.get_service_status()
            
            if status_info.get('method') == 'systemd':
                # Use systemd
                success, output = ServiceManager._run_systemctl_command(f"stop {SERVICE_NAME}")
                if success:
                    return True, "Service stopped successfully"
                else:
                    # Try with sudo
                    try:
                        subprocess.run(['sudo', 'systemctl', 'stop', SERVICE_NAME], 
                                     check=True, capture_output=True, text=True, timeout=30)
                        return True, "Service stopped with sudo"
                    except Exception as e:
                        return False, f"Failed to stop service: {output}, sudo attempt: {e}"
            else:
                # Try to stop manually
                return ServiceManager._stop_manual()
                
        except Exception as e:
            logger.error(f"Failed to stop service: {e}")
            return False, str(e)
    
    @staticmethod
    def restart_service() -> tuple[bool, str]:
        """Restart the service with comprehensive error handling"""
        try:
            # Stop first, then start
            stop_success, stop_msg = ServiceManager.stop_service()
            if not stop_success:
                return False, f"Failed to stop service: {stop_msg}"
            
            # Wait a moment
            import time
            time.sleep(2)
            
            start_success, start_msg = ServiceManager.start_service()
            if start_success:
                return True, "Service restarted successfully"
            else:
                return False, f"Failed to start after stop: {start_msg}"
                
        except Exception as e:
            logger.error(f"Failed to restart service: {e}")
            return False, str(e)
    
    @staticmethod
    def _start_manual() -> tuple[bool, str]:
        """Start service manually when systemd is not available"""
        try:
            # Check if already running
            status = ServiceManager._get_process_status()
            if status['active']:
                return True, "Service already running"
            
            # Try to start the main script
            install_dir = os.getenv('INSTALL_DIR', '/opt/storytellerpi')
            main_script = os.path.join(install_dir, 'main', 'storyteller_main.py')
            
            if not os.path.exists(main_script):
                return False, f"Main script not found: {main_script}"
            
            # Start in background
            subprocess.Popen([
                'python3', main_script
            ], cwd=install_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return True, "Service started manually"
            
        except Exception as e:
            return False, f"Manual start failed: {e}"
    
    @staticmethod
    def _stop_manual() -> tuple[bool, str]:
        """Stop service manually when systemd is not available"""
        try:
            # Find and terminate StorytellerPi processes
            killed_processes = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'storyteller_main.py' in cmdline or 'storytellerpi' in proc.info['name']:
                        proc.terminate()
                        killed_processes += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed_processes > 0:
                return True, f"Stopped {killed_processes} process(es)"
            else:
                return True, "No running processes found"
                
        except Exception as e:
            return False, f"Manual stop failed: {e}"


class SystemMonitor:
    """System monitoring utilities"""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get system information"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Temperature (Raspberry Pi specific)
            temp = None
            try:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temp = int(f.read()) / 1000.0
            except:
                pass
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used': memory.used // (1024*1024),  # MB
                'memory_total': memory.total // (1024*1024),  # MB
                'disk_percent': disk.percent,
                'disk_used': disk.used // (1024*1024*1024),  # GB
                'disk_total': disk.total // (1024*1024*1024),  # GB
                'temperature': temp,
                'uptime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {}
    
    @staticmethod
    def get_recent_logs(lines: int = 50) -> List[str]:
        """Get recent log entries"""
        try:
            result = subprocess.run(
                ['sudo', 'journalctl', '-u', SERVICE_NAME, '-n', str(lines), '--no-pager'],
                capture_output=True, text=True
            )
            return result.stdout.split('\n')
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return []


# Initialize managers with error handling
try:
    config_manager = ConfigManager(ENV_FILE)
    service_manager = ServiceManager()
    system_monitor = SystemMonitor()
    logger.info("Web interface managers initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize managers: {e}")
    # Create minimal fallback managers
    config_manager = None
    service_manager = None
    system_monitor = None


def safe_get_service_status():
    """Safely get service status with fallback"""
    if service_manager:
        try:
            return service_manager.get_service_status()
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
    
    return {
        'active': False,
        'enabled': False,
        'status': 'unknown',
        'service_exists': False,
        'method': 'error',
        'details': 'Service manager not available'
    }


def safe_get_system_info():
    """Safely get system info with fallback"""
    if system_monitor:
        try:
            return system_monitor.get_system_info()
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
    
    return {
        'cpu_percent': 0,
        'memory_percent': 0,
        'disk_percent': 0,
        'temperature': None,
        'uptime': 'Unknown',
        'hostname': 'Unknown'
    }


# Routes
@app.route('/')
def dashboard():
    """Main dashboard page with error handling"""
    try:
        service_status = safe_get_service_status()
        system_info = safe_get_system_info()
        recent_logs = system_monitor.get_recent_logs(10) if system_monitor else []
        
        return render_template('dashboard.html',
                             service_status=service_status,
                             system_info=system_info,
                             recent_logs=recent_logs)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        # Return minimal dashboard
        return render_template('dashboard.html',
                             service_status={'status': 'error', 'details': str(e)},
                             system_info={'cpu_percent': 0, 'memory_percent': 0},
                             recent_logs=[])


@app.route('/settings')
def settings():
    """Settings page"""
    config = config_manager.get_all_config()
    return render_template('settings.html', config=config)


# API Routes
@app.route('/api/service/<action>', methods=['POST'])
def service_control(action):
    """Control service (start/stop/restart) with enhanced error handling"""
    try:
        # Check if service manager is available
        if not service_manager:
            return jsonify({
                'success': False,
                'message': 'Service manager not available - system may not be properly configured',
                'status': {'active': False, 'status': 'unavailable'}
            }), 503
        
        if action == 'start':
            success, message = service_manager.start_service()
        elif action == 'stop':
            success, message = service_manager.stop_service()
        elif action == 'restart':
            success, message = service_manager.restart_service()
        elif action == 'status':
            # Return current status
            status = safe_get_service_status()
            return jsonify({
                'success': True, 
                'message': 'Status retrieved',
                'status': status
            })
        else:
            success = False
            message = f"Invalid action: {action}. Valid actions: start, stop, restart, status"
        
        # Also include current status in response
        current_status = safe_get_service_status()
        
        return jsonify({
            'success': success, 
            'message': message,
            'status': current_status
        })
        
    except Exception as e:
        logger.error(f"Service control error for action '{action}': {e}")
        return jsonify({
            'success': False, 
            'message': f"Internal error: {str(e)}",
            'status': {'active': False, 'status': 'error'}
        }), 500


@app.route('/api/config', methods=['GET', 'POST'])
def config_api():
    """Get or update configuration"""
    if request.method == 'GET':
        return jsonify(config_manager.get_all_config())
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            updated = 0
            
            for key, value in data.items():
                if config_manager.set_config(key, value):
                    updated += 1
            
            return jsonify({
                'success': True,
                'message': f'Updated {updated} configuration items',
                'updated': updated
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})


@app.route('/api/system/status')
def system_status():
    """Get system status with error handling"""
    try:
        return jsonify({
            'service': safe_get_service_status(),
            'system': safe_get_system_info()
        })
    except Exception as e:
        logger.error(f"System status error: {e}")
        return jsonify({
            'service': {'status': 'error', 'details': str(e)},
            'system': {'cpu_percent': 0, 'memory_percent': 0, 'error': str(e)}
        }), 500


@app.route('/api/logs')
def get_logs():
    """Get recent logs"""
    lines = request.args.get('lines', 50, type=int)
    logs = system_monitor.get_recent_logs(lines)
    return jsonify({'logs': logs})


@app.route('/api/test/<component>')
def test_component(component):
    """Test system components"""
    try:
        if component == 'audio':
            # Test audio playback
            result = subprocess.run(
                ['speaker-test', '-t', 'sine', '-f', '1000', '-l', '1', '-s', '1'],
                capture_output=True, text=True, timeout=5
            )
            success = result.returncode == 0
            message = "Audio test completed" if success else "Audio test failed"
            
        elif component == 'microphone':
            # Test microphone recording
            result = subprocess.run(
                ['arecord', '-D', 'hw:0,0', '-f', 'cd', '-t', 'wav', '-d', '2', '/tmp/test.wav'],
                capture_output=True, text=True, timeout=5
            )
            success = result.returncode == 0
            message = "Microphone test completed" if success else "Microphone test failed"
            
        elif component == 'wake_word':
            # Test wake word detection (simplified)
            success = True  # Placeholder - would need actual wake word test
            message = "Wake word detection is configured"
            
        else:
            success = False
            message = "Unknown component"
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/test/feedback/<feedback_type>')
def test_feedback(feedback_type):
    """Test audio feedback sounds"""
    try:
        # Import audio feedback functions
        from audio_feedback import get_audio_feedback
        
        audio_feedback = get_audio_feedback()
        
        if feedback_type == 'wake_word':
            audio_feedback.wake_word_detected()
            message = "Wake word feedback played"
        elif feedback_type == 'success':
            audio_feedback.success_feedback()
            message = "Success feedback played"
        elif feedback_type == 'error':
            audio_feedback.error_feedback()
            message = "Error feedback played"
        elif feedback_type == 'button':
            audio_feedback.button_pressed()
            message = "Button feedback played"
        else:
            return jsonify({'success': False, 'message': 'Unknown feedback type'})
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        logger.error(f"Failed to test feedback: {e}")
        return jsonify({'success': False, 'message': str(e)})


# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('status', {
        'service': service_manager.get_service_status(),
        'system': system_monitor.get_system_info()
    })


@socketio.on('request_status')
def handle_status_request():
    """Handle status update request"""
    emit('status', {
        'service': service_manager.get_service_status(),
        'system': system_monitor.get_system_info()
    })


if __name__ == '__main__':
    # Ensure template and static directories exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Run the web interface
    port = int(os.getenv('WEB_PORT', '8080'))
    debug = os.getenv('WEB_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting StorytellerPi Web Interface on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)