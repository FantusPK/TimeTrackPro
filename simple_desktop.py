#!/usr/bin/env python3
"""
Simple Time Tracker Desktop Application - Reliable Version
This version focuses on reliability and compatibility across different environments.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import datetime
import threading
import time
import os
import sys

# Environment detection
def check_gui_available():
    """Check if GUI is available"""
    try:
        # Try to create a test window
        test = tk.Tk()
        test.withdraw()  # Hide it immediately
        test.destroy()
        return True
    except Exception:
        return False

def check_display_environment():
    """Check if we have a display environment for GUI"""
    if os.name == 'nt':  # Windows
        return True
    else:  # Linux/Unix
        return 'DISPLAY' in os.environ

class SimpleTimeTracker:
    def __init__(self):
        if not check_display_environment():
            raise RuntimeError("No display environment available")
        
        self.root = tk.Tk()
        self.root.title("Simple Time Tracker")
        self.root.geometry("500x400")
        self.root.minsize(400, 300)
        
        # Application state
        self.current_task = None
        self.task_start_time = None
        self.csv_file = "simple_time_tracker.csv"
        self.is_running = True
        
        # Initialize CSV
        self.initialize_csv()
        
        # Setup GUI
        self.setup_gui()
        
        # Start update timer
        self.update_display()
        
        print("Simple Time Tracker started successfully")
    
    def initialize_csv(self):
        """Initialize CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Task Description', 'Start Time', 'End Time', 'Duration (minutes)', 'Date'])
    
    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky='nsew')
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Task entry
        ttk.Label(main_frame, text="Task Description:").grid(row=0, column=0, sticky='w', pady=5)
        self.task_entry = ttk.Entry(main_frame, width=40)
        self.task_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        self.task_entry.bind('<Return>', self.start_new_task)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.start_btn = ttk.Button(buttons_frame, text="Start Task", command=self.start_new_task)
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = ttk.Button(buttons_frame, text="Stop Task", command=self.stop_current_task, state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        # Current task display
        self.current_task_label = ttk.Label(main_frame, text="No active task", font=('Arial', 10, 'bold'))
        self.current_task_label.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Duration display
        self.duration_label = ttk.Label(main_frame, text="", font=('Arial', 12))
        self.duration_label.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Recent tasks
        ttk.Label(main_frame, text="Recent Tasks:").grid(row=4, column=0, sticky='w', pady=(20, 5))
        
        # Treeview for recent tasks
        columns = ('Task', 'Duration', 'Time')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == 'Task':
                self.tree.column(col, width=200)
            elif col == 'Duration':
                self.tree.column(col, width=80)
            else:
                self.tree.column(col, width=120)
        
        self.tree.grid(row=5, column=0, columnspan=2, sticky='nsew', pady=5)
        main_frame.rowconfigure(5, weight=1)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.tree.yview)
        scrollbar.grid(row=5, column=2, sticky='ns', pady=5)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Export button
        export_btn = ttk.Button(main_frame, text="Export CSV", command=self.export_csv)
        export_btn.grid(row=6, column=0, columnspan=2, pady=10)
        
        # Load recent tasks
        self.load_recent_tasks()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def start_new_task(self, event=None):
        """Start a new task"""
        task_description = self.task_entry.get().strip()
        if not task_description:
            messagebox.showwarning("Warning", "Please enter a task description")
            return
        
        # Stop current task if running
        if self.current_task:
            self.end_current_task()
        
        # Start new task
        self.current_task = task_description
        self.task_start_time = datetime.datetime.now()
        
        # Update UI
        self.task_entry.delete(0, tk.END)
        self.start_btn.configure(state='disabled')
        self.stop_btn.configure(state='normal')
        
        print(f"Started task: {task_description}")
    
    def stop_current_task(self):
        """Stop the current task"""
        if self.current_task:
            self.end_current_task()
    
    def end_current_task(self):
        """End the current task and save it"""
        if not self.current_task or not self.task_start_time:
            return
        
        end_time = datetime.datetime.now()
        duration = (end_time - self.task_start_time).total_seconds() / 60
        
        # Save to CSV
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                self.current_task,
                self.task_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                end_time.strftime('%Y-%m-%d %H:%M:%S'),
                round(duration, 2),
                self.task_start_time.strftime('%Y-%m-%d')
            ])
        
        print(f"Completed task: {self.current_task} ({duration:.1f} minutes)")
        
        # Reset state
        self.current_task = None
        self.task_start_time = None
        
        # Update UI
        self.start_btn.configure(state='normal')
        self.stop_btn.configure(state='disabled')
        
        # Reload recent tasks
        self.load_recent_tasks()
    
    def update_display(self):
        """Update the display every second"""
        if not self.is_running:
            return
        
        if self.current_task and self.task_start_time:
            # Update current task display
            self.current_task_label.configure(text=f"Current: {self.current_task}")
            
            # Update duration
            duration = datetime.datetime.now() - self.task_start_time
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            seconds = int(duration.total_seconds() % 60)
            
            if hours > 0:
                duration_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                duration_text = f"{minutes:02d}:{seconds:02d}"
            
            self.duration_label.configure(text=duration_text)
        else:
            self.current_task_label.configure(text="No active task")
            self.duration_label.configure(text="")
        
        # Schedule next update
        self.root.after(1000, self.update_display)
    
    def load_recent_tasks(self):
        """Load recent tasks into the display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            with open(self.csv_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                
                # Show last 20 tasks
                for row in reversed(rows[-20:]):
                    if row['End Time']:  # Only show completed tasks
                        duration = f"{float(row['Duration (minutes)']):0.1f} min"
                        start_time = datetime.datetime.strptime(row['Start Time'], '%Y-%m-%d %H:%M:%S')
                        time_str = start_time.strftime('%H:%M')
                        
                        self.tree.insert('', 'end', values=(
                            row['Task Description'][:50] + ('...' if len(row['Task Description']) > 50 else ''),
                            duration,
                            time_str
                        ))
        except Exception as e:
            print(f"Error loading recent tasks: {e}")
    
    def export_csv(self):
        """Export CSV to chosen location"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialname="time_tracker_export.csv"
            )
            
            if file_path:
                # Copy current CSV to new location
                import shutil
                shutil.copy2(self.csv_file, file_path)
                messagebox.showinfo("Export Complete", f"Data exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def on_closing(self):
        """Handle window closing"""
        if self.current_task:
            result = messagebox.askyesno("Active Task", 
                "You have an active task. Do you want to stop it before closing?")
            if result:
                self.end_current_task()
        
        self.is_running = False
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    # Check environment first
    if not check_display_environment():
        print("=" * 60)
        print("DESKTOP APPLICATION - DISPLAY ENVIRONMENT REQUIRED")
        print("=" * 60)
        print("This desktop application requires a graphical environment to run.")
        print("It appears you're running this on a server without display support.")
        print()
        print("OPTIONS:")
        print("1. Run this on your local Windows/Mac/Linux desktop computer")
        print("2. Use the web interface instead: python web_app.py")
        print("3. Access the web interface at: http://localhost:5000")
        print()
        print("The web interface provides the same functionality in your browser!")
        print("=" * 60)
        sys.exit(0)
    
    try:
        app = SimpleTimeTracker()
        app.run()
    except RuntimeError as e:
        print("=" * 60)
        print("DISPLAY ERROR - GUI CANNOT START")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("This error means no graphical display is available.")
        print("SOLUTION: Use the web interface instead!")
        print("Run: python web_app.py")
        print("Then open: http://localhost:5000")
        print("=" * 60)
    except Exception as e:
        print(f"Error starting Simple Time Tracker: {e}")
        import traceback
        traceback.print_exc()