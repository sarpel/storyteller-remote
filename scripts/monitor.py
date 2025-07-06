#!/usr/bin/env python3
"""
StorytellerPi System Monitor
Monitors system health, performance, and service status
"""

import os
import sys
import time
import psutil
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

class StorytellerMonitor:
    """System monitor for StorytellerPi"""
    
    def __init__(self, log_file: str = "logs/monitor.log"):
        self.log_file = log_file
        self.logger = self._setup_logging()
        
        # Thresholds
        self.memory_threshold = 80  # percent
        self.cpu_threshold = 85     # percent
        self.temp_threshold = 70    # Celsius
        self.disk_threshold = 90    # percent
        
    def _setup_logging(self):
        """Setup logging configuration"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def get_system_stats(self):
        """Get current system statistics"""
        stats = {}
        
        try:
            # CPU usage
            stats['cpu_percent'] = psutil.cpu_percent(interval=1)
            stats['cpu_count'] = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            stats['memory_percent'] = memory.percent
            stats['memory_available_mb'] = memory.available / (1024 * 1024)
            stats['memory_used_mb'] = memory.used / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            stats['disk_percent'] = (disk.used / disk.total) * 100
            stats['disk_free_gb'] = disk.free / (1024 * 1024 * 1024)
            
            # Temperature (Raspberry Pi specific)
            try:
                temp_output = subprocess.check_output(['vcgencmd', 'measure_temp'])
                temp_str = temp_output.decode().strip()
                stats['temperature'] = float(temp_str.split('=')[1].replace("'C", ""))
            except:
                stats['temperature'] = None
            
            # Network interfaces
            stats['network'] = {}
            for interface, addrs in psutil.net_if_addrs().items():
                if interface.startswith('wlan') or interface.startswith('eth'):
                    stats['network'][interface] = {
                        'is_up': psutil.net_if_stats()[interface].isup,
                        'addresses': [addr.address for addr in addrs if addr.family == 2]  # IPv4
                    }
            
        except Exception as e:
            self.logger.error(f"Error getting system stats: {e}")
            
        return stats    
    def check_service_status(self):
        """Check StorytellerPi service status"""
        try:
            service_name = os.getenv('SERVICE_NAME', 'storytellerpi')
            result = subprocess.run(
                ['systemctl', 'is-active', f'{service_name}.service'],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() == 'active'
        except:
            return False
    
    def get_service_logs(self, lines: int = 10):
        """Get recent service logs"""
        try:
            service_name = os.getenv('SERVICE_NAME', 'storytellerpi')
            result = subprocess.run(
                ['journalctl', '-u', f'{service_name}.service', '-n', str(lines), '--no-pager'],
                capture_output=True,
                text=True
            )
            return result.stdout
        except:
            return "Could not retrieve logs"
    
    def check_health(self):
        """Perform comprehensive health check"""
        stats = self.get_system_stats()
        issues = []
        
        # Check CPU
        if stats.get('cpu_percent', 0) > self.cpu_threshold:
            issues.append(f"High CPU usage: {stats['cpu_percent']:.1f}%")
        
        # Check memory
        if stats.get('memory_percent', 0) > self.memory_threshold:
            issues.append(f"High memory usage: {stats['memory_percent']:.1f}%")
        
        # Check temperature
        if stats.get('temperature') and stats['temperature'] > self.temp_threshold:
            issues.append(f"High temperature: {stats['temperature']:.1f}°C")
        
        # Check disk space
        if stats.get('disk_percent', 0) > self.disk_threshold:
            issues.append(f"Low disk space: {stats['disk_percent']:.1f}% used")
        
        # Check service
        if not self.check_service_status():
            issues.append("StorytellerPi service is not running")
        
        # Check network
        network_up = False
        for interface, info in stats.get('network', {}).items():
            if info['is_up'] and info['addresses']:
                network_up = True
                break
        
        if not network_up:
            issues.append("No active network connection")
        
        return issues
    
    def generate_report(self):
        """Generate comprehensive system report"""
        stats = self.get_system_stats()
        service_active = self.check_service_status()
        issues = self.check_health()
        
        report = []
        report.append("=" * 50)
        report.append(f"StorytellerPi System Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 50)
        
        # System Overview
        report.append("\n[SYSTEM OVERVIEW]")
        report.append(f"CPU Usage: {stats.get('cpu_percent', 'N/A'):.1f}%")
        report.append(f"Memory Usage: {stats.get('memory_percent', 'N/A'):.1f}% ({stats.get('memory_used_mb', 0):.0f}MB used, {stats.get('memory_available_mb', 0):.0f}MB available)")
        report.append(f"Disk Usage: {stats.get('disk_percent', 'N/A'):.1f}% ({stats.get('disk_free_gb', 0):.1f}GB free)")
        
        if stats.get('temperature'):
            report.append(f"Temperature: {stats['temperature']:.1f}°C")
        
        # Service Status
        report.append(f"\n[SERVICE STATUS]")
        report.append(f"StorytellerPi Service: {'ACTIVE' if service_active else 'INACTIVE'}")
        
        # Network Status
        report.append(f"\n[NETWORK STATUS]")
        for interface, info in stats.get('network', {}).items():
            status = "UP" if info['is_up'] else "DOWN"
            addresses = ", ".join(info['addresses']) if info['addresses'] else "No IP"
            report.append(f"{interface}: {status} ({addresses})")
        
        # Health Issues
        if issues:
            report.append(f"\n[HEALTH ISSUES]")
            for issue in issues:
                report.append(f"⚠️  {issue}")
        else:
            report.append(f"\n[HEALTH STATUS]")
            report.append("✅ All systems normal")
        
        return "\n".join(report)    
    def restart_service(self):
        """Restart the StorytellerPi service"""
        try:
            service_name = os.getenv('SERVICE_NAME', 'storytellerpi')
            subprocess.run(['sudo', 'systemctl', 'restart', f'{service_name}.service'], check=True)
            self.logger.info("StorytellerPi service restarted")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to restart service: {e}")
            return False
    
    def monitor_loop(self, interval: int = 60):
        """Continuous monitoring loop"""
        self.logger.info(f"Starting monitoring loop (interval: {interval}s)")
        
        while True:
            try:
                issues = self.check_health()
                
                if issues:
                    self.logger.warning(f"Health issues detected: {', '.join(issues)}")
                    
                    # Auto-restart service if it's down
                    if "service is not running" in str(issues):
                        self.logger.info("Attempting to restart StorytellerPi service...")
                        if self.restart_service():
                            time.sleep(10)  # Wait for service to start
                            if self.check_service_status():
                                self.logger.info("Service restart successful")
                            else:
                                self.logger.error("Service restart failed")
                else:
                    self.logger.info("All systems normal")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="StorytellerPi System Monitor")
    parser.add_argument('--report', action='store_true', help='Generate system report')
    parser.add_argument('--monitor', action='store_true', help='Start continuous monitoring')
    parser.add_argument('--check', action='store_true', help='Perform single health check')
    parser.add_argument('--restart', action='store_true', help='Restart StorytellerPi service')
    parser.add_argument('--logs', type=int, default=20, help='Show recent service logs')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds')
    
    args = parser.parse_args()
    
    monitor = StorytellerMonitor()
    
    if args.report:
        print(monitor.generate_report())
    elif args.monitor:
        monitor.monitor_loop(args.interval)
    elif args.check:
        issues = monitor.check_health()
        if issues:
            print("Health Issues:")
            for issue in issues:
                print(f"  ⚠️  {issue}")
            sys.exit(1)
        else:
            print("✅ All systems normal")
    elif args.restart:
        if monitor.restart_service():
            print("Service restarted successfully")
        else:
            print("Service restart failed")
            sys.exit(1)
    else:
        # Show logs by default
        print("Recent StorytellerPi logs:")
        print(monitor.get_service_logs(args.logs))


if __name__ == "__main__":
    main()