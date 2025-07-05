#!/usr/bin/env python3
"""
Lightweight StorytellerPi Web Interface for Pi Zero 2W
Minimal RAM footprint with lazy loading of full interface
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize lightweight Flask app
app = Flask(__name__)
app.secret_key = os.getenv('WEB_SECRET_KEY', 'storytellerpi-lite-key')

# Configuration
INSTALL_DIR = os.getenv('INSTALL_DIR', '/opt/storytellerpi')
ENV_FILE = os.path.join(INSTALL_DIR, '.env')
SERVICE_NAME = 'storytellerpi'

# Setup minimal logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global flag for full interface loading
_full_interface_loaded = False
_full_app_instance = None


class LiteConfigManager:
    """Minimal configuration manager for lite interface"""
    
    def __init__(self, env_file: str):
        self.env_file = env_file
    
    def get_basic_config(self) -> Dict[str, str]:
        """Get basic configuration for lite interface"""
        config = {
            'wake_word_framework': os.getenv('WAKE_WORD_FRAMEWORK', 'porcupine'),
            'wake_word_threshold': os.getenv('WAKE_WORD_THRESHOLD', '0.5'),
            'target_response_time': os.getenv('TARGET_RESPONSE_TIME', '11.0'),
            'max_memory_usage': os.getenv('MAX_MEMORY_USAGE', '400'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO')
        }
        return config
    
    def update_config(self, key: str, value: str) -> bool:
        """Update a single configuration value"""
        try:
            # Read current .env file
            lines = []
            if os.path.exists(self.env_file):
                with open(self.env_file, 'r') as f:
                    lines = f.readlines()
            
            # Update or add the key
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f'{key}='):
                    lines[i] = f'{key}={value}\n'
                    updated = True
                    break
            
            if not updated:
                lines.append(f'{key}={value}\n')
            
            # Write back to file
            with open(self.env_file, 'w') as f:
                f.writelines(lines)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            return False


# Initialize lite config manager
lite_config = LiteConfigManager(ENV_FILE)


def get_service_status() -> Dict[str, Any]:
    """Get basic service status without heavy system calls"""
    try:
        import subprocess
        result = subprocess.run(
            ['systemctl', 'is-active', SERVICE_NAME],
            capture_output=True, text=True, timeout=5
        )
        active = result.stdout.strip() == 'active'
        
        result = subprocess.run(
            ['systemctl', 'is-enabled', SERVICE_NAME],
            capture_output=True, text=True, timeout=5
        )
        enabled = result.stdout.strip() == 'enabled'
        
        return {
            'active': active,
            'enabled': enabled,
            'status': 'running' if active else 'stopped'
        }
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        return {'active': False, 'enabled': False, 'status': 'unknown'}


def load_full_interface():
    """Lazy load the full web interface when needed"""
    global _full_interface_loaded, _full_app_instance
    
    if _full_interface_loaded:
        return _full_app_instance
    
    try:
        logger.info("Loading full web interface...")
        
        # Import the full web interface module
        from web_interface import app as full_app
        from web_interface import config_manager, service_manager, system_monitor
        
        _full_app_instance = {
            'app': full_app,
            'config_manager': config_manager,
            'service_manager': service_manager,
            'system_monitor': system_monitor
        }
        
        _full_interface_loaded = True
        logger.info("Full web interface loaded successfully")
        
        return _full_app_instance
        
    except Exception as e:
        logger.error(f"Failed to load full interface: {e}")
        return None


# Lite Interface Routes
@app.route('/')
def lite_dashboard():
    """Minimal dashboard with load full interface button"""
    service_status = get_service_status()
    config = lite_config.get_basic_config()
    
    return render_template('lite_dashboard.html',
                         service_status=service_status,
                         config=config)


@app.route('/load-full-interface')
def load_full_interface_route():
    """Load and redirect to full interface"""
    full_interface = load_full_interface()
    
    if full_interface:
        # Redirect to full interface
        return redirect('/full-dashboard')
    else:
        return jsonify({'error': 'Failed to load full interface'}), 500


@app.route('/full-dashboard')
def full_dashboard():
    """Full dashboard - only available after loading"""
    if not _full_interface_loaded:
        return redirect(url_for('lite_dashboard'))
    
    # Use the full interface
    full_interface = _full_app_instance
    service_status = full_interface['service_manager'].get_service_status()
    system_info = full_interface['system_monitor'].get_system_info()
    recent_logs = full_interface['system_monitor'].get_recent_logs(10)
    
    return render_template('dashboard.html',
                         service_status=service_status,
                         system_info=system_info,
                         recent_logs=recent_logs)


@app.route('/api/service/<action>', methods=['POST'])
def control_service(action):
    """Control service with minimal overhead"""
    try:
        import subprocess
        
        if action == 'start':
            subprocess.run(['sudo', 'systemctl', 'start', SERVICE_NAME], check=True, timeout=10)
        elif action == 'stop':
            subprocess.run(['sudo', 'systemctl', 'stop', SERVICE_NAME], check=True, timeout=10)
        elif action == 'restart':
            subprocess.run(['sudo', 'systemctl', 'restart', SERVICE_NAME], check=True, timeout=10)
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        return jsonify({'success': True})
        
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Service command timed out'}), 500
    except Exception as e:
        logger.error(f"Service control error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Handle basic configuration"""
    if request.method == 'GET':
        config = lite_config.get_basic_config()
        return jsonify(config)
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            for key, value in data.items():
                if not lite_config.update_config(key, value):
                    return jsonify({'error': f'Failed to update {key}'}), 500
            
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"Config update error: {e}")
            return jsonify({'error': str(e)}), 500


@app.route('/api/status')
def get_status():
    """Get basic system status"""
    try:
        import psutil
        
        # Get basic system info without heavy operations
        status = {
            'service': get_service_status(),
            'memory_percent': psutil.virtual_memory().percent,
            'cpu_percent': psutil.cpu_percent(interval=None),  # Non-blocking
            'uptime': os.popen('uptime -p').read().strip()
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/memory-usage')
def get_memory_usage():
    """Get current memory usage"""
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        
        return jsonify({
            'total': memory.total // (1024*1024),  # MB
            'used': memory.used // (1024*1024),   # MB
            'percent': memory.percent,
            'available': memory.available // (1024*1024)  # MB
        })
        
    except Exception as e:
        logger.error(f"Memory usage error: {e}")
        return jsonify({'error': str(e)}), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('lite_error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('lite_error.html', 
                         error_code=500, 
                         error_message="Internal server error"), 500


if __name__ == '__main__':
    # Run in development mode
    app.run(host='0.0.0.0', port=5000, debug=False)