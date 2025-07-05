#!/usr/bin/env python3
"""
Memory Monitor for StorytellerPi on Pi Zero 2W
Monitors memory usage and provides optimization recommendations
"""

import os
import sys
import time
import psutil
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent / "main"))

class MemoryMonitor:
    """Monitor memory usage and provide optimization recommendations"""
    
    def __init__(self, log_file=None):
        self.log_file = log_file
        self.setup_logging()
        
        # Thresholds for Pi Zero 2W (512MB total RAM)
        self.warning_threshold = 75  # %
        self.critical_threshold = 85  # %
        self.max_memory_mb = 350  # MB for application
        
        # Process monitoring
        self.target_processes = [
            'storytellerpi',
            'python',
            'flask',
            'pulseaudio'
        ]
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        
        if self.log_file:
            logging.basicConfig(
                level=logging.INFO,
                format=log_format,
                handlers=[
                    logging.FileHandler(self.log_file),
                    logging.StreamHandler()
                ]
            )
        else:
            logging.basicConfig(level=logging.INFO, format=log_format)
        
        self.logger = logging.getLogger(__name__)
    
    def get_memory_info(self):
        """Get detailed memory information"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'total_mb': memory.total // (1024 * 1024),
            'available_mb': memory.available // (1024 * 1024),
            'used_mb': memory.used // (1024 * 1024),
            'free_mb': memory.free // (1024 * 1024),
            'percent': memory.percent,
            'swap_total_mb': swap.total // (1024 * 1024),
            'swap_used_mb': swap.used // (1024 * 1024),
            'swap_percent': swap.percent
        }
    
    def get_process_memory(self):
        """Get memory usage of target processes"""
        process_info = []
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                pinfo = proc.info
                name = pinfo['name']
                
                # Check if this is a target process
                if any(target in name.lower() for target in self.target_processes):
                    memory_mb = pinfo['memory_info'].rss // (1024 * 1024)
                    process_info.append({
                        'pid': pinfo['pid'],
                        'name': name,
                        'memory_mb': memory_mb,
                        'cpu_percent': pinfo['cpu_percent']
                    })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by memory usage
        process_info.sort(key=lambda x: x['memory_mb'], reverse=True)
        return process_info
    
    def get_system_info(self):
        """Get general system information"""
        try:
            # CPU info
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Load average
            load_avg = os.getloadavg()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Temperature (Pi specific)
            temp = None
            try:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temp = int(f.read()) / 1000.0
            except:
                pass
            
            return {
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'load_avg': load_avg,
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free // (1024 * 1024 * 1024),
                'temperature': temp
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return {}
    
    def analyze_memory_usage(self, memory_info, process_info):
        """Analyze memory usage and provide recommendations"""
        recommendations = []
        
        # Check overall memory usage
        if memory_info['percent'] > self.critical_threshold:
            recommendations.append({
                'level': 'CRITICAL',
                'message': f"Memory usage is critically high: {memory_info['percent']:.1f}%",
                'action': 'Consider restarting services or reducing memory usage'
            })
        elif memory_info['percent'] > self.warning_threshold:
            recommendations.append({
                'level': 'WARNING',
                'message': f"Memory usage is high: {memory_info['percent']:.1f}%",
                'action': 'Monitor closely and consider optimization'
            })
        
        # Check available memory
        if memory_info['available_mb'] < 50:
            recommendations.append({
                'level': 'CRITICAL',
                'message': f"Very low available memory: {memory_info['available_mb']}MB",
                'action': 'Free up memory immediately'
            })
        
        # Check swap usage
        if memory_info['swap_percent'] > 50:
            recommendations.append({
                'level': 'WARNING',
                'message': f"High swap usage: {memory_info['swap_percent']:.1f}%",
                'action': 'System may be slow due to swapping'
            })
        
        # Check process memory usage
        total_process_memory = sum(p['memory_mb'] for p in process_info)
        if total_process_memory > self.max_memory_mb:
            recommendations.append({
                'level': 'WARNING',
                'message': f"StorytellerPi processes using {total_process_memory}MB (limit: {self.max_memory_mb}MB)",
                'action': 'Consider optimizing application memory usage'
            })
        
        # Check for memory leaks
        for proc in process_info:
            if proc['memory_mb'] > 100:  # More than 100MB for a single process
                recommendations.append({
                    'level': 'WARNING',
                    'message': f"Process {proc['name']} (PID: {proc['pid']}) using {proc['memory_mb']}MB",
                    'action': 'Check for memory leaks or consider restarting'
                })
        
        return recommendations
    
    def print_memory_report(self):
        """Print a comprehensive memory report"""
        print("\n" + "="*60)
        print(f"StorytellerPi Memory Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Get information
        memory_info = self.get_memory_info()
        process_info = self.get_process_memory()
        system_info = self.get_system_info()
        recommendations = self.analyze_memory_usage(memory_info, process_info)
        
        # Memory summary
        print(f"\n📊 MEMORY SUMMARY")
        print(f"Total RAM: {memory_info['total_mb']}MB")
        print(f"Used: {memory_info['used_mb']}MB ({memory_info['percent']:.1f}%)")
        print(f"Available: {memory_info['available_mb']}MB")
        print(f"Free: {memory_info['free_mb']}MB")
        
        if memory_info['swap_total_mb'] > 0:
            print(f"Swap: {memory_info['swap_used_mb']}MB / {memory_info['swap_total_mb']}MB ({memory_info['swap_percent']:.1f}%)")
        
        # System information
        if system_info:
            print(f"\n🖥️  SYSTEM STATUS")
            print(f"CPU Usage: {system_info['cpu_percent']:.1f}%")
            print(f"CPU Cores: {system_info['cpu_count']}")
            print(f"Load Average: {system_info['load_avg'][0]:.2f}, {system_info['load_avg'][1]:.2f}, {system_info['load_avg'][2]:.2f}")
            print(f"Disk Usage: {system_info['disk_percent']:.1f}% (Free: {system_info['disk_free_gb']}GB)")
            
            if system_info['temperature']:
                print(f"Temperature: {system_info['temperature']:.1f}°C")
        
        # Process information
        if process_info:
            print(f"\n🔍 PROCESS MEMORY USAGE")
            print(f"{'PID':<8} {'Name':<20} {'Memory':<10} {'CPU%':<8}")
            print("-" * 50)
            
            for proc in process_info[:10]:  # Top 10 processes
                print(f"{proc['pid']:<8} {proc['name']:<20} {proc['memory_mb']:<10}MB {proc['cpu_percent']:<8.1f}%")
        
        # Recommendations
        if recommendations:
            print(f"\n⚠️  RECOMMENDATIONS")
            for rec in recommendations:
                level_color = {
                    'CRITICAL': '🔴',
                    'WARNING': '🟡',
                    'INFO': '🔵'
                }
                print(f"{level_color.get(rec['level'], '🔵')} {rec['level']}: {rec['message']}")
                print(f"   Action: {rec['action']}")
        else:
            print(f"\n✅ SYSTEM STATUS: Memory usage is within normal limits")
        
        print("\n" + "="*60)
    
    def monitor_continuous(self, interval=30):
        """Monitor memory usage continuously"""
        self.logger.info(f"Starting continuous memory monitoring (interval: {interval}s)")
        
        try:
            while True:
                memory_info = self.get_memory_info()
                process_info = self.get_process_memory()
                recommendations = self.analyze_memory_usage(memory_info, process_info)
                
                # Log current status
                self.logger.info(f"Memory: {memory_info['percent']:.1f}% used, {memory_info['available_mb']}MB available")
                
                # Log any recommendations
                for rec in recommendations:
                    if rec['level'] == 'CRITICAL':
                        self.logger.error(f"{rec['message']} - {rec['action']}")
                    elif rec['level'] == 'WARNING':
                        self.logger.warning(f"{rec['message']} - {rec['action']}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("Memory monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Error in continuous monitoring: {e}")
    
    def optimize_memory(self):
        """Attempt to optimize memory usage"""
        self.logger.info("Attempting memory optimization...")
        
        # Force garbage collection
        import gc
        collected = gc.collect()
        self.logger.info(f"Garbage collection freed {collected} objects")
        
        # Clear system caches (requires root)
        try:
            os.system("sync")
            os.system("echo 1 > /proc/sys/vm/drop_caches")
            self.logger.info("System caches cleared")
        except:
            self.logger.warning("Could not clear system caches (requires root)")
        
        # Get memory info after optimization
        memory_info = self.get_memory_info()
        self.logger.info(f"Memory after optimization: {memory_info['percent']:.1f}% used")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="StorytellerPi Memory Monitor")
    parser.add_argument('--continuous', '-c', action='store_true', 
                       help='Run continuous monitoring')
    parser.add_argument('--interval', '-i', type=int, default=30,
                       help='Monitoring interval in seconds (default: 30)')
    parser.add_argument('--log-file', '-l', type=str,
                       help='Log file path')
    parser.add_argument('--optimize', '-o', action='store_true',
                       help='Attempt memory optimization')
    
    args = parser.parse_args()
    
    # Create monitor instance
    monitor = MemoryMonitor(log_file=args.log_file)
    
    if args.optimize:
        monitor.optimize_memory()
    
    if args.continuous:
        monitor.monitor_continuous(args.interval)
    else:
        monitor.print_memory_report()


if __name__ == "__main__":
    main()