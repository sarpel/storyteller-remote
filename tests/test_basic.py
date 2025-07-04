"""
Basic tests for StorytellerPi components
"""

import os
import sys
import pytest
import yaml
from pathlib import Path

# Add main directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'main'))

def test_config_loading():
    """Test configuration file loading"""
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    
    assert config_path.exists(), "Configuration file should exist"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Check required sections
    assert 'audio' in config
    assert 'wake_word' in config
    assert 'apis' in config
    assert 'storyteller' in config
    
    # Check required audio settings
    assert 'sample_rate' in config['audio']
    assert 'chunk_size' in config['audio']
    
    # Check wake word settings
    assert 'model_path' in config['wake_word']
    assert 'threshold' in config['wake_word']

def test_model_files_exist():
    """Test that wake word model files exist"""
    models_dir = Path(__file__).parent.parent / 'models'
    
    # Check that at least one model file exists
    model_files = list(models_dir.glob('*.onnx')) + \
                 list(models_dir.glob('*.ppn')) + \
                 list(models_dir.glob('*.tflite'))
    
    assert len(model_files) > 0, "At least one wake word model should exist"

def test_directory_structure():
    """Test that required directories exist"""
    base_dir = Path(__file__).parent.parent
    
    required_dirs = [
        'main',
        'config', 
        'credentials',
        'models',
        'scripts',
        'logs'
    ]
    
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        assert dir_path.exists(), f"Directory {dir_name} should exist"

def test_main_modules_exist():
    """Test that main application modules exist"""
    main_dir = Path(__file__).parent.parent / 'main'
    
    required_modules = [
        'storyteller_main.py',
        'wake_word_detector.py',
        'stt_service.py',
        'storyteller_llm.py',
        'tts_service.py'
    ]
    
    for module_name in required_modules:
        module_path = main_dir / module_name
        assert module_path.exists(), f"Module {module_name} should exist"

@pytest.mark.skipif(not os.path.exists('credentials/google-credentials.json'), 
                   reason="Google credentials not available")
def test_google_credentials():
    """Test Google credentials format"""
    cred_path = Path(__file__).parent.parent / 'credentials' / 'google-credentials.json'
    
    if cred_path.exists():
        import json
        with open(cred_path, 'r') as f:
            creds = json.load(f)
        
        assert 'type' in creds
        assert 'project_id' in creds
        assert creds['type'] == 'service_account'

if __name__ == "__main__":
    pytest.main([__file__])