#!/bin/bash

# 🍓 Raspberry Pi Auto-Print Setup Script
# This script automates the installation and configuration process

set -e  # Exit on error

echo "=================================="
echo "🍓 Raspberry Pi Auto-Print Setup"
echo "=================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    print_warning "This doesn't appear to be a Raspberry Pi."
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Update system
print_info "Step 1/7: Updating system packages..."
sudo apt update
sudo apt upgrade -y
print_success "System updated"

# Step 2: Install system dependencies
print_info "Step 2/7: Installing system dependencies..."
sudo apt install -y python3-pip python3-venv git cups cups-client
print_success "System dependencies installed"

# Step 3: Enable and start CUPS
print_info "Step 3/7: Configuring CUPS printing service..."
sudo systemctl enable cups
sudo systemctl start cups
sudo usermod -a -G lpadmin $USER
print_success "CUPS configured"
print_warning "You may need to reboot for printer permissions to take effect"

# Step 4: Setup Python virtual environment
print_info "Step 4/7: Setting up Python virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Step 5: Activate venv and install Python dependencies
print_info "Step 5/7: Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
print_success "Python dependencies installed"

# Step 6: Check for Firebase credentials
print_info "Step 6/7: Checking Firebase credentials..."
if [ ! -f "serviceAccountKey.json" ]; then
    print_error "serviceAccountKey.json not found!"
    print_warning "You MUST add your Firebase Admin SDK credentials file"
    print_info "Download from: Firebase Console → Project Settings → Service Accounts"
    print_info "Place the file in: $(pwd)/serviceAccountKey.json"
else
    print_success "Firebase credentials found"
fi

# Step 7: Configuration
print_info "Step 7/7: Configuration..."
echo ""
echo "Please configure the following in main.py:"
echo "  1. BACKEND_BASE_URL - Your backend server URL"
echo "  2. PRINTER_NAME - Your printer name (optional)"
echo ""
read -p "Do you want to edit main.py now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    nano main.py
fi

# Check available printers
print_info "Checking for available printers..."
if command -v lpstat &> /dev/null; then
    echo ""
    echo "Available printers:"
    lpstat -p -d 2>/dev/null || print_warning "No printers found. Connect a printer and run: lpstat -p -d"
    echo ""
fi

# Final instructions
echo ""
echo "=================================="
print_success "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Ensure serviceAccountKey.json is in place"
echo "  2. Configure BACKEND_BASE_URL in main.py"
echo "  3. Connect and configure your printer"
echo "  4. Run the application:"
echo ""
echo "     source venv/bin/activate"
echo "     python main.py"
echo ""
echo "Optional: Setup auto-start on boot"
echo "  See RASPBERRY_PI_SETUP.md for instructions"
echo ""
print_warning "IMPORTANT: You may need to reboot for printer permissions"
read -p "Reboot now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo reboot
fi
