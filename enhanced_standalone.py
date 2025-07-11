#!/usr/bin/env python3
"""
Enhanced Time Tracker - Standalone Version (No Database Dependencies)
Works entirely with CSV files, includes categories and quick buttons
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import csv
import datetime
import threading
import time
import os
import sys
from pathlib import Path

# Hide console window on Windows
if os.name == 'nt':
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

def check_display_environment():
    """Check if we have a display environment for GUI"""
    if os.name == 'nt':  # Windows
        return True
    else:  # Linux/Unix
        return 'DISPLAY' in os.environ

class EnhancedStandaloneTracker:
    def __init__(self):
        if not check_display_environment():
            raise RuntimeError("No display environment available")
        
        try:
            self.root = tk.Tk()
            self.root.title("Enhanced Time Tracker (Standalone)")
            self.root.geometry("800x700")
            self.root.minsize(600, 500)
            self.root.resizable(True, True)
        except tk.TclError as e:
            raise RuntimeError(f"Cannot create GUI window: {e}")
        
        # Application state
        self.current_task = None
        self.current_task_id = None
        self.current_category_id = None
        self.task_start_time = None
        self.csv_file = "enhanced_time_tracker.csv"
        self.categories_file = "categories.csv"
        self.buttons_file = "quick_buttons.csv"
        self.auto_close_timer = None
        self.is_running = True
        self.always_on_top = tk.BooleanVar()
        
        # Initialize CSV files
        self.initialize_csv_files()
        
        # Setup GUI
        self.setup_gui()
        
        # Start update timer
        self.update_display()
        
        print("Enhanced Time Tracker (Standalone) started successfully")
    
    def initialize_csv_files(self):
        """Initialize all CSV files"""
        # Main time tracking CSV
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['ID', 'Task Description', 'Category', 'Start Time', 'End Time', 'Duration (minutes)', 'Date'])
        
        # Categories CSV
        if not os.path.exists(self.categories_file):
            with open(self.categories_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['id', 'name', 'color'])
                # Add default categories
                writer.writerow([1, 'Work', '#2196F3'])
                writer.writerow([2, 'Personal', '#4CAF50'])
                writer.writerow([3, 'Learning', '#FF9800'])
                writer.writerow([4, 'Other', '#9E9E9E'])
        
        # Quick buttons CSV
        if not os.path.exists(self.buttons_file):
            with open(self.buttons_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['id', 'task_name', 'category_id'])
    
    def get_categories(self):
        """Read categories from CSV"""
        categories = []
        try:
            with open(self.categories_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    categories.append({
                        'id': int(row['id']),
                        'name': row['name'],
                        'color': row['color']
                    })
        except Exception as e:
            print(f"Error reading categories: {e}")
        return categories
    
    def get_quick_buttons(self):
        """Read quick buttons from CSV"""
        buttons = []
        categories = self.get_categories()
        try:
            with open(self.buttons_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    category_name = None
                    if row['category_id']:
                        for cat in categories:
                            if cat['id'] == int(row['category_id']):
                                category_name = cat['name']
                                break
                    
                    buttons.append({
                        'id': int(row['id']),
                        'task_name': row['task_name'],
                        'category_id': int(row['category_id']) if row['category_id'] else None,
                        'category_name': category_name
                    })
        except Exception as e:
            print(f"Error reading buttons: {e}")
        return buttons
    
    def add_category(self, name, color='#4CAF50'):
        """Add a new category"""
        categories = self.get_categories()
        new_id = max([cat['id'] for cat in categories], default=0) + 1
        
        # Check if name already exists
        for cat in categories:
            if cat['name'].lower() == name.lower():
                raise ValueError("Category name already exists")
        
        # Add to CSV
        with open(self.categories_file, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([new_id, name, color])
        
        return new_id
    
    def add_quick_button(self, task_name, category_id=None):
        """Add a new quick button"""
        buttons = self.get_quick_buttons()
        new_id = max([btn['id'] for btn in buttons], default=0) + 1
        
        # Add to CSV
        with open(self.buttons_file, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([new_id, task_name, category_id if category_id else ''])
        
        return new_id
    
    def setup_gui(self):
        """Setup the GUI with tabs"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Main tracking tab
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Time Tracking")
        self.setup_main_tab()
        
        # Categories tab
        self.categories_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.categories_frame, text="Categories")
        self.setup_categories_tab()
        
        # Quick buttons tab
        self.buttons_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.buttons_frame, text="Quick Tasks")
        self.setup_buttons_tab()
        
        # Reports tab
        self.reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_frame, text="Reports")
        self.setup_reports_tab()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Add minimize to taskbar support
        self.is_minimized = False
        
        # Bind events for restoring from taskbar
        self.root.bind('<Map>', self.restore_from_taskbar)  # Window restored
        self.root.bind('<Button-1>', self.restore_from_taskbar)  # Click to restore
    
    def setup_main_tab(self):
        """Setup the main time tracking tab"""
        # Configure grid
        self.main_frame.columnconfigure(1, weight=1)
        
        # Task entry section
        ttk.Label(self.main_frame, text="Task Description:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.task_entry = ttk.Entry(self.main_frame, width=40)
        self.task_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        self.task_entry.bind('<Return>', self.start_new_task)
        
        # Category selection
        ttk.Label(self.main_frame, text="Category:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(self.main_frame, textvariable=self.category_var, state='readonly')
        self.category_combo.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        self.load_categories()
        
        # Buttons
        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.start_btn = ttk.Button(buttons_frame, text="Start Task", command=self.start_new_task)
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = ttk.Button(buttons_frame, text="Stop Task", command=self.stop_current_task, state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        # Always on top checkbox
        self.always_on_top_check = ttk.Checkbutton(
            buttons_frame, 
            text="Always on Top", 
            variable=self.always_on_top,
            command=self.toggle_always_on_top
        )
        self.always_on_top_check.pack(side='left', padx=10)
        
        # Minimize to taskbar checkbox
        self.minimize_to_taskbar = tk.BooleanVar(value=True)
        self.minimize_check = ttk.Checkbutton(
            buttons_frame,
            text="Minimize on Close",
            variable=self.minimize_to_taskbar
        )
        self.minimize_check.pack(side='left', padx=10)
        
        # Test timeout button (for testing - uncomment to use)
        # ttk.Button(buttons_frame, text="Test Timeout (10s)", 
        #           command=self.test_timeout).pack(side='left', padx=10)
        
        # Current task display
        self.current_task_label = ttk.Label(self.main_frame, text="No active task", font=('Arial', 10, 'bold'))
        self.current_task_label.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Duration display
        self.duration_label = ttk.Label(self.main_frame, text="", font=('Arial', 14))
        self.duration_label.grid(row=4, column=0, columnspan=2, pady=5)
        
        # Quick task buttons frame
        self.quick_buttons_frame = ttk.LabelFrame(self.main_frame, text="Quick Tasks")
        self.quick_buttons_frame.grid(row=5, column=0, columnspan=2, sticky='ew', padx=5, pady=10)
        self.load_quick_buttons()
        
        # Recent tasks
        ttk.Label(self.main_frame, text="Recent Tasks:").grid(row=6, column=0, sticky='w', padx=5, pady=(20, 5))
        
        # Treeview for recent tasks
        columns = ('Task', 'Category', 'Duration', 'Time')
        self.tree = ttk.Treeview(self.main_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == 'Task':
                self.tree.column(col, width=250)
            elif col == 'Category':
                self.tree.column(col, width=100)
            elif col == 'Duration':
                self.tree.column(col, width=80)
            else:
                self.tree.column(col, width=100)
        
        self.tree.grid(row=7, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)
        self.main_frame.rowconfigure(7, weight=1)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.main_frame, orient='vertical', command=self.tree.yview)
        scrollbar.grid(row=7, column=2, sticky='ns', pady=5)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Load recent tasks
        self.load_recent_tasks()
    
    def setup_categories_tab(self):
        """Setup categories management tab"""
        # Add category section
        ttk.Label(self.categories_frame, text="Add New Category", font=('Arial', 12, 'bold')).pack(pady=10)
        
        add_frame = ttk.Frame(self.categories_frame)
        add_frame.pack(pady=10)
        
        ttk.Label(add_frame, text="Name:").grid(row=0, column=0, padx=5)
        self.new_category_entry = ttk.Entry(add_frame, width=20)
        self.new_category_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(add_frame, text="Color:").grid(row=0, column=2, padx=5)
        self.category_color = tk.StringVar(value='#4CAF50')
        self.color_button = ttk.Button(add_frame, text="Choose Color", command=self.choose_category_color)
        self.color_button.grid(row=0, column=3, padx=5)
        
        ttk.Button(add_frame, text="Add Category", command=self.add_category_gui).grid(row=0, column=4, padx=5)
        
        # Categories list
        ttk.Label(self.categories_frame, text="Existing Categories", font=('Arial', 12, 'bold')).pack(pady=(20, 10))
        
        self.categories_tree = ttk.Treeview(self.categories_frame, columns=('Name', 'Color'), show='headings', height=10)
        self.categories_tree.heading('Name', text='Category Name')
        self.categories_tree.heading('Color', text='Color')
        self.categories_tree.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.load_categories_tree()
    
    def setup_buttons_tab(self):
        """Setup quick buttons management tab"""
        # Add button section
        ttk.Label(self.buttons_frame, text="Add Quick Task Button", font=('Arial', 12, 'bold')).pack(pady=10)
        
        add_frame = ttk.Frame(self.buttons_frame)
        add_frame.pack(pady=10)
        
        ttk.Label(add_frame, text="Task Name:").grid(row=0, column=0, padx=5)
        self.new_button_entry = ttk.Entry(add_frame, width=25)
        self.new_button_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(add_frame, text="Category:").grid(row=0, column=2, padx=5)
        self.button_category_var = tk.StringVar()
        self.button_category_combo = ttk.Combobox(add_frame, textvariable=self.button_category_var, state='readonly', width=15)
        self.button_category_combo.grid(row=0, column=3, padx=5)
        
        ttk.Button(add_frame, text="Add Button", command=self.add_button_gui).grid(row=0, column=4, padx=5)
        
        # Buttons list
        ttk.Label(self.buttons_frame, text="Quick Task Buttons", font=('Arial', 12, 'bold')).pack(pady=(20, 10))
        
        self.buttons_tree = ttk.Treeview(self.buttons_frame, columns=('Task', 'Category'), show='headings', height=10)
        self.buttons_tree.heading('Task', text='Task Name')
        self.buttons_tree.heading('Category', text='Category')
        self.buttons_tree.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.load_buttons_tree()
    
    def setup_reports_tab(self):
        """Setup reports tab"""
        ttk.Label(self.reports_frame, text="Task Reports", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Filter section
        filter_frame = ttk.Frame(self.reports_frame)
        filter_frame.pack(pady=10)
        
        ttk.Button(filter_frame, text="Show All Tasks", command=self.show_all_tasks).pack(side='left', padx=5)
        ttk.Button(filter_frame, text="Export CSV", command=self.export_csv).pack(side='left', padx=5)
        
        # Reports tree
        columns = ('Task', 'Category', 'Duration', 'Start', 'End')
        self.reports_tree = ttk.Treeview(self.reports_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.reports_tree.heading(col, text=col)
        
        self.reports_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add right-click menu for restore option
        self.setup_system_tray_menu()
    
    def load_categories(self):
        """Load categories into comboboxes"""
        categories = self.get_categories()
        category_names = [''] + [cat['name'] for cat in categories]
        
        # Update main tab combobox
        self.category_combo['values'] = category_names
        
        # Update buttons tab combobox if it exists
        if hasattr(self, 'button_category_combo'):
            self.button_category_combo['values'] = category_names
    
    def load_categories_tree(self):
        """Load categories into tree view"""
        # Clear existing items
        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)
        
        categories = self.get_categories()
        for cat in categories:
            self.categories_tree.insert('', 'end', values=(cat['name'], cat['color']))
    
    def load_quick_buttons(self):
        """Load quick task buttons"""
        # Clear existing buttons
        for widget in self.quick_buttons_frame.winfo_children():
            widget.destroy()
        
        buttons = self.get_quick_buttons()
        for i, btn in enumerate(buttons):
            row = i // 4
            col = i % 4
            
            # Get category color
            color = '#e0e0e0'  # default
            if btn['category_id']:
                categories = self.get_categories()
                for cat in categories:
                    if cat['id'] == btn['category_id']:
                        color = cat['color']
                        break
            
            task_btn = ttk.Button(
                self.quick_buttons_frame,
                text=btn['task_name'][:15] + ('...' if len(btn['task_name']) > 15 else ''),
                command=lambda t=btn['task_name'], c=btn['category_id']: self.start_quick_task(t, c)
            )
            task_btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
        
        # Configure column weights
        for i in range(4):
            self.quick_buttons_frame.columnconfigure(i, weight=1)
    
    def load_buttons_tree(self):
        """Load buttons into tree view"""
        # Clear existing items
        for item in self.buttons_tree.get_children():
            self.buttons_tree.delete(item)
        
        buttons = self.get_quick_buttons()
        for btn in buttons:
            self.buttons_tree.insert('', 'end', values=(btn['task_name'], btn['category_name'] or 'None'))
    
    def choose_category_color(self):
        """Open color chooser"""
        color = colorchooser.askcolor(title="Choose category color")[1]
        if color:
            self.category_color.set(color)
    
    def add_category_gui(self):
        """Add category from GUI"""
        name = self.new_category_entry.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Please enter a category name")
            return
        
        try:
            self.add_category(name, self.category_color.get())
            self.new_category_entry.delete(0, tk.END)
            self.load_categories()
            self.load_categories_tree()
            messagebox.showinfo("Success", f"Category '{name}' added successfully")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def add_button_gui(self):
        """Add quick button from GUI"""
        task_name = self.new_button_entry.get().strip()
        category_name = self.button_category_var.get()
        
        if not task_name:
            messagebox.showwarning("Warning", "Please enter a task name")
            return
        
        # Find category ID
        category_id = None
        if category_name:
            categories = self.get_categories()
            for cat in categories:
                if cat['name'] == category_name:
                    category_id = cat['id']
                    break
        
        try:
            self.add_quick_button(task_name, category_id)
            self.new_button_entry.delete(0, tk.END)
            self.button_category_var.set('')
            self.load_quick_buttons()
            self.load_buttons_tree()
            messagebox.showinfo("Success", f"Quick button '{task_name}' added successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def start_quick_task(self, task_name, category_id):
        """Start a task from quick button"""
        self.task_entry.delete(0, tk.END)
        self.task_entry.insert(0, task_name)
        
        # Set category
        if category_id:
            categories = self.get_categories()
            for cat in categories:
                if cat['id'] == category_id:
                    self.category_var.set(cat['name'])
                    break
        
        self.start_new_task()
    
    def start_new_task(self, event=None):
        """Start a new task"""
        task_description = self.task_entry.get().strip()
        if not task_description:
            messagebox.showwarning("Warning", "Please enter a task description")
            return
        
        # Stop current task if running
        if self.current_task:
            self.end_current_task()
        
        # Get category
        category_name = self.category_var.get()
        
        # Start new task
        self.current_task = task_description
        self.task_start_time = datetime.datetime.now()
        
        # Start auto-close timer
        self.start_auto_close_timer()
        
        # Update UI
        self.task_entry.delete(0, tk.END)
        self.start_btn.configure(state='disabled')
        self.stop_btn.configure(state='normal')
        
        print(f"Started task: {task_description} ({category_name})")
    
    def stop_current_task(self):
        """Stop the current task"""
        if self.current_task:
            self.end_current_task()
    
    def end_current_task(self):
        """End current task and save it"""
        if not self.current_task or not self.task_start_time:
            return
        
        end_time = datetime.datetime.now()
        duration = (end_time - self.task_start_time).total_seconds() / 60
        category_name = self.category_var.get()
        
        # Generate unique ID
        task_id = int(self.task_start_time.timestamp())
        
        # Save to CSV
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                task_id,
                self.current_task,
                category_name,
                self.task_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                end_time.strftime('%Y-%m-%d %H:%M:%S'),
                round(duration, 2),
                self.task_start_time.strftime('%Y-%m-%d')
            ])
        
        print(f"Completed task: {self.current_task} ({duration:.1f} minutes)")
        
        # Cancel auto-close timer
        if self.auto_close_timer:
            self.auto_close_timer.cancel()
            self.auto_close_timer = None
        
        # Reset state
        self.current_task = None
        self.task_start_time = None
        self.category_var.set('')
        
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
            category_text = f" ({self.category_var.get()})" if self.category_var.get() else ""
            self.current_task_label.configure(text=f"Current: {self.current_task}{category_text}")
            
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
            
            # Check if task has been running for 2 hours
            if duration.total_seconds() >= 7200:  # 2 hours = 7200 seconds
                self.auto_close_task()
        else:
            self.current_task_label.configure(text="No active task")
            self.duration_label.configure(text="")
        
        # Schedule next update
        self.root.after(1000, self.update_display)
    
    def load_recent_tasks(self):
        """Load recent tasks into display"""
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
                            row['Task Description'][:40] + ('...' if len(row['Task Description']) > 40 else ''),
                            row['Category'],
                            duration,
                            time_str
                        ))
        except Exception as e:
            print(f"Error loading recent tasks: {e}")
    
    def show_all_tasks(self):
        """Show all tasks in reports"""
        # Clear existing items
        for item in self.reports_tree.get_children():
            self.reports_tree.delete(item)
        
        try:
            with open(self.csv_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['End Time']:  # Only show completed tasks
                        start_time = datetime.datetime.strptime(row['Start Time'], '%Y-%m-%d %H:%M:%S')
                        end_time = datetime.datetime.strptime(row['End Time'], '%Y-%m-%d %H:%M:%S')
                        
                        self.reports_tree.insert('', 'end', values=(
                            row['Task Description'],
                            row['Category'],
                            f"{float(row['Duration (minutes)']):0.1f} min",
                            start_time.strftime('%H:%M'),
                            end_time.strftime('%H:%M')
                        ))
        except Exception as e:
            print(f"Error loading tasks: {e}")
    
    def toggle_always_on_top(self):
        """Toggle always on top"""
        try:
            self.root.attributes('-topmost', self.always_on_top.get())
        except Exception as e:
            print(f"Always on top not supported: {e}")
    
    def start_auto_close_timer(self):
        """Start the 2-hour auto-close timer"""
        # Cancel any existing timer
        if self.auto_close_timer:
            self.auto_close_timer.cancel()
        
        # Start new timer for 2 hours (7200 seconds)
        self.auto_close_timer = threading.Timer(7200, self.auto_close_task)
        self.auto_close_timer.daemon = True
        self.auto_close_timer.start()
        print("Auto-close timer started - task will close after 2 hours")
    
    def auto_close_task(self):
        """Auto-close task after 2 hours"""
        if self.current_task:
            print(f"Auto-closing task after 2 hours: {self.current_task}")
            try:
                # Use thread-safe method to close task
                self.root.after(0, self._auto_close_task_safe)
            except Exception as e:
                print(f"Error in auto-close: {e}")
    
    def _auto_close_task_safe(self):
        """Thread-safe auto-close task"""
        if self.current_task:
            # Show notification
            if not self.is_minimized:
                messagebox.showinfo("Task Auto-Closed", 
                    f"Task '{self.current_task}' has been automatically closed after 2 hours.")
            
            # End the task
            self.end_current_task()
            print("Task auto-closed successfully after 2 hours")
    
    def test_timeout(self):
        """Test timeout functionality with 10 seconds (for testing only)"""
        if self.current_task:
            # Cancel existing timer and start 10-second timer
            if self.auto_close_timer:
                self.auto_close_timer.cancel()
            
            self.auto_close_timer = threading.Timer(10, self.auto_close_task)
            self.auto_close_timer.daemon = True
            self.auto_close_timer.start()
            print("Test timeout started - task will close in 10 seconds")
    
    def setup_system_tray_menu(self):
        """Setup right-click context menu for system tray functionality"""
        try:
            # Create a simple menu for right-click
            self.context_menu = tk.Menu(self.root, tearoff=0)
            self.context_menu.add_command(label="Restore Window", command=self.restore_from_taskbar)
            self.context_menu.add_command(label="Show Current Task", command=self.show_current_task_popup)
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Exit Application", command=self.actual_close)
            
            # Bind right-click to show menu
            self.root.bind("<Button-3>", self.show_context_menu)
            
        except Exception as e:
            print(f"Error setting up context menu: {e}")
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing context menu: {e}")
        finally:
            self.context_menu.grab_release()
    
    def show_current_task_popup(self):
        """Show current task in a popup"""
        if self.current_task:
            duration = datetime.datetime.now() - self.task_start_time
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            
            if hours > 0:
                duration_text = f"{hours:02d}:{minutes:02d}"
            else:
                duration_text = f"{minutes:02d} minutes"
            
            message = f"Current Task: {self.current_task}\nDuration: {duration_text}"
            if self.category_var.get():
                message += f"\nCategory: {self.category_var.get()}"
        else:
            message = "No active task"
        
        # Show in console (for when minimized)
        print(f"Task Status: {message}")
        
        # Also show popup if window is visible
        if not self.is_minimized:
            messagebox.showinfo("Current Task", message)
    
    def export_csv(self):
        """Export CSV to chosen location"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialname="enhanced_time_tracker_export.csv"
            )
            
            if file_path:
                import shutil
                shutil.copy2(self.csv_file, file_path)
                messagebox.showinfo("Export Complete", f"Data exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def on_closing(self):
        """Handle window closing"""
        # Check if minimize to taskbar is enabled
        if self.minimize_to_taskbar.get():
            self.minimize_to_taskbar_action()
        else:
            self.actual_close()
    
    def minimize_to_taskbar_action(self):
        """Minimize window to taskbar instead of closing"""
        try:
            # Minimize to taskbar
            self.root.withdraw()  # Hide the window
            self.is_minimized = True
            
            # Show notification in console
            print("Time Tracker minimized to taskbar. Double-click the taskbar icon to restore.")
            
            # For Windows, try to minimize to system tray properly
            if os.name == 'nt':
                try:
                    self.root.iconify()  # Minimize to taskbar
                except Exception:
                    pass  # Fallback already handled by withdraw()
            
        except Exception as e:
            print(f"Error minimizing: {e}")
            # Fallback to normal close
            self.actual_close()
    
    def restore_from_taskbar(self, event=None):
        """Restore window from taskbar"""
        if self.is_minimized:
            self.root.deiconify()  # Restore window
            self.root.lift()       # Bring to front
            self.is_minimized = False
    
    def actual_close(self):
        """Actually close the application"""
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
        print("2. Use the web interface instead: python web_standalone.py")
        print("3. Access the web interface at: http://localhost:5000")
        print()
        print("The web interface provides the same functionality in your browser!")
        print("=" * 60)
        sys.exit(0)
    
    try:
        app = EnhancedStandaloneTracker()
        app.run()
    except RuntimeError as e:
        print("=" * 60)
        print("DISPLAY ERROR - GUI CANNOT START")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("This error means no graphical display is available.")
        print("SOLUTION: Use the web interface instead!")
        print("Run: python web_standalone.py")
        print("Then open: http://localhost:5000")
        print("=" * 60)
    except Exception as e:
        print(f"Error starting Enhanced Time Tracker: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")