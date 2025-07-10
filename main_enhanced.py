#!/usr/bin/env python3
"""
Enhanced Time Tracking Desktop Application with Categories and Database
Features:
- Task categorization with color coding
- Customizable quick-access buttons
- Online PostgreSQL database storage
- Filtering and reporting capabilities
- CSV export compatibility
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
from models import DatabaseManager

# Hide console window on Windows
if os.name == 'nt':
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        # If hiding console fails, continue without it
        pass

class EnhancedTimeTracker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Enhanced Time Tracker")
        self.root.geometry("800x700")
        self.root.minsize(600, 500)
        self.root.resizable(True, True)
        
        # Application state
        self.current_task = None
        self.current_task_id = None
        self.current_category_id = None
        self.task_start_time = None
        self.csv_file = "time_tracker.csv"
        self.auto_close_timer = None
        self.is_running = True
        self.always_on_top = tk.BooleanVar()
        
        # Initialize database with graceful fallback
        self.db = None
        try:
            self.db = DatabaseManager()
            self.db.initialize_database()
            print("Connected to online database successfully")
        except Exception as e:
            print(f"Database connection failed: {e}")
            print("Running in offline mode with CSV storage")
            # Don't show error dialog for server environments
            try:
                # Only show messagebox if we're in a GUI environment
                messagebox.showinfo("Offline Mode", "Database unavailable. Running in offline mode with CSV storage.\nAll features remain available!")
            except:
                # If messagebox fails, we're probably in a non-GUI environment
                pass
        
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
                    writer.writerow(['Task Description', 'Category', 'Start Time', 'End Time', 'Duration (minutes)', 'Date'])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize CSV file: {str(e)}")
    
    def setup_gui(self):
        """Setup the enhanced GUI components"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main tracking tab
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Time Tracking")
        
        # Categories tab
        self.categories_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.categories_frame, text="Categories")
        
        # Custom buttons tab
        self.buttons_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.buttons_frame, text="Quick Tasks")
        
        # Reports tab
        self.reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_frame, text="Reports")
        
        # Setup each tab
        self.setup_main_tab()
        self.setup_categories_tab()
        self.setup_buttons_tab()
        self.setup_reports_tab()
    
    def setup_main_tab(self):
        """Setup the main time tracking tab"""
        # Configure grid weights
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(8, weight=1)
        
        # Current task display
        ttk.Label(self.main_frame, text="Current Task:", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(10, 5), padx=(10, 5))
        self.current_task_label = ttk.Label(self.main_frame, text="No active task", font=('Arial', 10))
        self.current_task_label.grid(row=0, column=1, sticky=tk.W+tk.E, pady=(10, 5), padx=(0, 10))
        
        # Category display
        ttk.Label(self.main_frame, text="Category:", font=('Arial', 12, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=(0, 5), padx=(10, 5))
        self.current_category_label = ttk.Label(self.main_frame, text="None", font=('Arial', 10))
        self.current_category_label.grid(row=1, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(0, 10))
        
        # Duration display
        ttk.Label(self.main_frame, text="Duration:", font=('Arial', 12, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=(0, 10), padx=(10, 5))
        self.duration_label = ttk.Label(self.main_frame, text="00:00:00", font=('Arial', 10))
        self.duration_label.grid(row=2, column=1, sticky=tk.W+tk.E, pady=(0, 10), padx=(0, 10))
        
        # Separator
        ttk.Separator(self.main_frame, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10, padx=10)
        
        # Category selection
        ttk.Label(self.main_frame, text="Category:", font=('Arial', 12, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=(0, 5), padx=(10, 5))
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(self.main_frame, textvariable=self.category_var, state="readonly")
        self.category_combo.grid(row=4, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(0, 10))
        
        # Task entry section
        ttk.Label(self.main_frame, text="New Task:", font=('Arial', 12, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=(10, 5), padx=(10, 5))
        
        # Task description entry
        self.task_entry = ttk.Entry(self.main_frame, font=('Arial', 10))
        self.task_entry.grid(row=6, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(0, 10), padx=10)
        self.task_entry.bind('<Return>', self.start_new_task)
        
        # Control buttons frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=10, padx=10)
        
        # Start task button
        self.start_button = ttk.Button(button_frame, text="Start Task", command=self.start_new_task)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Stop current task button
        self.stop_button = ttk.Button(button_frame, text="Stop Current Task", command=self.stop_current_task)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Export CSV button
        export_button = ttk.Button(button_frame, text="Export CSV", command=self.export_csv)
        export_button.pack(side=tk.LEFT, padx=5)
        
        # Always on top checkbox
        self.always_on_top_checkbox = ttk.Checkbutton(
            button_frame, 
            text="Always on Top", 
            variable=self.always_on_top,
            command=self.toggle_always_on_top
        )
        self.always_on_top_checkbox.pack(side=tk.LEFT, padx=5)
        
        # Quick task buttons frame
        quick_frame = ttk.LabelFrame(self.main_frame, text="Quick Tasks", padding="5")
        quick_frame.grid(row=8, column=0, columnspan=2, sticky=tk.W+tk.E+tk.N+tk.S, pady=10, padx=10)
        quick_frame.columnconfigure(0, weight=1)
        quick_frame.rowconfigure(0, weight=1)
        
        # Scrollable frame for quick buttons
        self.quick_canvas = tk.Canvas(quick_frame)
        self.quick_scrollbar = ttk.Scrollbar(quick_frame, orient="vertical", command=self.quick_canvas.yview)
        self.quick_scroll_frame = ttk.Frame(self.quick_canvas)
        
        self.quick_scroll_frame.bind(
            "<Configure>",
            lambda e: self.quick_canvas.configure(scrollregion=self.quick_canvas.bbox("all"))
        )
        
        self.quick_canvas.create_window((0, 0), window=self.quick_scroll_frame, anchor="nw")
        self.quick_canvas.configure(yscrollcommand=self.quick_scrollbar.set)
        
        self.quick_canvas.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)
        self.quick_scrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)
        
        # Load initial data
        self.load_categories()
        self.load_quick_buttons()
        
        # Check for resumable task
        self.check_resumable_task()
        
        # Focus on task entry
        self.task_entry.focus()
    
    def setup_categories_tab(self):
        """Setup the categories management tab"""
        # Category management frame
        cat_frame = ttk.LabelFrame(self.categories_frame, text="Manage Categories", padding="10")
        cat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add new category section
        add_frame = ttk.Frame(cat_frame)
        add_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(add_frame, text="Category Name:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_category_entry = ttk.Entry(add_frame)
        self.new_category_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.category_color_var = tk.StringVar(value="#4CAF50")
        self.color_button = tk.Button(add_frame, text="Color", bg=self.category_color_var.get(), 
                                     width=8, command=self.choose_category_color)
        self.color_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(add_frame, text="Add Category", command=self.add_category).pack(side=tk.LEFT)
        
        # Categories list
        self.categories_tree = ttk.Treeview(cat_frame, columns=('Color', 'Tasks'), show='tree headings', height=10)
        self.categories_tree.heading('#0', text='Category Name')
        self.categories_tree.heading('Color', text='Color')
        self.categories_tree.heading('Tasks', text='Total Tasks')
        
        self.categories_tree.column('#0', width=200)
        self.categories_tree.column('Color', width=100)
        self.categories_tree.column('Tasks', width=100)
        
        self.categories_tree.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Load categories
        self.load_categories_tree()
    
    def setup_buttons_tab(self):
        """Setup the custom buttons management tab"""
        # Button management frame
        btn_frame = ttk.LabelFrame(self.buttons_frame, text="Manage Quick Task Buttons", padding="10")
        btn_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add new button section
        add_btn_frame = ttk.Frame(btn_frame)
        add_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(add_btn_frame, text="Task Name:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_button_entry = ttk.Entry(add_btn_frame)
        self.new_button_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Label(add_btn_frame, text="Category:").pack(side=tk.LEFT, padx=(5, 5))
        self.button_category_var = tk.StringVar()
        self.button_category_combo = ttk.Combobox(add_btn_frame, textvariable=self.button_category_var, 
                                                 state="readonly", width=15)
        self.button_category_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(add_btn_frame, text="Add Button", command=self.add_custom_button).pack(side=tk.LEFT)
        
        # Buttons list
        self.buttons_tree = ttk.Treeview(btn_frame, columns=('Category',), show='tree headings', height=10)
        self.buttons_tree.heading('#0', text='Task Name')
        self.buttons_tree.heading('Category', text='Category')
        
        self.buttons_tree.column('#0', width=300)
        self.buttons_tree.column('Category', width=150)
        
        self.buttons_tree.pack(fill=tk.BOTH, expand=True, pady=(10, 5))
        
        # Delete button
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_custom_button).pack(pady=5)
        
        # Load custom buttons
        self.load_custom_buttons_tree()
    
    def setup_reports_tab(self):
        """Setup the reports tab"""
        # Reports frame
        reports_frame = ttk.LabelFrame(self.reports_frame, text="Time Tracking Reports", padding="10")
        reports_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Filter frame
        filter_frame = ttk.Frame(reports_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter by Category:").pack(side=tk.LEFT, padx=(0, 5))
        self.report_category_var = tk.StringVar()
        self.report_category_combo = ttk.Combobox(filter_frame, textvariable=self.report_category_var, 
                                                 state="readonly")
        self.report_category_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(filter_frame, text="Generate Report", command=self.generate_report).pack(side=tk.LEFT)
        ttk.Button(filter_frame, text="Show All", command=self.show_all_tasks).pack(side=tk.LEFT, padx=(5, 0))
        
        # Reports tree
        self.reports_tree = ttk.Treeview(reports_frame, columns=('Category', 'Duration', 'Start', 'End'), 
                                        show='tree headings', height=15)
        self.reports_tree.heading('#0', text='Task Description')
        self.reports_tree.heading('Category', text='Category')
        self.reports_tree.heading('Duration', text='Duration (min)')
        self.reports_tree.heading('Start', text='Start Time')
        self.reports_tree.heading('End', text='End Time')
        
        self.reports_tree.column('#0', width=250)
        self.reports_tree.column('Category', width=100)
        self.reports_tree.column('Duration', width=100)
        self.reports_tree.column('Start', width=120)
        self.reports_tree.column('End', width=120)
        
        # Scrollbar for reports
        reports_scrollbar = ttk.Scrollbar(reports_frame, orient='vertical', command=self.reports_tree.yview)
        self.reports_tree.configure(yscrollcommand=reports_scrollbar.set)
        
        self.reports_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(10, 0))
        reports_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(10, 0))
        
        # Load initial report data
        self.load_report_categories()
        self.show_all_tasks()
    
    def load_categories(self):
        """Load categories into comboboxes"""
        if not self.db:
            return
        
        try:
            categories = self.db.get_categories()
            category_names = [cat['name'] for cat in categories]
            
            # Update category combobox
            self.category_combo['values'] = category_names
            if category_names and not self.category_var.get():
                self.category_var.set(category_names[0])
            
            # Update button category combobox (if it exists)
            if hasattr(self, 'button_category_combo'):
                self.button_category_combo['values'] = category_names
            
            # Update report category combobox (if it exists)
            if hasattr(self, 'report_category_combo'):
                report_values = ['All'] + category_names
                self.report_category_combo['values'] = report_values
                if not self.report_category_var.get():
                    self.report_category_var.set('All')
                
        except Exception as e:
            print(f"Error loading categories: {e}")
    
    def load_categories_tree(self):
        """Load categories into the tree view"""
        if not self.db:
            return
        
        # Clear existing items
        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)
        
        try:
            categories = self.db.get_categories()
            for cat in categories:
                # Get task count for this category
                tasks = self.db.get_tasks_by_category(cat['id'])
                task_count = len(tasks)
                
                self.categories_tree.insert('', 'end', text=cat['name'], 
                                          values=(cat['color'], task_count))
        except Exception as e:
            print(f"Error loading categories tree: {e}")
    
    def load_quick_buttons(self):
        """Load custom quick task buttons"""
        if not self.db:
            return
        
        # Clear existing buttons
        for widget in self.quick_scroll_frame.winfo_children():
            widget.destroy()
        
        try:
            buttons = self.db.get_custom_buttons()
            row = 0
            col = 0
            max_cols = 3
            
            for btn in buttons:
                color = btn['category_color'] or '#4CAF50'
                
                # Create button
                quick_btn = tk.Button(
                    self.quick_scroll_frame,
                    text=btn['task_name'],
                    bg=color,
                    fg='white',
                    font=('Arial', 9),
                    width=20,
                    height=2,
                    command=lambda t=btn['task_name'], c=btn['category_id']: self.start_quick_task(t, c)
                )
                quick_btn.grid(row=row, column=col, padx=5, pady=5, sticky=tk.W+tk.E)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            
            # Configure column weights
            for i in range(max_cols):
                self.quick_scroll_frame.columnconfigure(i, weight=1)
                
        except Exception as e:
            print(f"Error loading quick buttons: {e}")
    
    def load_custom_buttons_tree(self):
        """Load custom buttons into tree view"""
        if not self.db:
            return
        
        # Clear existing items
        for item in self.buttons_tree.get_children():
            self.buttons_tree.delete(item)
        
        try:
            buttons = self.db.get_custom_buttons()
            for btn in buttons:
                category_name = btn['category_name'] or 'No Category'
                self.buttons_tree.insert('', 'end', text=btn['task_name'], 
                                       values=(category_name,), tags=(btn['id'],))
        except Exception as e:
            print(f"Error loading custom buttons tree: {e}")
    
    def load_report_categories(self):
        """Load categories for reports"""
        self.load_categories()
    
    def choose_category_color(self):
        """Open color chooser for category"""
        color = colorchooser.askcolor(initialcolor=self.category_color_var.get())
        if color[1]:  # If user didn't cancel
            self.category_color_var.set(color[1])
            self.color_button.config(bg=color[1])
    
    def add_category(self):
        """Add a new category"""
        if not self.db:
            messagebox.showwarning("Database Error", "Database not available")
            return
        
        name = self.new_category_entry.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Please enter a category name")
            return
        
        try:
            self.db.add_category(name, self.category_color_var.get())
            self.new_category_entry.delete(0, tk.END)
            self.category_color_var.set("#4CAF50")
            self.color_button.config(bg="#4CAF50")
            
            # Refresh all category displays
            self.load_categories()
            self.load_categories_tree()
            messagebox.showinfo("Success", f"Category '{name}' added successfully")
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add category: {str(e)}")
    
    def add_custom_button(self):
        """Add a new custom button"""
        if not self.db:
            messagebox.showwarning("Database Error", "Database not available")
            return
        
        task_name = self.new_button_entry.get().strip()
        if not task_name:
            messagebox.showwarning("Warning", "Please enter a task name")
            return
        
        # Get category ID
        category_name = self.button_category_var.get()
        category_id = None
        if category_name:
            try:
                categories = self.db.get_categories()
                for cat in categories:
                    if cat['name'] == category_name:
                        category_id = cat['id']
                        break
            except Exception as e:
                print(f"Error finding category: {e}")
        
        try:
            self.db.add_custom_button(task_name, category_id)
            self.new_button_entry.delete(0, tk.END)
            
            # Refresh displays
            self.load_quick_buttons()
            self.load_custom_buttons_tree()
            messagebox.showinfo("Success", f"Quick task button '{task_name}' added successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add custom button: {str(e)}")
    
    def delete_custom_button(self):
        """Delete selected custom button"""
        if not self.db:
            messagebox.showwarning("Database Error", "Database not available")
            return
        
        selection = self.buttons_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a button to delete")
            return
        
        item = selection[0]
        button_id = self.buttons_tree.item(item, 'tags')[0]
        task_name = self.buttons_tree.item(item, 'text')
        
        if messagebox.askyesno("Confirm Delete", f"Delete quick task button '{task_name}'?"):
            try:
                self.db.delete_custom_button(button_id)
                
                # Refresh displays
                self.load_quick_buttons()
                self.load_custom_buttons_tree()
                messagebox.showinfo("Success", f"Quick task button '{task_name}' deleted successfully")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete custom button: {str(e)}")

    def delete_category(self):
        """Delete selected category"""
        if not self.db:
            messagebox.showwarning("Database Error", "Database not available")
            return
        
        selection = self.categories_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a category to delete")
            return
        
        item = selection[0]
        category_id = self.categories_tree.item(item, 'tags')[0]
        category_name = self.categories_tree.item(item, 'text')
        
        if messagebox.askyesno("Confirm Delete", f"Delete category '{category_name}'?\n\nThis will remove the category from all existing tasks and quick buttons."):
            try:
                self.db.delete_category(category_id)
                
                # Refresh displays
                self.load_categories()
                self.load_categories_tree()
                self.load_quick_buttons()
                messagebox.showinfo("Success", f"Category '{category_name}' deleted successfully")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete category: {str(e)}")
    
    def start_quick_task(self, task_name, category_id):
        """Start a task from quick button"""
        # Switch to main tab
        self.notebook.select(0)
        
        # Set task name and category
        self.task_entry.delete(0, tk.END)
        self.task_entry.insert(0, task_name)
        
        # Set category
        if category_id and self.db:
            try:
                categories = self.db.get_categories()
                for cat in categories:
                    if cat['id'] == category_id:
                        self.category_var.set(cat['name'])
                        break
            except Exception as e:
                print(f"Error setting category: {e}")
        
        # Start the task
        self.start_new_task()
    
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
        
        # Get category ID
        category_name = self.category_var.get()
        category_id = None
        if category_name and self.db:
            try:
                categories = self.db.get_categories()
                for cat in categories:
                    if cat['name'] == category_name:
                        category_id = cat['id']
                        break
            except Exception as e:
                print(f"Error finding category: {e}")
        
        # Start new task
        self.current_task = task_description
        self.current_category_id = category_id
        self.task_start_time = current_time
        
        # Add to database
        if self.db:
            try:
                self.current_task_id = self.db.add_task(task_description, category_id, current_time)
            except Exception as e:
                print(f"Error adding task to database: {e}")
                self.current_task_id = None
        
        # Clear entry
        self.task_entry.delete(0, tk.END)
        
        # Update display
        self.update_current_task_display()
        
        # Reset auto-close timer
        self.reset_auto_close_timer()
    
    def stop_current_task(self):
        """Stop the current task manually"""
        if not self.current_task:
            messagebox.showinfo("Info", "No active task to stop.")
            return
        
        self.end_task(datetime.datetime.now())
        self.update_current_task_display()
        self.show_all_tasks()  # Refresh reports
    
    def end_task(self, end_time):
        """End the current task and log it to CSV and database"""
        if not self.current_task or not self.task_start_time:
            return
        
        duration_seconds = (end_time - self.task_start_time).total_seconds()
        duration_minutes = round(duration_seconds / 60, 2)
        
        # Format times for CSV
        start_time_str = self.task_start_time.strftime("%H:%M:%S")
        end_time_str = end_time.strftime("%H:%M:%S")
        date_str = self.task_start_time.strftime("%Y-%m-%d")
        
        # Get category name for CSV
        category_name = ""
        if self.current_category_id and self.db:
            try:
                categories = self.db.get_categories()
                for cat in categories:
                    if cat['id'] == self.current_category_id:
                        category_name = cat['name']
                        break
            except Exception as e:
                print(f"Error getting category name: {e}")
        
        # Write to CSV
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    self.current_task,
                    category_name,
                    start_time_str,
                    end_time_str,
                    duration_minutes,
                    date_str
                ])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save task to CSV: {str(e)}")
        
        # Update database
        if self.db and self.current_task_id:
            try:
                self.db.end_task(self.current_task_id, end_time, duration_minutes)
            except Exception as e:
                print(f"Error updating task in database: {e}")
        
        # Clear current task
        self.current_task = None
        self.current_task_id = None
        self.current_category_id = None
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
            self.root.after(0, self.show_all_tasks)
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
            
            # Update category display
            if self.current_category_id and self.db:
                try:
                    categories = self.db.get_categories()
                    for cat in categories:
                        if cat['id'] == self.current_category_id:
                            self.current_category_label.config(text=cat['name'])
                            self.current_category_label.config(foreground=cat['color'])
                            break
                except Exception as e:
                    print(f"Error updating category display: {e}")
            else:
                self.current_category_label.config(text="None")
                self.current_category_label.config(foreground='gray')
        else:
            self.current_task_label.config(text="No active task")
            self.current_task_label.config(foreground='gray')
            self.current_category_label.config(text="None")
            self.current_category_label.config(foreground='gray')
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
    
    def generate_report(self):
        """Generate filtered report"""
        if not self.db:
            messagebox.showwarning("Database Error", "Database not available")
            return
        
        category_name = self.report_category_var.get()
        if not category_name or category_name == 'All':
            self.show_all_tasks()
            return
        
        # Clear existing items
        for item in self.reports_tree.get_children():
            self.reports_tree.delete(item)
        
        try:
            # Find category ID
            categories = self.db.get_categories()
            category_id = None
            for cat in categories:
                if cat['name'] == category_name:
                    category_id = cat['id']
                    break
            
            if category_id:
                tasks = self.db.get_tasks_by_category(category_id)
                for task in tasks:
                    start_time = task['start_time'].strftime("%H:%M:%S") if task['start_time'] else ""
                    end_time = task['end_time'].strftime("%H:%M:%S") if task['end_time'] else ""
                    
                    self.reports_tree.insert('', 'end', text=task['task_description'],
                                           values=(task['category_name'] or 'None', 
                                                 task['duration_minutes'] or 0,
                                                 start_time, end_time))
        except Exception as e:
            print(f"Error generating report: {e}")
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")
    
    def check_resumable_task(self):
        """Check if there's a recent incomplete task that can be resumed"""
        resumable_task = None
        
        # First try database
        if self.db:
            try:
                last_task = self.db.get_last_incomplete_task()
                if last_task:
                    # Check if task was started less than 2 hours ago
                    time_diff = datetime.datetime.now() - last_task['start_time']
                    if time_diff.total_seconds() < 7200:  # Less than 2 hours
                        resumable_task = last_task
            except Exception as e:
                print(f"Error checking database for resumable task: {e}")
        
        # Fallback to CSV if no database result
        if not resumable_task:
            try:
                resumable_task = self.check_csv_for_resumable_task()
            except Exception as e:
                print(f"Error checking CSV for resumable task: {e}")
        
        # Resume the task if found
        if resumable_task:
            self.resume_task(resumable_task)
    
    def check_csv_for_resumable_task(self):
        """Check CSV file for incomplete tasks (fallback method)"""
        if not os.path.exists(self.csv_file):
            return None
        
        try:
            with open(self.csv_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                
                rows = list(reader)
                if not rows:
                    return None
                
                # Check the last row
                last_row = rows[-1]
                if len(last_row) >= 6:
                    # If end time is empty, it might be incomplete
                    if not last_row[3].strip():  # End time column
                        task_desc = last_row[0]
                        category = last_row[1]
                        start_time_str = last_row[2]
                        date_str = last_row[5]
                        
                        # Parse start time
                        try:
                            start_datetime = datetime.datetime.strptime(
                                f"{date_str} {start_time_str}", 
                                "%Y-%m-%d %H:%M:%S"
                            )
                            
                            # Check if less than 2 hours ago
                            time_diff = datetime.datetime.now() - start_datetime
                            if time_diff.total_seconds() < 7200:
                                return {
                                    'task_description': task_desc,
                                    'category_name': category,
                                    'start_time': start_datetime,
                                    'id': None  # No ID for CSV tasks
                                }
                        except ValueError as e:
                            print(f"Error parsing CSV date/time: {e}")
                            
        except Exception as e:
            print(f"Error reading CSV file: {e}")
        
        return None
    
    def resume_task(self, task_data):
        """Resume a task from stored data"""
        try:
            # Set current task state
            self.current_task = task_data['task_description']
            self.task_start_time = task_data['start_time']
            self.current_task_id = task_data.get('id')
            
            # Set category if available
            if task_data.get('category_name'):
                self.category_var.set(task_data['category_name'])
                # Find category ID for database tasks
                if self.db:
                    try:
                        categories = self.db.get_categories()
                        for cat in categories:
                            if cat['name'] == task_data['category_name']:
                                self.current_category_id = cat['id']
                                break
                    except Exception as e:
                        print(f"Error finding category ID: {e}")
            
            # Update display
            self.update_current_task_display()
            
            # Reset auto-close timer for resumed task
            self.reset_auto_close_timer()
            
            # Show notification
            elapsed_time = datetime.datetime.now() - self.task_start_time
            hours = int(elapsed_time.total_seconds() // 3600)
            minutes = int((elapsed_time.total_seconds() % 3600) // 60)
            
            self.root.after(1000, lambda: messagebox.showinfo(
                "Task Resumed", 
                f"Resumed task: '{self.current_task}'\n"
                f"Running for: {hours}h {minutes}m"
            ))
            
        except Exception as e:
            print(f"Error resuming task: {e}")
            messagebox.showerror("Resume Error", f"Failed to resume task: {str(e)}")
    
    def show_all_tasks(self):
        """Show all completed tasks in reports"""
        if not self.db:
            return
        
        # Clear existing items
        for item in self.reports_tree.get_children():
            self.reports_tree.delete(item)
        
        try:
            tasks = self.db.get_recent_tasks(50)  # Show last 50 tasks
            for task in tasks:
                start_time = task['start_time'].strftime("%H:%M:%S") if task['start_time'] else ""
                end_time = task['end_time'].strftime("%H:%M:%S") if task['end_time'] else ""
                
                self.reports_tree.insert('', 'end', text=task['task_description'],
                                       values=(task['category_name'] or 'None', 
                                             task['duration_minutes'] or 0,
                                             start_time, end_time))
        except Exception as e:
            print(f"Error loading all tasks: {e}")
    
    def toggle_always_on_top(self):
        """Toggle the always on top window attribute"""
        try:
            self.root.attributes('-topmost', self.always_on_top.get())
        except Exception as e:
            print(f"Error toggling always on top: {e}")
            # Fallback for systems that don't support -topmost
            try:
                if self.always_on_top.get():
                    self.root.lift()
                    self.root.after_idle(self.root.attributes, '-topmost', True)
                else:
                    self.root.attributes('-topmost', False)
            except Exception as e2:
                print(f"Fallback also failed: {e2}")
    
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

def check_display_environment():
    """Check if we have a display environment for GUI"""
    if os.name == 'nt':  # Windows
        return True
    else:  # Linux/Unix
        return 'DISPLAY' in os.environ

if __name__ == "__main__":
    # Check if we can run GUI applications
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
        # Start the enhanced application
        app = EnhancedTimeTracker()
        app.run()
    except tk.TclError as e:
        print("=" * 60)
        print("DISPLAY ERROR - GUI CANNOT START")
        print("=" * 60)
        print(f"GUI Error: {e}")
        print()
        print("This error typically means:")
        print("- No graphical display is available")
        print("- Running on a server without GUI support")
        print("- X11 forwarding is not enabled (Linux)")
        print()
        print("SOLUTION: Use the web interface instead!")
        print("Run: python web_app.py")
        print("Then open: http://localhost:5000")
        print("=" * 60)
    except Exception as e:
        print(f"Error starting Enhanced Time Tracker: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")  # Keep window open to see error