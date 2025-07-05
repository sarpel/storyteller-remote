#!/bin/bash

echo "🧹 Cleaning up StorytellerPi repository..."

# Files to remove (these were added during our optimization work)
FILES_TO_REMOVE=(
    ".env"
    "google-credentials.json"
    "README_PI_ZERO_OPTIMIZATION.md"
    "requirements_pi_zero.txt"
    "setup_pi_zero.sh"
    "setup_pi_zero_dietpi.sh"
    "fix_dietpi_setup.sh"
    "fix_usb_audio_dietpi.sh"
    "check_audio_setup.sh"
    "setup_pi_zero_optimized.sh"
    "memory_monitor.py"
    "optimize_config.py"
)

# Remove unwanted files
for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        echo "Removing $file"
        rm "$file"
    fi
done

# Remove log files
if [ -d "logs" ]; then
    echo "Cleaning logs directory"
    rm -rf logs/*
fi

# Git cleanup
echo "🔄 Git cleanup..."

# Check if we have uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Found uncommitted changes, stashing them..."
    git stash push -m "Cleanup stash $(date)"
fi

# Reset to clean state
git reset --hard HEAD

# Clean untracked files
git clean -fd

# Remove files from git if they were accidentally added
git rm --cached -r logs/ 2>/dev/null || true
git rm --cached .env 2>/dev/null || true
git rm --cached google-credentials.json 2>/dev/null || true
git rm --cached README_PI_ZERO_OPTIMIZATION.md 2>/dev/null || true
git rm --cached requirements_pi_zero.txt 2>/dev/null || true
git rm --cached setup_pi_zero*.sh 2>/dev/null || true
git rm --cached fix_*.sh 2>/dev/null || true
git rm --cached check_*.sh 2>/dev/null || true
git rm --cached memory_monitor.py 2>/dev/null || true
git rm --cached optimize_config.py 2>/dev/null || true

# Update .gitignore to prevent future issues
cat > .gitignore << 'EOF'
# Logs
logs/
*.log

# Environment files
.env
.env.local
.env.*.local

# Credentials
credentials/
google-credentials.json
*.json
!requirements.txt

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
*.bak
*.backup

# Setup variations (keep only main ones)
setup_pi_zero*.sh
fix_*.sh
check_*.sh
memory_monitor.py
optimize_config.py
README_PI_ZERO_OPTIMIZATION.md
requirements_pi_zero.txt
EOF

echo "✅ Repository cleaned!"
echo ""
echo "📋 Current clean state:"
echo "├── setup_complete.sh          # Single setup script"
echo "├── main/                      # Application source"
echo "├── models/                    # Wake word models"
echo "├── scripts/                   # Utility scripts"
echo "├── tests/                     # Test files"
echo "├── requirements.txt           # Python dependencies"
echo "└── README.md                  # Documentation"
echo ""
echo "🔧 Next steps:"
echo "1. Review changes: git status"
echo "2. Commit cleanup: git add -A && git commit -m 'Clean up repository'"
echo "3. Push changes: git push"