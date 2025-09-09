#!/usr/bin/env python3
"""
Simple launcher script for the DecentSampler GUI application.
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from decent_sampler_gui import main
    main()
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the correct directory and have PySide6 installed.")
    sys.exit(1)
except Exception as e:
    print(f"Error running application: {e}")
    sys.exit(1)
