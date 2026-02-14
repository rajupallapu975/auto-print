"""
Configuration Management
Centralized configuration for the Auto-Print System
"""
import os
import sys

# ============================================================
# BACKEND CONFIGURATION
# ============================================================
BACKEND_URL = "https://printer-backend-ch2e.onrender.com"
PRINTER_KEY = "LOCAL_PRINTER"

# ============================================================
# HARDWARE CONFIGURATION
# ============================================================
ARDUINO_PORT = "COM19" if sys.platform.startswith('win') else None

# ============================================================
# PRINTER CONFIGURATION
# ============================================================
PRINTER_NAME = None  # Auto-detect default printer
TEMP_DIR = "temp_jobs"

# ============================================================
# FIREBASE CONFIGURATION
# ============================================================
FIREBASE_KEY_PATH = "serviceAccountKey.json"

# ============================================================
# LOGGING CONFIGURATION
# ============================================================
LOG_FILE = "autoprint.log"
LOG_LEVEL = "INFO"

# ============================================================
# RETRY CONFIGURATION
# ============================================================
MAX_RETRIES = 2
TIMEOUT_SECONDS = 15
