#!/usr/bin/env python3
"""
Lightweight Time Tracking Desktop Application
Features:
- Quick time entry with current timestamp
- Automatic task switching and previous task conclusion
- Auto-close tasks after 2 hours of inactivity
- CSV export compatible with Excel
- Real-time display of active task and duration
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import datetime
import threading
import time
import os
import sys
from pathlib import Path

# Hide console window on Windows
if os.name == 'nt':
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class TimeTracker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Time Tracker")
        self.root.geometry("600x500")
        self.root.minsize(400, 300)  # Set minimum window size
        self.root.resizable(True, True)
        
        # Application state
        self.current_task = None
        self.task_start_time = None
        self.csv_file = "time_tracker.csv"
        self.auto_close_timer = None
        self.is_running = True
        
        # Create CSV file with headers if it doesn't exist
        self.initialize_csv()
        
        # Setup GUI
        self.setup_gui()
        
        # Start background timer for auto-close
        self.start_auto_close_timer()
        
        # Start real-time update
        self.update_display()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def initialize_csv(self):
        """Initialize CSV file with headers if it doesn't exist"""
        try:
            if not os.path.exists(self.csv_file):
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Task Description', 'Start Time', 'End Time', 'Duration (minutes)', 'Date'])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize CSV file: {str(e)}")
    
    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Current task display
        ttk.Label(main_frame, text="Current Task:", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.current_task_label = ttk.Label(main_frame, text="No active task", font=('Arial', 10))
        self.current_task_label.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Duration display
        ttk.Label(main_frame, text="Duration:", font=('Arial', 12, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        self.duration_label = ttk.Label(main_frame, text="00:00:00", font=('Arial', 10))
        self.duration_label.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Task entry section
        ttk.Separator(main_frame, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(main_frame, text="New Task:", font=('Arial', 12, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        
        # Task description entry
        self.task_entry = ttk.Entry(main_frame, font=('Arial', 10))
        self.task_entry.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.task_entry.bind('<Return>', self.start_new_task)
        
        # Start task button
        self.start_button = ttk.Button(main_frame, text="Start Task", command=self.start_new_task)
        self.start_button.grid(row=5, column=0, columnspan=2, pady=(0, 10))
        
        # Control buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        # Stop current task button
        self.stop_button = ttk.Button(button_frame, text="Stop Current Task", command=self.stop_current_task)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Export CSV button
        export_button = ttk.Button(button_frame, text="Export CSV", command=self.export_csv)
        export_button.pack(side=tk.LEFT, padx=5)
        
        # View log button
        view_button = ttk.Button(button_frame, text="View Log", command=self.view_log)
        view_button.pack(side=tk.LEFT, padx=5)
        
        # Status display
        ttk.Separator(main_frame, orient='horizontal').grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Recent tasks display
        ttk.Label(main_frame, text="Recent Tasks:", font=('Arial', 12, 'bold')).grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Treeview for recent tasks
        self.tree = ttk.Treeview(main_frame, columns=('Task', 'Duration', 'Date'), show='headings', height=6)
        self.tree.heading('Task', text='Task Description')
        self.tree.heading('Duration', text='Duration (min)')
        self.tree.heading('Date', text='Date')
        
        self.tree.column('Task', width=200)
        self.tree.column('Duration', width=100)
        self.tree.column('Date', width=100)
        
        self.tree.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.tree.yview)
        scrollbar.grid(row=9, column=2, sticky=(tk.N, tk.S), pady=(0, 10))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure grid weights for treeview
        main_frame.rowconfigure(9, weight=1)
        
        # Load recent tasks
        self.load_recent_tasks()
        
        # Focus on task entry
        self.task_entry.focus()
    
    def start_new_task(self, event=None):
        """Start a new task, ending the previous one if it exists"""
        task_description = self.task_entry.get().strip()
        
        if not task_description:
            messagebox.showwarning("Warning", "Please enter a task description.")
            return
        
        current_time = datetime.datetime.now()
        
        # End previous task if exists
        if self.current_task and self.task_start_time:
            self.end_task(current_time)
        
        # Start new task
        self.current_task = task_description
        self.task_start_time = current_time
        
        # Clear entry
        self.task_entry.delete(0, tk.END)
        
        # Update display
        self.update_current_task_display()
        
        # Reset auto-close timer
        self.reset_auto_close_timer()
        
        # Update recent tasks
        self.load_recent_tasks()
    
    def stop_current_task(self):
        """Stop the current task manually"""
        if not self.current_task:
            messagebox.showinfo("Info", "No active task to stop.")
            return
        
        self.end_task(datetime.datetime.now())
        self.update_current_task_display()
        self.load_recent_tasks()
    
    def end_task(self, end_time):
        """End the current task and log it to CSV"""
        if not self.current_task or not self.task_start_time:
            return
        
        duration_seconds = (end_time - self.task_start_time).total_seconds()
        duration_minutes = round(duration_seconds / 60, 2)
        
        # Format times for CSV
        start_time_str = self.task_start_time.strftime("%H:%M:%S")
        end_time_str = end_time.strftime("%H:%M:%S")
        date_str = self.task_start_time.strftime("%Y-%m-%d")
        
        # Write to CSV
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    self.current_task,
                    start_time_str,
                    end_time_str,
                    duration_minutes,
                    date_str
                ])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save task to CSV: {str(e)}")
        
        # Clear current task
        self.current_task = None
        self.task_start_time = None
        
        # Cancel auto-close timer
        if self.auto_close_timer:
            self.auto_close_timer.cancel()
            self.auto_close_timer = None
    
    def reset_auto_close_timer(self):
        """Reset the 2-hour auto-close timer"""
        if self.auto_close_timer:
            self.auto_close_timer.cancel()
        
        if self.current_task:
            self.auto_close_timer = threading.Timer(7200.0, self.auto_close_task)  # 2 hours = 7200 seconds
            self.auto_close_timer.start()
    
    def auto_close_task(self):
        """Auto-close task after 2 hours of inactivity"""
        if self.current_task:
            self.end_task(datetime.datetime.now())
            self.root.after(0, self.update_current_task_display)
            self.root.after(0, self.load_recent_tasks)
            self.root.after(0, lambda: messagebox.showinfo("Auto-Close", "Task automatically closed after 2 hours of inactivity."))
    
    def start_auto_close_timer(self):
        """Start the background timer thread"""
        def timer_thread():
            while self.is_running:
                time.sleep(1)
        
        timer = threading.Thread(target=timer_thread, daemon=True)
        timer.start()
    
    def update_display(self):
        """Update the real-time display"""
        if self.is_running:
            self.update_duration_display()
            self.root.after(1000, self.update_display)  # Update every second
    
    def update_current_task_display(self):
        """Update the current task display"""
        if self.current_task:
            self.current_task_label.config(text=self.current_task)
            self.current_task_label.config(foreground='green')
            self.stop_button.config(state='normal')
        else:
            self.current_task_label.config(text="No active task")
            self.current_task_label.config(foreground='gray')
            self.stop_button.config(state='disabled')
    
    def update_duration_display(self):
        """Update the duration display"""
        if self.current_task and self.task_start_time:
            current_time = datetime.datetime.now()
            duration = current_time - self.task_start_time
            
            # Format duration as HH:MM:SS
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.duration_label.config(text=duration_str)
            self.duration_label.config(foreground='green')
        else:
            self.duration_label.config(text="00:00:00")
            self.duration_label.config(foreground='gray')
    
    def load_recent_tasks(self):
        """Load recent tasks into the treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            if os.path.exists(self.csv_file):
                with open(self.csv_file, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    next(reader)  # Skip header
                    
                    # Read all rows and get the last 10
                    rows = list(reader)
                    recent_rows = rows[-10:] if len(rows) > 10 else rows
                    
                    # Insert in reverse order (most recent first)
                    for row in reversed(recent_rows):
                        if len(row) >= 5:
                            task_desc = row[0][:50] + "..." if len(row[0]) > 50 else row[0]
                            self.tree.insert('', 0, values=(task_desc, row[3], row[4]))
        except Exception as e:
            print(f"Error loading recent tasks: {str(e)}")
    
    def export_csv(self):
        """Export CSV to a chosen location"""
        if not os.path.exists(self.csv_file):
            messagebox.showwarning("Warning", "No data to export.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Time Tracking Data"
        )
        
        if file_path:
            try:
                import shutil
                shutil.copy2(self.csv_file, file_path)
                messagebox.showinfo("Success", f"Data exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {str(e)}")
    
    def view_log(self):
        """Open a window to view the complete log"""
        log_window = tk.Toplevel(self.root)
        log_window.title("Time Tracking Log")
        log_window.geometry("800x600")
        
        # Create treeview for full log
        log_tree = ttk.Treeview(log_window, columns=('Task', 'Start', 'End', 'Duration', 'Date'), show='headings')
        log_tree.heading('Task', text='Task Description')
        log_tree.heading('Start', text='Start Time')
        log_tree.heading('End', text='End Time')
        log_tree.heading('Duration', text='Duration (min)')
        log_tree.heading('Date', text='Date')
        
        log_tree.column('Task', width=200)
        log_tree.column('Start', width=100)
        log_tree.column('End', width=100)
        log_tree.column('Duration', width=100)
        log_tree.column('Date', width=100)
        
        log_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load all data
        try:
            if os.path.exists(self.csv_file):
                with open(self.csv_file, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    next(reader)  # Skip header
                    
                    for row in reader:
                        if len(row) >= 5:
                            log_tree.insert('', 'end', values=row)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load log data: {str(e)}")
    
    def on_closing(self):
        """Handle application closing"""
        # End current task if exists
        if self.current_task:
            self.end_task(datetime.datetime.now())
        
        # Cancel timers
        self.is_running = False
        if self.auto_close_timer:
            self.auto_close_timer.cancel()
        
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

# Initialize CSV file with sample header (will be created empty)
def create_sample_csv():
    """Create an empty CSV file with proper headers"""
    csv_file = "time_tracker.csv"
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Task Description', 'Start Time', 'End Time', 'Duration (minutes)', 'Date'])

if __name__ == "__main__":
    # Create sample CSV file
    create_sample_csv()
    
    # Start the application
    app = TimeTracker()
    app.run()
