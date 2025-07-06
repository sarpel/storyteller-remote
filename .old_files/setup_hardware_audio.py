#!/usr/bin/env python3
"""
StorytellerPi Hardware-Specific Audio Setup
Handles 4 combinations: Pi Zero 2W/Pi 5 + DietPi/Raspberry Pi OS + Appropriate Audio Device
"""

import os
import sys
import subprocess
import logging
import json
from pathlib import Path
from typing import Dict, Any, Tuple

def setup_logging():
    """Setup logging for setup process"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('setup_hardware_audio.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def detect_hardware() -> Dict[str, str]:
    """Detect hardware model and OS"""
    logger = logging.getLogger(__name__)
    
    hardware_info = {
        'model': 'unknown',
        'os': 'unknown',
        'audio_device': 'unknown'
    }
    
    # Detect Raspberry Pi model
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        
        # Check for Pi Zero 2W
        if 'BCM2837' in cpuinfo and 'Pi Zero 2' in cpuinfo:
            hardware_info['model'] = 'pi_zero_2w'
            hardware_info['audio_device'] = 'iqaudio_codec_hat'
            logger.info("Detected: Raspberry Pi Zero 2W")
        
        # Check for Pi 5
        elif 'BCM2712' in cpuinfo or 'Pi 5' in cpuinfo:
            hardware_info['model'] = 'pi_5'
            hardware_info['audio_device'] = 'waveshare_usb_audio'
            logger.info("Detected: Raspberry Pi 5")
        
        # Check for other Pi models
        elif 'BCM283' in cpuinfo or 'BCM271' in cpuinfo:
            # Try to get more specific model info
            try:
                result = subprocess.run(['cat', '/proc/device-tree/model'], 
                                      capture_output=True, text=True)
                model_info = result.stdout.strip()
                
                if 'Pi Zero 2' in model_info:
                    hardware_info['model'] = 'pi_zero_2w'
                    hardware_info['audio_device'] = 'iqaudio_codec_hat'
                    logger.info(f"Detected via device-tree: {model_info}")
                elif 'Pi 5' in model_info:
                    hardware_info['model'] = 'pi_5'
                    hardware_info['audio_device'] = 'waveshare_usb_audio'
                    logger.info(f"Detected via device-tree: {model_info}")
                else:
                    logger.warning(f"Unknown Pi model: {model_info}")
            except:
                logger.warning("Could not determine specific Pi model")
        
        else:
            logger.warning("Not running on Raspberry Pi")
    
    except Exception as e:
        logger.error(f"Failed to detect hardware: {e}")
    
    # Detect OS
    try:
        # Check for DietPi
        if os.path.exists('/boot/dietpi'):
            hardware_info['os'] = 'dietpi'
            logger.info("Detected: DietPi OS")
        
        # Check for Raspberry Pi OS
        elif os.path.exists('/etc/rpi-issue'):
            hardware_info['os'] = 'raspberry_pi_os'
            logger.info("Detected: Raspberry Pi OS")
        
        # Check via /etc/os-release
        elif os.path.exists('/etc/os-release'):
            with open('/etc/os-release', 'r') as f:
                os_release = f.read()
            
            if 'DietPi' in os_release:
                hardware_info['os'] = 'dietpi'
                logger.info("Detected: DietPi OS via os-release")
            elif 'Raspbian' in os_release or 'Raspberry Pi OS' in os_release:
                hardware_info['os'] = 'raspberry_pi_os'
                logger.info("Detected: Raspberry Pi OS via os-release")
            else:
                logger.warning(f"Unknown OS: {os_release}")
        
        else:
            logger.warning("Could not determine OS")
    
    except Exception as e:
        logger.error(f"Failed to detect OS: {e}")
    
    return hardware_info

def configure_pi_zero_2w_dietpi_iqaudio(logger) -> bool:
    """Configure Pi Zero 2W + DietPi + IQAudio Codec HAT"""
    logger.info("=== Configuring Pi Zero 2W + DietPi + IQAudio Codec HAT ===")
    
    try:
        # 1. Update boot configuration
        boot_config = "/boot/config.txt"
        
        boot_additions = """
# IQAudio Codec HAT Configuration for Pi Zero 2W
dtoverlay=iqaudio-codec
gpio=25=op,dh
"""
        
        # Read existing config
        existing_config = ""
        if os.path.exists(boot_config):
            with open(boot_config, 'r') as f:
                existing_config = f.read()
        
        # Add IQAudio config if not present
        if "iqaudio-codec" not in existing_config:
            logger.info("Adding IQAudio configuration to boot config")
            with open(boot_config, 'a') as f:
                f.write(boot_additions)
        
        # 2. Install required packages
        logger.info("Installing audio packages for DietPi...")
        packages = [
            'alsa-utils',
            'alsa-tools',
            'libasound2-dev',
            'python3-pyaudio'
        ]
        
        subprocess.run(['apt-get', 'update'], check=True)
        subprocess.run(['apt-get', 'install', '-y'] + packages, check=True)
        
        # 3. Configure ALSA
        asound_conf = """
# IQAudio Codec HAT ALSA Configuration
pcm.!default {
    type asym
    playback.pcm "iqaudio_playback"
    capture.pcm "iqaudio_capture"
}

pcm.iqaudio_playback {
    type hw
    card 0
    device 0
}

pcm.iqaudio_capture {
    type hw
    card 0
    device 0
}

ctl.!default {
    type hw
    card 0
}
"""
        
        with open('/etc/asound.conf', 'w') as f:
            f.write(asound_conf)
        
        # 4. Set up audio group permissions
        subprocess.run(['usermod', '-a', '-G', 'audio', 'dietpi'], check=True)
        
        # 5. Configure modules
        modules_conf = """
# IQAudio Codec HAT modules
snd-soc-iqaudio-codec
"""
        
        with open('/etc/modules', 'a') as f:
            f.write(modules_conf)
        
        logger.info("Pi Zero 2W + DietPi + IQAudio configuration complete")
        return True
        
    except Exception as e:
        logger.error(f"Failed to configure Pi Zero 2W + DietPi: {e}")
        return False

def configure_pi_zero_2w_raspios_iqaudio(logger) -> bool:
    """Configure Pi Zero 2W + Raspberry Pi OS + IQAudio Codec HAT"""
    logger.info("=== Configuring Pi Zero 2W + Raspberry Pi OS + IQAudio Codec HAT ===")
    
    try:
        # 1. Update boot configuration
        boot_config = "/boot/config.txt"
        
        boot_additions = """
# IQAudio Codec HAT Configuration for Pi Zero 2W
dtoverlay=iqaudio-codec
gpio=25=op,dh
"""
        
        # Read existing config
        existing_config = ""
        if os.path.exists(boot_config):
            with open(boot_config, 'r') as f:
                existing_config = f.read()
        
        # Add IQAudio config if not present
        if "iqaudio-codec" not in existing_config:
            logger.info("Adding IQAudio configuration to boot config")
            with open(boot_config, 'a') as f:
                f.write(boot_additions)
        
        # 2. Install required packages
        logger.info("Installing audio packages for Raspberry Pi OS...")
        packages = [
            'alsa-utils',
            'alsa-tools',
            'libasound2-dev',
            'python3-pyaudio',
            'pulseaudio'
        ]
        
        subprocess.run(['apt-get', 'update'], check=True)
        subprocess.run(['apt-get', 'install', '-y'] + packages, check=True)
        
        # 3. Configure ALSA (Raspberry Pi OS specific)
        asound_conf = """
# IQAudio Codec HAT ALSA Configuration for Raspberry Pi OS
pcm.!default {
    type asym
    playback.pcm "iqaudio_playback"
    capture.pcm "iqaudio_capture"
}

pcm.iqaudio_playback {
    type plug
    slave.pcm "hw:0,0"
}

pcm.iqaudio_capture {
    type plug
    slave.pcm "hw:0,0"
}

ctl.!default {
    type hw
    card 0
}
"""
        
        with open('/etc/asound.conf', 'w') as f:
            f.write(asound_conf)
        
        # 4. Set up audio group permissions
        subprocess.run(['usermod', '-a', '-G', 'audio', 'pi'], check=True)
        
        # 5. Configure PulseAudio (Raspberry Pi OS includes it)
        pulse_config = """
# IQAudio Codec HAT PulseAudio Configuration
load-module module-alsa-sink device=hw:0,0 sink_name=iqaudio_output
load-module module-alsa-source device=hw:0,0 source_name=iqaudio_input
set-default-sink iqaudio_output
set-default-source iqaudio_input
"""
        
        pulse_dir = "/home/pi/.config/pulse"
        os.makedirs(pulse_dir, exist_ok=True)
        
        with open(f"{pulse_dir}/default.pa", 'w') as f:
            f.write(pulse_config)
        
        logger.info("Pi Zero 2W + Raspberry Pi OS + IQAudio configuration complete")
        return True
        
    except Exception as e:
        logger.error(f"Failed to configure Pi Zero 2W + Raspberry Pi OS: {e}")
        return False

def configure_pi5_dietpi_waveshare(logger) -> bool:
    """Configure Pi 5 + DietPi + Waveshare USB Audio Dongle"""
    logger.info("=== Configuring Pi 5 + DietPi + Waveshare USB Audio Dongle ===")
    
    try:
        # 1. Install required packages
        logger.info("Installing audio packages for Pi 5 + DietPi...")
        packages = [
            'alsa-utils',
            'alsa-tools',
            'libasound2-dev',
            'python3-pyaudio',
            'usb-modeswitch'
        ]
        
        subprocess.run(['apt-get', 'update'], check=True)
        subprocess.run(['apt-get', 'install', '-y'] + packages, check=True)
        
        # 2. Configure ALSA for USB audio
        asound_conf = """
# Waveshare USB Audio Dongle ALSA Configuration
pcm.!default {
    type asym
    playback.pcm "usb_audio_playback"
    capture.pcm "usb_audio_capture"
}

pcm.usb_audio_playback {
    type hw
    card 1
    device 0
}

pcm.usb_audio_capture {
    type hw
    card 1
    device 0
}

ctl.!default {
    type hw
    card 1
}
"""
        
        with open('/etc/asound.conf', 'w') as f:
            f.write(asound_conf)
        
        # 3. Set up audio group permissions
        subprocess.run(['usermod', '-a', '-G', 'audio', 'dietpi'], check=True)
        
        # 4. Configure USB audio modules
        modules_conf = """
# USB Audio modules for Waveshare dongle
snd-usb-audio
"""
        
        with open('/etc/modules', 'a') as f:
            f.write(modules_conf)
        
        # 5. Create udev rule for Waveshare USB Audio
        udev_rule = """
# Waveshare USB Audio Dongle udev rule
SUBSYSTEM=="usb", ATTR{idVendor}=="0d8c", ATTR{idProduct}=="0014", MODE="0666"
SUBSYSTEM=="sound", KERNEL=="card*", SUBSYSTEMS=="usb", ACTION=="add", TAG+="systemd"
"""
        
        with open('/etc/udev/rules.d/99-waveshare-usb-audio.rules', 'w') as f:
            f.write(udev_rule)
        
        subprocess.run(['udevadm', 'control', '--reload-rules'], check=True)
        
        logger.info("Pi 5 + DietPi + Waveshare USB Audio configuration complete")
        return True
        
    except Exception as e:
        logger.error(f"Failed to configure Pi 5 + DietPi: {e}")
        return False

def configure_pi5_raspios_waveshare(logger) -> bool:
    """Configure Pi 5 + Raspberry Pi OS + Waveshare USB Audio Dongle"""
    logger.info("=== Configuring Pi 5 + Raspberry Pi OS + Waveshare USB Audio Dongle ===")
    
    try:
        # 1. Install required packages
        logger.info("Installing audio packages for Pi 5 + Raspberry Pi OS...")
        packages = [
            'alsa-utils',
            'alsa-tools',
            'libasound2-dev',
            'python3-pyaudio',
            'pulseaudio',
            'usb-modeswitch'
        ]
        
        subprocess.run(['apt-get', 'update'], check=True)
        subprocess.run(['apt-get', 'install', '-y'] + packages, check=True)
        
        # 2. Configure ALSA for USB audio
        asound_conf = """
# Waveshare USB Audio Dongle ALSA Configuration for Raspberry Pi OS
pcm.!default {
    type asym
    playback.pcm "usb_audio_playback"
    capture.pcm "usb_audio_capture"
}

pcm.usb_audio_playback {
    type plug
    slave.pcm "hw:1,0"
}

pcm.usb_audio_capture {
    type plug
    slave.pcm "hw:1,0"
}

ctl.!default {
    type hw
    card 1
}
"""
        
        with open('/etc/asound.conf', 'w') as f:
            f.write(asound_conf)
        
        # 3. Set up audio group permissions
        subprocess.run(['usermod', '-a', '-G', 'audio', 'pi'], check=True)
        
        # 4. Configure PulseAudio for USB audio
        pulse_config = """
# Waveshare USB Audio Dongle PulseAudio Configuration
load-module module-alsa-sink device=hw:1,0 sink_name=waveshare_usb_output
load-module module-alsa-source device=hw:1,0 source_name=waveshare_usb_input
set-default-sink waveshare_usb_output
set-default-source waveshare_usb_input
"""
        
        pulse_dir = "/home/pi/.config/pulse"
        os.makedirs(pulse_dir, exist_ok=True)
        
        with open(f"{pulse_dir}/default.pa", 'w') as f:
            f.write(pulse_config)
        
        # 5. Create udev rule for Waveshare USB Audio
        udev_rule = """
# Waveshare USB Audio Dongle udev rule
SUBSYSTEM=="usb", ATTR{idVendor}=="0d8c", ATTR{idProduct}=="0014", MODE="0666"
SUBSYSTEM=="sound", KERNEL=="card*", SUBSYSTEMS=="usb", ACTION=="add", TAG+="systemd"
"""
        
        with open('/etc/udev/rules.d/99-waveshare-usb-audio.rules', 'w') as f:
            f.write(udev_rule)
        
        subprocess.run(['udevadm', 'control', '--reload-rules'], check=True)
        
        logger.info("Pi 5 + Raspberry Pi OS + Waveshare USB Audio configuration complete")
        return True
        
    except Exception as e:
        logger.error(f"Failed to configure Pi 5 + Raspberry Pi OS: {e}")
        return False

def create_audio_environment_config(hardware_info: Dict[str, str], logger) -> bool:
    """Create environment configuration for detected hardware"""
    logger.info("Creating audio environment configuration...")
    
    try:
        # Base environment configuration
        env_config = {
            'HARDWARE_MODEL': hardware_info['model'],
            'OPERATING_SYSTEM': hardware_info['os'],
            'AUDIO_DEVICE': hardware_info['audio_device'],
            'AUDIO_ENABLED': 'true',
            'AUDIO_INPUT_DEVICE': '',
            'AUDIO_OUTPUT_DEVICE': '',
            'AUDIO_SAMPLE_RATE': '16000',
            'AUDIO_CHANNELS': '1',
            'AUDIO_CHUNK_SIZE': '1024'
        }
        
        # Hardware-specific configurations
        if hardware_info['model'] == 'pi_zero_2w' and hardware_info['audio_device'] == 'iqaudio_codec_hat':
            env_config.update({
                'AUDIO_INPUT_DEVICE': 'hw:0,0',
                'AUDIO_OUTPUT_DEVICE': 'hw:0,0',
                'AUDIO_MIXER_CONTROL': 'PCM',
                'AUDIO_DEVICE_NAME': 'IQAudio Codec HAT',
                'AUDIO_DRIVER': 'alsa'
            })
        
        elif hardware_info['model'] == 'pi_5' and hardware_info['audio_device'] == 'waveshare_usb_audio':
            env_config.update({
                'AUDIO_INPUT_DEVICE': 'hw:1,0',
                'AUDIO_OUTPUT_DEVICE': 'hw:1,0',
                'AUDIO_MIXER_CONTROL': 'PCM',
                'AUDIO_DEVICE_NAME': 'Waveshare USB Audio Dongle',
                'AUDIO_DRIVER': 'alsa'
            })
        
        # OS-specific configurations
        if hardware_info['os'] == 'raspberry_pi_os':
            env_config.update({
                'AUDIO_SYSTEM': 'pulseaudio',
                'AUDIO_PULSE_SERVER': 'unix:/tmp/pulse-server'
            })
        else:  # DietPi
            env_config.update({
                'AUDIO_SYSTEM': 'alsa',
                'AUDIO_PULSE_SERVER': ''
            })
        
        # Write to .env file
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        
        # Read existing .env
        existing_env = {}
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_env[key.strip()] = value.strip()
        
        # Update with new audio config
        existing_env.update(env_config)
        
        # Write updated .env
        with open(env_file, 'w') as f:
            f.write("# StorytellerPi Environment Configuration\n")
            f.write("# Hardware-specific audio configuration\n\n")
            
            for key, value in existing_env.items():
                f.write(f"{key}={value}\n")
        
        logger.info(f"Audio environment configuration created: {env_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create audio environment config: {e}")
        return False

def test_audio_configuration(hardware_info: Dict[str, str], logger) -> bool:
    """Test the audio configuration"""
    logger.info("Testing audio configuration...")
    
    try:
        # Test ALSA detection
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("ALSA audio devices detected:")
            logger.info(result.stdout)
        else:
            logger.warning("No ALSA audio devices detected")
        
        # Test recording capability
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("ALSA recording devices detected:")
            logger.info(result.stdout)
        else:
            logger.warning("No ALSA recording devices detected")
        
        # Test hardware-specific audio
        if hardware_info['audio_device'] == 'iqaudio_codec_hat':
            # Test IQAudio Codec HAT
            logger.info("Testing IQAudio Codec HAT...")
            result = subprocess.run(['amixer', '-c', '0', 'sget', 'PCM'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("IQAudio Codec HAT mixer controls detected")
            else:
                logger.warning("IQAudio Codec HAT mixer controls not found")
        
        elif hardware_info['audio_device'] == 'waveshare_usb_audio':
            # Test Waveshare USB Audio
            logger.info("Testing Waveshare USB Audio Dongle...")
            result = subprocess.run(['lsusb'], capture_output=True, text=True)
            if "Audio" in result.stdout:
                logger.info("USB Audio device detected")
            else:
                logger.warning("USB Audio device not found")
        
        return True
        
    except Exception as e:
        logger.error(f"Audio test failed: {e}")
        return False

def main():
    """Main setup function"""
    logger = setup_logging()
    logger.info("Starting StorytellerPi Hardware-Specific Audio Setup")
    
    # Check if running as root
    if os.geteuid() != 0:
        logger.error("This script must be run as root (use sudo)")
        return 1
    
    # Detect hardware and OS
    hardware_info = detect_hardware()
    
    logger.info(f"Detected configuration:")
    logger.info(f"  Model: {hardware_info['model']}")
    logger.info(f"  OS: {hardware_info['os']}")
    logger.info(f"  Audio Device: {hardware_info['audio_device']}")
    
    # Configure based on detected hardware
    success = False
    
    if hardware_info['model'] == 'pi_zero_2w' and hardware_info['os'] == 'dietpi':
        success = configure_pi_zero_2w_dietpi_iqaudio(logger)
    
    elif hardware_info['model'] == 'pi_zero_2w' and hardware_info['os'] == 'raspberry_pi_os':
        success = configure_pi_zero_2w_raspios_iqaudio(logger)
    
    elif hardware_info['model'] == 'pi_5' and hardware_info['os'] == 'dietpi':
        success = configure_pi5_dietpi_waveshare(logger)
    
    elif hardware_info['model'] == 'pi_5' and hardware_info['os'] == 'raspberry_pi_os':
        success = configure_pi5_raspios_waveshare(logger)
    
    else:
        logger.error(f"Unsupported hardware/OS combination: {hardware_info}")
        return 1
    
    if not success:
        logger.error("Hardware configuration failed")
        return 1
    
    # Create environment configuration
    if not create_audio_environment_config(hardware_info, logger):
        logger.error("Failed to create environment configuration")
        return 1
    
    # Test audio configuration
    test_audio_configuration(hardware_info, logger)
    
    # Final instructions
    logger.info("\n=== SETUP COMPLETE ===")
    logger.info("Hardware-specific audio configuration complete!")
    logger.info("Please reboot your system to apply all changes:")
    logger.info("  sudo reboot")
    logger.info("\nAfter reboot, test audio with:")
    logger.info("  speaker-test -t wav -c 2")
    logger.info("  arecord -D hw:0,0 -f cd -t wav -d 5 test.wav")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())