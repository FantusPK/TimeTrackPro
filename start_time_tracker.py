#!/usr/bin/env python3
"""
Time Tracker Launcher
This script automatically detects your environment and launches the appropriate version.
"""

import os
import sys
import subprocess

def check_display_environment():
    """Check if we have a display environment for GUI"""
    if os.name == 'nt':  # Windows
        return True
    else:  # Linux/Unix
        return 'DISPLAY' in os.environ

def check_gui_available():
    """Test if GUI is actually available"""
    try:
        import tkinter as tk
        test = tk.Tk()
        test.withdraw()
        test.destroy()
        return True
    except Exception:
        return False

def main():
    print("=" * 60)
    print("TIME TRACKER APPLICATION LAUNCHER")
    print("=" * 60)
    
    # Check environment
    has_display = check_display_environment()
    gui_works = check_gui_available() if has_display else False
    
    print(f"Environment: {'Windows' if os.name == 'nt' else 'Linux/Unix'}")
    print(f"Display available: {has_display}")
    print(f"GUI functional: {gui_works}")
    print()
    
    if gui_works:
        print("✓ Desktop GUI is available!")
        print()
        print("Available options:")
        print("1. Simple Desktop App (Reliable, CSV-only)")
        print("2. Enhanced Desktop App (Categories, Database + CSV)")
        print("3. Web Interface (Browser-based, all features)")
        print()
        
        while True:
            choice = input("Choose version (1/2/3) or press Enter for web interface: ").strip()
            
            if choice == "1":
                print("Starting Simple Desktop Application...")
                try:
                    subprocess.run([sys.executable, "simple_desktop.py"])
                except KeyboardInterrupt:
                    print("Application closed by user")
                break
            elif choice == "2":
                print("Starting Enhanced Desktop Application...")
                try:
                    subprocess.run([sys.executable, "main_enhanced.py"])
                except KeyboardInterrupt:
                    print("Application closed by user")
                break
            elif choice == "3" or choice == "":
                print("Starting Web Interface...")
                print("Once started, open your browser to: http://localhost:5000")
                try:
                    subprocess.run([sys.executable, "web_app.py"])
                except KeyboardInterrupt:
                    print("Web server stopped")
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
    else:
        print("❌ Desktop GUI is not available in this environment.")
        print()
        print("This is common when running on:")
        print("- Servers without display support")
        print("- SSH connections without X11 forwarding")
        print("- Docker containers")
        print("- Cloud environments")
        print()
        print("✓ Starting Web Interface instead...")
        print("Once started, open your browser to: http://localhost:5000")
        print("The web interface provides all features in your browser!")
        print()
        
        try:
            subprocess.run([sys.executable, "web_app.py"])
        except KeyboardInterrupt:
            print("Web server stopped")

if __name__ == "__main__":
    main()