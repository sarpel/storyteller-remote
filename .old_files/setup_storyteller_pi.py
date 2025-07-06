#!/usr/bin/env python3
"""
StorytellerPi Complete Setup Script
Handles all 4 hardware/OS combinations with proper audio configuration
"""

import os
import sys
import subprocess
import logging
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List

def setup_logging():
    """Setup logging for setup process"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'setup_storyteller_pi.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def check_prerequisites() -> bool:
    """Check system prerequisites"""
    logger = logging.getLogger(__name__)
    
    # Check if running as root
    if os.geteuid() != 0:
        logger.error("This script must be run as root (use sudo)")
        return False
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ required")
        return False
    
    # Check if running on Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        
        if 'BCM' not in cpuinfo:
            logger.error("This script is designed for Raspberry Pi hardware")
            return False
    except:
        logger.error("Cannot determine hardware - not running on Raspberry Pi?")
        return False
    
    logger.info("Prerequisites check passed")
    return True

def install_base_packages() -> bool:
    """Install base system packages"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Updating package manager...")
        subprocess.run(['apt-get', 'update'], check=True)
        
        logger.info("Installing base packages...")
        base_packages = [
            'python3',
            'python3-pip',
            'python3-venv',
            'python3-dev',
            'git',
            'curl',
            'wget',
            'build-essential',
            'cmake',
            'pkg-config',
            'libasound2-dev',
            'portaudio19-dev',
            'libportaudio2',
            'libportaudiocpp0',
            'ffmpeg',
            'sox',
            'libsox-fmt-all'
        ]
        
        subprocess.run(['apt-get', 'install', '-y'] + base_packages, check=True)
        
        logger.info("Base packages installed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to install base packages: {e}")
        return False

def create_project_structure() -> bool:
    """Create project directory structure"""
    logger = logging.getLogger(__name__)
    
    try:
        install_dir = Path("/opt/storytellerpi")
        logger.info(f"Creating project structure at {install_dir}")
        
        # Create main directories
        directories = [
            install_dir,
            install_dir / "main",
            install_dir / "models",
            install_dir / "logs",
            install_dir / "credentials",
            install_dir / "tests",
            install_dir / "scripts"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        # Copy project files
        current_dir = Path(__file__).parent
        
        # Copy main files
        main_files = [
            "main/storyteller_main.py",
            "main/web_interface.py",
            "main/storyteller_llm.py",
            "main/stt_service.py",
            "main/tts_service.py",
            "main/wake_word_detector.py",
            "main/audio_feedback.py",
            "main/config_validator.py",
            "main/service_manager.py"
        ]
        
        for file_path in main_files:
            src = current_dir / file_path
            dst = install_dir / file_path
            
            if src.exists():
                shutil.copy2(src, dst)
                logger.info(f"Copied: {file_path}")
            else:
                logger.warning(f"Source file not found: {file_path}")
        
        # Copy templates and static files
        if (current_dir / "main/templates").exists():
            shutil.copytree(current_dir / "main/templates", 
                          install_dir / "main/templates", 
                          dirs_exist_ok=True)
            logger.info("Copied templates directory")
        
        if (current_dir / "main/static").exists():
            shutil.copytree(current_dir / "main/static", 
                          install_dir / "main/static", 
                          dirs_exist_ok=True)
            logger.info("Copied static files directory")
        
        # Copy model files
        if (current_dir / "models").exists():
            for model_file in (current_dir / "models").glob("*"):
                if model_file.is_file():
                    shutil.copy2(model_file, install_dir / "models")
                    logger.info(f"Copied model: {model_file.name}")
        
        # Copy test files
        if (current_dir / "tests").exists():
            for test_file in (current_dir / "tests").glob("*.py"):
                shutil.copy2(test_file, install_dir / "tests")
                logger.info(f"Copied test: {test_file.name}")
        
        # Copy requirements.txt
        if (current_dir / "requirements.txt").exists():
            shutil.copy2(current_dir / "requirements.txt", install_dir)
            logger.info("Copied requirements.txt")
        
        # Set proper permissions
        subprocess.run(['chown', '-R', 'pi:pi', str(install_dir)], check=True)
        subprocess.run(['chmod', '-R', '755', str(install_dir)], check=True)
        
        logger.info("Project structure created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create project structure: {e}")
        return False

def install_python_dependencies() -> bool:
    """Install Python dependencies"""
    logger = logging.getLogger(__name__)
    
    try:
        install_dir = Path("/opt/storytellerpi")
        requirements_file = install_dir / "requirements.txt"
        
        if not requirements_file.exists():
            logger.warning("requirements.txt not found, creating minimal requirements")
            
            minimal_requirements = """
flask==2.3.3
flask-socketio==5.3.6
python-dotenv==1.0.0
psutil==5.9.6
numpy==1.24.3
pygame==2.5.2
google-cloud-speech==2.21.0
elevenlabs==0.2.24
openai==0.28.1
anthropic==0.3.11
scipy==1.11.4
librosa==0.10.1
soundfile==0.12.1
pyaudio==0.2.11
"""
            
            with open(requirements_file, 'w') as f:
                f.write(minimal_requirements)
        
        logger.info("Installing Python dependencies...")
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
        ], check=True, cwd=str(install_dir))
        
        logger.info("Python dependencies installed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to install Python dependencies: {e}")
        return False

def run_hardware_specific_setup() -> bool:
    """Run hardware-specific audio setup"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Running hardware-specific audio setup...")
        
        # Copy the hardware setup script
        current_dir = Path(__file__).parent
        hardware_setup_script = current_dir / "setup_hardware_audio.py"
        
        if not hardware_setup_script.exists():
            logger.error("Hardware setup script not found")
            return False
        
        # Run the hardware setup script
        result = subprocess.run([
            sys.executable, str(hardware_setup_script)
        ], check=True, capture_output=True, text=True)
        
        logger.info("Hardware setup output:")
        logger.info(result.stdout)
        
        if result.stderr:
            logger.warning("Hardware setup warnings:")
            logger.warning(result.stderr)
        
        logger.info("Hardware-specific setup completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Hardware setup failed: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Failed to run hardware setup: {e}")
        return False

def create_systemd_service() -> bool:
    """Create systemd service for StorytellerPi"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Creating systemd service...")
        
        service_content = """[Unit]
Description=StorytellerPi Voice Assistant
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/opt/storytellerpi
Environment=PYTHONPATH=/opt/storytellerpi
ExecStart=/usr/bin/python3 /opt/storytellerpi/main/storyteller_main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/etc/systemd/system/storytellerpi.service")
        
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        # Reload systemd and enable service
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', 'enable', 'storytellerpi'], check=True)
        
        logger.info("Systemd service created and enabled")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create systemd service: {e}")
        return False

def create_web_interface_service() -> bool:
    """Create systemd service for web interface"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Creating web interface service...")
        
        service_content = """[Unit]
Description=StorytellerPi Web Interface
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/opt/storytellerpi
Environment=PYTHONPATH=/opt/storytellerpi
ExecStart=/usr/bin/python3 /opt/storytellerpi/main/web_interface.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/etc/systemd/system/storytellerpi-web.service")
        
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        # Reload systemd and enable service
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', 'enable', 'storytellerpi-web'], check=True)
        
        logger.info("Web interface service created and enabled")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create web interface service: {e}")
        return False

def setup_environment_variables() -> bool:
    """Setup environment variables"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Setting up environment variables...")
        
        env_file = Path("/opt/storytellerpi/.env")
        
        # Read hardware-specific config that should have been created
        env_content = {}
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_content[key.strip()] = value.strip()
        
        # Add/update base configuration
        base_config = {
            'INSTALL_DIR': '/opt/storytellerpi',
            'LOG_DIR': '/opt/storytellerpi/logs',
            'MODEL_DIR': '/opt/storytellerpi/models',
            'CREDENTIALS_DIR': '/opt/storytellerpi/credentials',
            'SERVICE_NAME': 'storytellerpi',
            'WEB_HOST': '0.0.0.0',
            'WEB_PORT': '5000',
            'WEB_DEBUG': 'false',
            'WEB_SECRET_KEY': 'storytellerpi-secret-key-change-me',
            'WAKE_WORD': 'hey elsa',
            'WAKE_WORD_SENSITIVITY': '0.7',
            'STT_SERVICE': 'google',
            'TTS_SERVICE': 'elevenlabs',
            'LLM_SERVICE': 'openai',
            'LLM_MODEL': 'gpt-3.5-turbo',
            'STORY_TEMPERATURE': '0.8',
            'STORY_MAX_TOKENS': '500',
            'STORY_SYSTEM_PROMPT': 'You are a friendly storyteller for children. Create engaging, appropriate stories.',
            'FEEDBACK_ENABLED': 'true',
            'FEEDBACK_VOLUME': '0.7',
            'LOG_LEVEL': 'INFO'
        }
        
        # Merge configurations
        env_content.update(base_config)
        
        # Write complete configuration
        with open(env_file, 'w') as f:
            f.write("# StorytellerPi Complete Environment Configuration\n")
            f.write("# Generated by setup_storyteller_pi.py\n\n")
            
            # Hardware section
            f.write("# Hardware Configuration\n")
            hardware_keys = ['HARDWARE_MODEL', 'OPERATING_SYSTEM', 'AUDIO_DEVICE', 
                           'AUDIO_ENABLED', 'AUDIO_INPUT_DEVICE', 'AUDIO_OUTPUT_DEVICE',
                           'AUDIO_DRIVER', 'AUDIO_SYSTEM']
            
            for key in hardware_keys:
                if key in env_content:
                    f.write(f"{key}={env_content[key]}\n")
            
            f.write("\n# System Configuration\n")
            system_keys = ['INSTALL_DIR', 'LOG_DIR', 'MODEL_DIR', 'CREDENTIALS_DIR', 'SERVICE_NAME']
            
            for key in system_keys:
                if key in env_content:
                    f.write(f"{key}={env_content[key]}\n")
            
            f.write("\n# Web Interface Configuration\n")
            web_keys = ['WEB_HOST', 'WEB_PORT', 'WEB_DEBUG', 'WEB_SECRET_KEY']
            
            for key in web_keys:
                if key in env_content:
                    f.write(f"{key}={env_content[key]}\n")
            
            f.write("\n# Audio Configuration\n")
            audio_keys = ['AUDIO_SAMPLE_RATE', 'AUDIO_CHANNELS', 'AUDIO_CHUNK_SIZE',
                         'AUDIO_MIXER_CONTROL', 'AUDIO_DEVICE_NAME']
            
            for key in audio_keys:
                if key in env_content:
                    f.write(f"{key}={env_content[key]}\n")
            
            f.write("\n# Service Configuration\n")
            service_keys = ['WAKE_WORD', 'WAKE_WORD_SENSITIVITY', 'STT_SERVICE', 
                           'TTS_SERVICE', 'LLM_SERVICE', 'LLM_MODEL']
            
            for key in service_keys:
                if key in env_content:
                    f.write(f"{key}={env_content[key]}\n")
            
            f.write("\n# Story Configuration\n")
            story_keys = ['STORY_TEMPERATURE', 'STORY_MAX_TOKENS', 'STORY_SYSTEM_PROMPT']
            
            for key in story_keys:
                if key in env_content:
                    f.write(f"{key}={env_content[key]}\n")
            
            f.write("\n# Feedback Configuration\n")
            feedback_keys = ['FEEDBACK_ENABLED', 'FEEDBACK_VOLUME', 'LOG_LEVEL']
            
            for key in feedback_keys:
                if key in env_content:
                    f.write(f"{key}={env_content[key]}\n")
            
            # Add any remaining keys
            f.write("\n# Additional Configuration\n")
            written_keys = set(hardware_keys + system_keys + web_keys + audio_keys + 
                             service_keys + story_keys + feedback_keys)
            
            for key, value in env_content.items():
                if key not in written_keys:
                    f.write(f"{key}={value}\n")
        
        # Set proper permissions
        subprocess.run(['chown', 'pi:pi', str(env_file)], check=True)
        subprocess.run(['chmod', '644', str(env_file)], check=True)
        
        logger.info("Environment variables configured successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup environment variables: {e}")
        return False

def run_tests() -> bool:
    """Run basic system tests"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Running basic system tests...")
        
        install_dir = Path("/opt/storytellerpi")
        
        # Test Python imports
        test_imports = [
            "import sys; sys.path.insert(0, '/opt/storytellerpi/main'); from config_validator import ConfigValidator; print('Config validator OK')",
            "import sys; sys.path.insert(0, '/opt/storytellerpi/main'); from service_manager import ServiceManager; print('Service manager OK')",
            "import pygame; print('Pygame OK')",
            "import numpy; print('NumPy OK')"
        ]
        
        for test in test_imports:
            try:
                result = subprocess.run([
                    sys.executable, '-c', test
                ], capture_output=True, text=True, cwd=str(install_dir))
                
                if result.returncode == 0:
                    logger.info(f"Import test passed: {result.stdout.strip()}")
                else:
                    logger.warning(f"Import test failed: {result.stderr}")
            except Exception as e:
                logger.warning(f"Import test error: {e}")
        
        # Test audio detection
        try:
            result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Audio devices detected")
            else:
                logger.warning("No audio devices found")
        except:
            logger.warning("Could not test audio devices")
        
        logger.info("Basic system tests completed")
        return True
        
    except Exception as e:
        logger.error(f"System tests failed: {e}")
        return False

def main():
    """Main setup function"""
    logger = setup_logging()
    logger.info("Starting StorytellerPi Complete Setup")
    
    setup_steps = [
        ("Checking prerequisites", check_prerequisites),
        ("Installing base packages", install_base_packages),
        ("Creating project structure", create_project_structure),
        ("Installing Python dependencies", install_python_dependencies),
        ("Running hardware-specific setup", run_hardware_specific_setup),
        ("Setting up environment variables", setup_environment_variables),
        ("Creating systemd services", create_systemd_service),
        ("Creating web interface service", create_web_interface_service),
        ("Running basic tests", run_tests)
    ]
    
    for step_name, step_function in setup_steps:
        logger.info(f"\n{'='*50}")
        logger.info(f"Step: {step_name}")
        logger.info(f"{'='*50}")
        
        if not step_function():
            logger.error(f"Setup failed at step: {step_name}")
            return 1
        
        logger.info(f"Step completed successfully: {step_name}")
    
    # Final instructions
    logger.info("\n" + "="*60)
    logger.info("STORYTELLERPI SETUP COMPLETE!")
    logger.info("="*60)
    logger.info("\nNext steps:")
    logger.info("1. Configure your API keys in /opt/storytellerpi/credentials/")
    logger.info("2. Reboot your system: sudo reboot")
    logger.info("3. After reboot, services will start automatically")
    logger.info("4. Access web interface at: http://YOUR_PI_IP:5000")
    logger.info("5. Test audio: speaker-test -t wav -c 2")
    logger.info("\nService management:")
    logger.info("  Start: sudo systemctl start storytellerpi")
    logger.info("  Stop: sudo systemctl stop storytellerpi")
    logger.info("  Status: sudo systemctl status storytellerpi")
    logger.info("  Logs: sudo journalctl -u storytellerpi -f")
    logger.info("\nWeb interface:")
    logger.info("  Start: sudo systemctl start storytellerpi-web")
    logger.info("  Status: sudo systemctl status storytellerpi-web")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())