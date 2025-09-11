"""
Command-line entry point for the MongoDB ETL GUI
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from mongodb_etl.gui import main

if __name__ == "__main__":
    main()
