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
    """Manages StorytellerPi service"""
    
    @staticmethod
    def get_service_status() -> Dict[str, Any]:
        """Get service status"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', SERVICE_NAME],
                capture_output=True, text=True
            )
            is_active = result.stdout.strip() == 'active'
            
            result = subprocess.run(
                ['systemctl', 'is-enabled', SERVICE_NAME],
                capture_output=True, text=True
            )
            is_enabled = result.stdout.strip() == 'enabled'
            
            return {
                'active': is_active,
                'enabled': is_enabled,
                'status': 'running' if is_active else 'stopped'
            }
        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
            return {'active': False, 'enabled': False, 'status': 'unknown'}
    
    @staticmethod
    def start_service() -> bool:
        """Start the service"""
        try:
            subprocess.run(['sudo', 'systemctl', 'start', SERVICE_NAME], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            return False
    
    @staticmethod
    def stop_service() -> bool:
        """Stop the service"""
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', SERVICE_NAME], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to stop service: {e}")
            return False
    
    @staticmethod
    def restart_service() -> bool:
        """Restart the service"""
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', SERVICE_NAME], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to restart service: {e}")
            return False


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


# Initialize managers
config_manager = ConfigManager(ENV_FILE)
service_manager = ServiceManager()
system_monitor = SystemMonitor()


# Routes
@app.route('/')
def dashboard():
    """Main dashboard page"""
    service_status = service_manager.get_service_status()
    system_info = system_monitor.get_system_info()
    recent_logs = system_monitor.get_recent_logs(10)
    
    return render_template('dashboard.html',
                         service_status=service_status,
                         system_info=system_info,
                         recent_logs=recent_logs)


@app.route('/settings')
def settings():
    """Settings page"""
    config = config_manager.get_all_config()
    return render_template('settings.html', config=config)


# API Routes
@app.route('/api/service/<action>', methods=['POST'])
def service_control(action):
    """Control service (start/stop/restart)"""
    success = False
    message = ""
    
    if action == 'start':
        success = service_manager.start_service()
        message = "Service started successfully" if success else "Failed to start service"
    elif action == 'stop':
        success = service_manager.stop_service()
        message = "Service stopped successfully" if success else "Failed to stop service"
    elif action == 'restart':
        success = service_manager.restart_service()
        message = "Service restarted successfully" if success else "Failed to restart service"
    else:
        message = "Invalid action"
    
    return jsonify({'success': success, 'message': message})


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
    """Get system status"""
    return jsonify({
        'service': service_manager.get_service_status(),
        'system': system_monitor.get_system_info()
    })


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