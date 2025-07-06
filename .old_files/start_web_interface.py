#!/usr/bin/env python3
"""
StorytellerPi Web Interface Startup Script
Starts the web interface with proper error handling and diagnostics
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

def setup_logging():
    """Setup logging"""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'web_interface.log')),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def check_prerequisites():
    """Check system prerequisites"""
    logger = logging.getLogger(__name__)
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ required")
        return False
    
    # Check required files
    required_files = [
        'main/web_interface.py',
        '.env'
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            logger.error(f"Required file missing: {file_path}")
            return False
    
    # Check required packages
    required_packages = ['flask', 'flask_socketio', 'psutil', 'python-dotenv']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'flask_socketio':
                __import__('flask_socketio')
            elif package == 'python-dotenv':
                __import__('dotenv')
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("Run: pip install " + " ".join(missing_packages))
        return False
    
    return True

def create_env_if_missing():
    """Create .env file if missing"""
    logger = logging.getLogger(__name__)
    env_file = '.env'
    
    if not os.path.exists(env_file):
        logger.info("Creating default .env file")
        
        default_env = """# StorytellerPi Environment Configuration
INSTALL_DIR=/opt/storytellerpi
SERVICE_NAME=storytellerpi
LOG_DIR=/opt/storytellerpi/logs
WEB_SECRET_KEY=storytellerpi-secret-key-change-me
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_DEBUG=false
"""
        
        try:
            with open(env_file, 'w') as f:
                f.write(default_env)
            logger.info(f"Created {env_file}")
        except Exception as e:
            logger.error(f"Failed to create {env_file}: {e}")
            return False
    
    return True

def start_web_interface():
    """Start the web interface"""
    logger = logging.getLogger(__name__)
    
    # Add main directory to Python path
    main_dir = os.path.join(os.path.dirname(__file__), 'main')
    sys.path.insert(0, main_dir)
    
    try:
        # Import and start the web interface
        from web_interface import app, socketio
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Get configuration
        host = os.getenv('WEB_HOST', '0.0.0.0')
        port = int(os.getenv('WEB_PORT', 5000))
        debug = os.getenv('WEB_DEBUG', 'false').lower() == 'true'
        
        logger.info(f"Starting web interface on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        
        # Start the server
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        logger.info("Web interface stopped by user")
    except Exception as e:
        logger.error(f"Failed to start web interface: {e}")
        raise

def main():
    """Main function"""
    logger = setup_logging()
    logger.info("Starting StorytellerPi Web Interface")
    
    try:
        # Check prerequisites
        if not check_prerequisites():
            logger.error("Prerequisites check failed")
            return 1
        
        # Create .env if missing
        if not create_env_if_missing():
            logger.error("Failed to create .env file")
            return 1
        
        # Start web interface
        start_web_interface()
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())