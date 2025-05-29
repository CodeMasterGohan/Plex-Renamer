#!/usr/bin/env python3
"""
Plex-Optimized Media Renamer
Main entry point for the application
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import logging

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.main_window import PlexRenamerApp
from src.utils.logger import setup_logging

def main():
    """Main entry point for the Plex Media Renamer application."""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting Plex Media Renamer application")
        
        # Create the main application window
        root = tk.Tk()
        app = PlexRenamerApp(root)
        
        # Start the GUI event loop
        root.mainloop()
        
    except Exception as e:
        # Show error message and log the error
        error_msg = f"Failed to start application: {str(e)}"
        logging.error(error_msg, exc_info=True)
        
        # Try to show a message box, but if that fails, print to console
        try:
            messagebox.showerror("Application Error", error_msg)
        except:
            print(f"ERROR: {error_msg}", file=sys.stderr)
        
        sys.exit(1)

if __name__ == "__main__":
    main() 