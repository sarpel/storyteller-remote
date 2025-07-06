#!/usr/bin/env python3
"""
StorytellerPi Web Interface Debug Tool
Diagnoses web interface issues and provides system status
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Add the main directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'main'))

def setup_logging():
    """Setup logging for debug output"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_system_prerequisites():
    """Check system prerequisites"""
    logger = logging.getLogger(__name__)
    issues = []
    
    # Check Python version
    python_version = sys.version_info
    logger.info(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        issues.append("Python 3.8+ required")
    
    # Check for systemctl
    systemctl_paths = ['/usr/bin/systemctl', '/bin/systemctl', '/usr/local/bin/systemctl']
    systemctl_found = False
    
    for path in systemctl_paths:
        if os.path.exists(path):
            systemctl_found = True
            logger.info(f"Found systemctl at: {path}")
            break
    
    if not systemctl_found:
        try:
            result = subprocess.run(['which', 'systemctl'], capture_output=True, text=True)
            if result.returncode == 0:
                systemctl_found = True
                logger.info(f"Found systemctl via which: {result.stdout.strip()}")
        except:
            pass
    
    if not systemctl_found:
        issues.append("systemctl not found - service management may not work")
        logger.warning("systemctl not found")
    
    # Check required Python packages
    required_packages = ['flask', 'flask_socketio', 'psutil', 'python-dotenv']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"Package {package}: OK")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"Package {package}: MISSING")
    
    if missing_packages:
        issues.append(f"Missing packages: {', '.join(missing_packages)}")
    
    return issues

def check_web_interface_files():
    """Check web interface files"""
    logger = logging.getLogger(__name__)
    issues = []
    
    # Check main files
    required_files = [
        'main/web_interface.py',
        'main/templates/dashboard.html',
        'main/templates/base.html',
        'main/static',
        '.env'
    ]
    
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            logger.info(f"File {file_path}: OK")
        else:
            issues.append(f"Missing file: {file_path}")
            logger.error(f"File {file_path}: MISSING")
    
    return issues

def test_web_interface_imports():
    """Test importing web interface modules"""
    logger = logging.getLogger(__name__)
    issues = []
    
    try:
        from web_interface import app, service_manager, config_manager, system_monitor
        logger.info("Web interface imports: OK")
        
        # Test service manager
        try:
            status = service_manager.get_service_status() if service_manager else None
            logger.info(f"Service manager status: {status}")
        except Exception as e:
            issues.append(f"Service manager error: {e}")
            logger.error(f"Service manager error: {e}")
        
        # Test config manager
        try:
            config = config_manager.get_all_config() if config_manager else {}
            logger.info(f"Config manager loaded {len(config)} settings")
        except Exception as e:
            issues.append(f"Config manager error: {e}")
            logger.error(f"Config manager error: {e}")
        
        # Test system monitor
        try:
            sys_info = system_monitor.get_system_info() if system_monitor else {}
            logger.info(f"System monitor: CPU {sys_info.get('cpu_percent', 'N/A')}%")
        except Exception as e:
            issues.append(f"System monitor error: {e}")
            logger.error(f"System monitor error: {e}")
        
    except Exception as e:
        issues.append(f"Import error: {e}")
        logger.error(f"Import error: {e}")
    
    return issues

def test_web_endpoints():
    """Test web endpoints"""
    logger = logging.getLogger(__name__)
    issues = []
    
    try:
        from web_interface import app
        
        with app.test_client() as client:
            # Test dashboard
            try:
                response = client.get('/')
                if response.status_code == 200:
                    logger.info("Dashboard endpoint: OK")
                else:
                    issues.append(f"Dashboard returned {response.status_code}")
            except Exception as e:
                issues.append(f"Dashboard error: {e}")
            
            # Test API status
            try:
                response = client.get('/api/system/status')
                if response.status_code == 200:
                    logger.info("API status endpoint: OK")
                else:
                    issues.append(f"API status returned {response.status_code}")
            except Exception as e:
                issues.append(f"API status error: {e}")
            
            # Test service control
            try:
                response = client.post('/api/service/status')
                if response.status_code in [200, 503]:  # 503 is acceptable if service manager unavailable
                    logger.info("Service control endpoint: OK")
                else:
                    issues.append(f"Service control returned {response.status_code}")
            except Exception as e:
                issues.append(f"Service control error: {e}")
    
    except Exception as e:
        issues.append(f"Endpoint testing error: {e}")
        logger.error(f"Endpoint testing error: {e}")
    
    return issues

def check_environment_variables():
    """Check environment variables"""
    logger = logging.getLogger(__name__)
    issues = []
    
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check critical environment variables
    critical_vars = [
        'INSTALL_DIR',
        'SERVICE_NAME',
        'LOG_DIR'
    ]
    
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"Environment variable {var}: {value}")
        else:
            issues.append(f"Missing environment variable: {var}")
            logger.warning(f"Environment variable {var}: NOT SET")
    
    return issues

def main():
    """Main diagnostic function"""
    logger = setup_logging()
    logger.info("Starting StorytellerPi Web Interface Diagnostics")
    
    all_issues = []
    
    # Run all checks
    logger.info("\n=== System Prerequisites ===")
    all_issues.extend(check_system_prerequisites())
    
    logger.info("\n=== File System ===")
    all_issues.extend(check_web_interface_files())
    
    logger.info("\n=== Environment Variables ===")
    all_issues.extend(check_environment_variables())
    
    logger.info("\n=== Module Imports ===")
    all_issues.extend(test_web_interface_imports())
    
    logger.info("\n=== Web Endpoints ===")
    all_issues.extend(test_web_endpoints())
    
    # Summary
    logger.info("\n=== SUMMARY ===")
    if all_issues:
        logger.error(f"Found {len(all_issues)} issues:")
        for i, issue in enumerate(all_issues, 1):
            logger.error(f"  {i}. {issue}")
        
        logger.info("\n=== RECOMMENDATIONS ===")
        if any('systemctl' in issue for issue in all_issues):
            logger.info("• Install systemd or run in manual mode")
        if any('Missing packages' in issue for issue in all_issues):
            logger.info("• Run: pip install -r requirements.txt")
        if any('Missing file' in issue for issue in all_issues):
            logger.info("• Check file permissions and installation")
        if any('environment variable' in issue.lower() for issue in all_issues):
            logger.info("• Configure .env file with required settings")
    else:
        logger.info("No issues found - web interface should work correctly")
    
    return len(all_issues)

if __name__ == '__main__':
    sys.exit(main())