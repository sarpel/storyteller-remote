#!/usr/bin/env python3
"""
Configuration Optimizer for StorytellerPi on Pi Zero 2W
Automatically optimizes configuration based on available resources
"""

import os
import sys
import psutil
import logging
from pathlib import Path
from dotenv import load_dotenv, set_key

class ConfigOptimizer:
    """Optimize configuration for Pi Zero 2W"""
    
    def __init__(self, env_file=None):
        self.env_file = env_file or "/opt/storytellerpi/.env"
        self.logger = logging.getLogger(__name__)
        
        # Load current configuration
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file)
        
        # System information
        self.total_memory_mb = psutil.virtual_memory().total // (1024 * 1024)
        self.cpu_count = psutil.cpu_count()
        self.is_pi_zero = self.total_memory_mb <= 512
        
        # Optimization profiles
        self.profiles = {
            'minimal': {
                'description': 'Minimal footprint - basic functionality only',
                'max_memory_usage': 200,
                'wake_word_framework': 'porcupine',
                'wake_word_buffer_size': 256,
                'target_response_time': 20.0,
                'log_level': 'ERROR',
                'enable_memory_monitoring': True,
                'gc_frequency': 20,
                'web_interface': 'lite'
            },
            'balanced': {
                'description': 'Balanced performance and features',
                'max_memory_usage': 300,
                'wake_word_framework': 'porcupine',
                'wake_word_buffer_size': 512,
                'target_response_time': 15.0,
                'log_level': 'WARNING',
                'enable_memory_monitoring': True,
                'gc_frequency': 30,
                'web_interface': 'lite'
            },
            'performance': {
                'description': 'Better performance with more memory usage',
                'max_memory_usage': 400,
                'wake_word_framework': 'porcupine',
                'wake_word_buffer_size': 1024,
                'target_response_time': 12.0,
                'log_level': 'INFO',
                'enable_memory_monitoring': True,
                'gc_frequency': 45,
                'web_interface': 'full'
            }
        }
    
    def detect_optimal_profile(self):
        """Detect the optimal configuration profile based on system resources"""
        available_memory = psutil.virtual_memory().available // (1024 * 1024)
        
        if self.total_memory_mb <= 512:
            if available_memory < 200:
                return 'minimal'
            elif available_memory < 300:
                return 'balanced'
            else:
                return 'balanced'  # Still conservative for Pi Zero
        else:
            # More than 512MB - not a Pi Zero
            if available_memory < 400:
                return 'balanced'
            else:
                return 'performance'
    
    def get_current_config(self):
        """Get current configuration values"""
        config = {}
        
        # Memory settings
        config['max_memory_usage'] = int(os.getenv('MAX_MEMORY_USAGE', '400'))
        config['target_response_time'] = float(os.getenv('TARGET_RESPONSE_TIME', '11.0'))
        config['log_level'] = os.getenv('LOG_LEVEL', 'INFO')
        config['enable_memory_monitoring'] = os.getenv('ENABLE_MEMORY_MONITORING', 'true').lower() == 'true'
        config['gc_frequency'] = int(os.getenv('GC_FREQUENCY', '30'))
        
        # Wake word settings
        config['wake_word_framework'] = os.getenv('WAKE_WORD_FRAMEWORK', 'porcupine')
        config['wake_word_buffer_size'] = int(os.getenv('WAKE_WORD_BUFFER_SIZE', '1024'))
        config['wake_word_threshold'] = float(os.getenv('WAKE_WORD_THRESHOLD', '0.5'))
        
        # Web interface
        config['web_interface'] = 'lite' if 'lite' in os.getenv('WEB_INTERFACE', 'lite') else 'full'
        
        return config
    
    def apply_profile(self, profile_name):
        """Apply a configuration profile"""
        if profile_name not in self.profiles:
            raise ValueError(f"Unknown profile: {profile_name}")
        
        profile = self.profiles[profile_name]
        self.logger.info(f"Applying profile: {profile_name} - {profile['description']}")
        
        # Apply settings
        set_key(self.env_file, 'MAX_MEMORY_USAGE', str(profile['max_memory_usage']))
        set_key(self.env_file, 'TARGET_RESPONSE_TIME', str(profile['target_response_time']))
        set_key(self.env_file, 'LOG_LEVEL', profile['log_level'])
        set_key(self.env_file, 'ENABLE_MEMORY_MONITORING', str(profile['enable_memory_monitoring']).lower())
        set_key(self.env_file, 'GC_FREQUENCY', str(profile['gc_frequency']))
        set_key(self.env_file, 'WAKE_WORD_FRAMEWORK', profile['wake_word_framework'])
        set_key(self.env_file, 'WAKE_WORD_BUFFER_SIZE', str(profile['wake_word_buffer_size']))
        set_key(self.env_file, 'WEB_INTERFACE', profile['web_interface'])
        
        # Pi Zero specific optimizations
        if self.is_pi_zero:
            set_key(self.env_file, 'WAKE_WORD_SAMPLE_RATE', '16000')
            set_key(self.env_file, 'WAKE_WORD_CHANNELS', '1')
            set_key(self.env_file, 'AUDIO_QUALITY', 'low')
            set_key(self.env_file, 'ENABLE_AUDIO_PROCESSING', 'false')
        
        self.logger.info(f"Profile {profile_name} applied successfully")
    
    def optimize_for_current_system(self):
        """Automatically optimize configuration for current system"""
        self.logger.info("Analyzing system for optimal configuration...")
        
        # Get system info
        memory_info = psutil.virtual_memory()
        cpu_info = psutil.cpu_count()
        
        self.logger.info(f"System: {memory_info.total // (1024*1024)}MB RAM, {cpu_info} CPU cores")
        self.logger.info(f"Available memory: {memory_info.available // (1024*1024)}MB")
        
        # Detect optimal profile
        optimal_profile = self.detect_optimal_profile()
        self.logger.info(f"Recommended profile: {optimal_profile}")
        
        # Apply profile
        self.apply_profile(optimal_profile)
        
        return optimal_profile
    
    def print_system_analysis(self):
        """Print system analysis and recommendations"""
        print("\n" + "="*60)
        print("StorytellerPi Configuration Analysis")
        print("="*60)
        
        # System information
        memory = psutil.virtual_memory()
        print(f"\n🖥️  SYSTEM INFORMATION")
        print(f"Total RAM: {memory.total // (1024*1024)}MB")
        print(f"Available RAM: {memory.available // (1024*1024)}MB")
        print(f"CPU Cores: {psutil.cpu_count()}")
        print(f"Pi Zero 2W: {'Yes' if self.is_pi_zero else 'No'}")
        
        # Current configuration
        current_config = self.get_current_config()
        print(f"\n⚙️  CURRENT CONFIGURATION")
        print(f"Max Memory Usage: {current_config['max_memory_usage']}MB")
        print(f"Wake Word Framework: {current_config['wake_word_framework']}")
        print(f"Buffer Size: {current_config['wake_word_buffer_size']}")
        print(f"Target Response Time: {current_config['target_response_time']}s")
        print(f"Log Level: {current_config['log_level']}")
        print(f"Memory Monitoring: {'Enabled' if current_config['enable_memory_monitoring'] else 'Disabled'}")
        print(f"Web Interface: {current_config['web_interface']}")
        
        # Profile recommendations
        optimal_profile = self.detect_optimal_profile()
        print(f"\n📊 PROFILE RECOMMENDATIONS")
        print(f"Recommended Profile: {optimal_profile}")
        
        for name, profile in self.profiles.items():
            status = "✅ RECOMMENDED" if name == optimal_profile else "⚪ Available"
            print(f"\n{status} {name.upper()}")
            print(f"   Description: {profile['description']}")
            print(f"   Memory Limit: {profile['max_memory_usage']}MB")
            print(f"   Response Time: {profile['target_response_time']}s")
            print(f"   Log Level: {profile['log_level']}")
        
        # Optimization suggestions
        print(f"\n💡 OPTIMIZATION SUGGESTIONS")
        
        if current_config['max_memory_usage'] > memory.available // (1024*1024):
            print("⚠️  Memory limit is higher than available memory")
            print("   Consider reducing MAX_MEMORY_USAGE")
        
        if current_config['wake_word_framework'] != 'porcupine' and self.is_pi_zero:
            print("⚠️  Consider using Porcupine for better Pi Zero performance")
        
        if current_config['log_level'] == 'DEBUG' and self.is_pi_zero:
            print("⚠️  Debug logging uses extra memory and CPU")
            print("   Consider setting LOG_LEVEL to WARNING or ERROR")
        
        if not current_config['enable_memory_monitoring'] and self.is_pi_zero:
            print("⚠️  Memory monitoring is disabled")
            print("   Consider enabling it for Pi Zero 2W")
        
        print("\n" + "="*60)
    
    def interactive_optimization(self):
        """Interactive configuration optimization"""
        print("\n🎯 StorytellerPi Configuration Optimizer")
        print("="*50)
        
        self.print_system_analysis()
        
        print(f"\nWould you like to apply the recommended optimizations?")
        optimal_profile = self.detect_optimal_profile()
        print(f"This will apply the '{optimal_profile}' profile.")
        
        response = input("\nApply optimizations? (y/N): ").lower().strip()
        
        if response == 'y' or response == 'yes':
            self.apply_profile(optimal_profile)
            print(f"\n✅ Configuration optimized with '{optimal_profile}' profile")
            print("⚠️  Please restart the StorytellerPi service for changes to take effect:")
            print("   sudo systemctl restart storytellerpi")
        else:
            print("\n❌ No changes made")
    
    def validate_configuration(self):
        """Validate current configuration"""
        issues = []
        config = self.get_current_config()
        memory = psutil.virtual_memory()
        
        # Check memory limits
        if config['max_memory_usage'] > memory.total // (1024*1024) * 0.8:
            issues.append("Memory limit is too high for this system")
        
        # Check wake word framework
        if config['wake_word_framework'] not in ['porcupine', 'openwakeword', 'tflite']:
            issues.append("Invalid wake word framework")
        
        # Check buffer size
        if config['wake_word_buffer_size'] > 2048 and self.is_pi_zero:
            issues.append("Buffer size may be too large for Pi Zero 2W")
        
        # Check response time
        if config['target_response_time'] < 10.0 and self.is_pi_zero:
            issues.append("Response time target may be too aggressive for Pi Zero 2W")
        
        return issues


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="StorytellerPi Configuration Optimizer")
    parser.add_argument('--env-file', '-e', type=str, default="/opt/storytellerpi/.env",
                       help='Path to .env file')
    parser.add_argument('--profile', '-p', type=str, choices=['minimal', 'balanced', 'performance'],
                       help='Apply specific profile')
    parser.add_argument('--auto', '-a', action='store_true',
                       help='Auto-optimize for current system')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive optimization')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze current configuration')
    parser.add_argument('--validate', '-v', action='store_true',
                       help='Validate current configuration')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Create optimizer
    optimizer = ConfigOptimizer(args.env_file)
    
    if args.profile:
        optimizer.apply_profile(args.profile)
        print(f"Applied profile: {args.profile}")
    elif args.auto:
        profile = optimizer.optimize_for_current_system()
        print(f"Auto-optimized with profile: {profile}")
    elif args.interactive:
        optimizer.interactive_optimization()
    elif args.analyze:
        optimizer.print_system_analysis()
    elif args.validate:
        issues = optimizer.validate_configuration()
        if issues:
            print("⚠️  Configuration issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ Configuration is valid")
    else:
        optimizer.print_system_analysis()


if __name__ == "__main__":
    main()