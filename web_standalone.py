#!/usr/bin/env python3
"""
Time Tracker Web Interface - Standalone Version (No Database Dependencies)
Works entirely with CSV files, includes all features from the enhanced version
"""

import csv
import datetime
import json
import os
from pathlib import Path

# Try to import Flask, provide helpful error if not available
try:
    from flask import Flask, render_template, request, jsonify
    from flask_cors import CORS
except ImportError as e:
    print("=" * 60)
    print("MISSING DEPENDENCIES")
    print("=" * 60)
    print("The web interface requires Flask. Please install it:")
    print()
    print("pip install flask flask-cors")
    print()
    print("Or use the simple desktop version instead:")
    print("python simple_desktop.py")
    print("=" * 60)
    exit(1)

app = Flask(__name__)
CORS(app)

# CSV files
CSV_FILE = "web_time_tracker.csv"
CATEGORIES_FILE = "web_categories.csv"
BUTTONS_FILE = "web_quick_buttons.csv"

# Global variable for current task
current_task = None

def initialize_csv_files():
    """Initialize CSV files if they don't exist"""
    # Main CSV
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['ID', 'Task Description', 'Category', 'Start Time', 'End Time', 'Duration (minutes)', 'Date'])
    
    # Categories CSV
    if not os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'name', 'color'])
            # Add default categories
            writer.writerow([1, 'Work', '#2196F3'])
            writer.writerow([2, 'Personal', '#4CAF50'])
            writer.writerow([3, 'Learning', '#FF9800'])
            writer.writerow([4, 'Other', '#9E9E9E'])
    
    # Quick buttons CSV
    if not os.path.exists(BUTTONS_FILE):
        with open(BUTTONS_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'task_name', 'category_id'])

def read_categories():
    """Read categories from CSV"""
    categories = []
    try:
        with open(CATEGORIES_FILE, 'r', newline='', encoding='utf-8') as file:
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

def read_quick_buttons():
    """Read quick buttons from CSV"""
    buttons = []
    categories = read_categories()
    try:
        with open(BUTTONS_FILE, 'r', newline='', encoding='utf-8') as file:
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

# Initialize CSV files
initialize_csv_files()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/categories')
def get_categories():
    """Get all categories"""
    categories = read_categories()
    return jsonify(categories)

@app.route('/api/categories', methods=['POST'])
def add_category():
    """Add a new category"""
    data = request.get_json()
    name = data.get('name', '').strip()
    color = data.get('color', '#4CAF50')
    
    if not name:
        return jsonify({'error': 'Category name is required'}), 400
    
    # Check if name already exists
    categories = read_categories()
    for cat in categories:
        if cat['name'].lower() == name.lower():
            return jsonify({'error': 'Category name already exists'}), 400
    
    # Get new ID
    new_id = max([cat['id'] for cat in categories], default=0) + 1
    
    # Add to CSV
    with open(CATEGORIES_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([new_id, name, color])
    
    return jsonify({'id': new_id, 'name': name, 'color': color})

@app.route('/api/quick-buttons')
def get_quick_buttons():
    """Get all quick task buttons"""
    buttons = read_quick_buttons()
    return jsonify(buttons)

@app.route('/api/quick-buttons', methods=['POST'])
def add_quick_button():
    """Add a new quick task button"""
    data = request.get_json()
    task_name = data.get('task_name', '').strip()
    category_id = data.get('category_id')
    
    if not task_name:
        return jsonify({'error': 'Task name is required'}), 400
    
    # Get new ID
    buttons = read_quick_buttons()
    new_id = max([btn['id'] for btn in buttons], default=0) + 1
    
    # Add to CSV
    with open(BUTTONS_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([new_id, task_name, category_id if category_id else ''])
    
    return jsonify({'id': new_id, 'task_name': task_name, 'category_id': category_id})

@app.route('/api/tasks/current')
def get_current_task():
    """Get current running task"""
    if current_task:
        # Calculate duration
        start_time = datetime.datetime.fromisoformat(current_task['start_time'])
        duration = datetime.datetime.now() - start_time
        task_dict = current_task.copy()
        task_dict['duration_seconds'] = int(duration.total_seconds())
        return jsonify(task_dict)
    return jsonify(None)

@app.route('/api/tasks/start', methods=['POST'])
def start_task():
    """Start a new task"""
    global current_task
    
    data = request.get_json()
    task_description = data.get('task_description', '').strip()
    category_id = data.get('category_id')
    
    if not task_description:
        return jsonify({'error': 'Task description is required'}), 400
    
    # End current task if any
    if current_task:
        end_time = datetime.datetime.now()
        start_time = datetime.datetime.fromisoformat(current_task['start_time'])
        duration = (end_time - start_time).total_seconds() / 60
        
        # Write completed task to CSV
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                current_task['id'],
                current_task['task_description'],
                current_task.get('category_name', ''),
                start_time.strftime('%Y-%m-%d %H:%M:%S'),
                end_time.strftime('%Y-%m-%d %H:%M:%S'),
                round(duration, 2),
                start_time.strftime('%Y-%m-%d')
            ])
    
    # Start new task
    start_time = datetime.datetime.now()
    category_name = None
    if category_id:
        categories = read_categories()
        for cat in categories:
            if cat['id'] == category_id:
                category_name = cat['name']
                break
    
    current_task = {
        'id': int(start_time.timestamp()),
        'task_description': task_description,
        'category_id': category_id,
        'category_name': category_name,
        'start_time': start_time.isoformat()
    }
    
    return jsonify(current_task)

@app.route('/api/tasks/stop', methods=['POST'])
def stop_task():
    """Stop the current task"""
    global current_task
    
    if not current_task:
        return jsonify({'error': 'No active task to stop'}), 400
    
    end_time = datetime.datetime.now()
    start_time = datetime.datetime.fromisoformat(current_task['start_time'])
    duration = (end_time - start_time).total_seconds() / 60
    
    # Write completed task to CSV
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            current_task['id'],
            current_task['task_description'],
            current_task.get('category_name', ''),
            start_time.strftime('%Y-%m-%d %H:%M:%S'),
            end_time.strftime('%Y-%m-%d %H:%M:%S'),
            round(duration, 2),
            start_time.strftime('%Y-%m-%d')
        ])
    
    result = {
        'task_description': current_task['task_description'],
        'duration_minutes': round(duration, 2),
        'end_time': end_time.isoformat()
    }
    
    current_task = None
    return jsonify(result)

@app.route('/api/tasks/recent')
def get_recent_tasks():
    """Get recent completed tasks"""
    limit = request.args.get('limit', 10, type=int)
    
    tasks = []
    try:
        with open(CSV_FILE, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            # Get the most recent tasks (reverse order)
            for row in reversed(rows[-limit:]):
                if row['End Time']:  # Only completed tasks
                    tasks.append({
                        'id': int(row['ID']) if row['ID'] else 0,
                        'task_description': row['Task Description'],
                        'start_time': row['Start Time'],
                        'end_time': row['End Time'],
                        'duration_minutes': float(row['Duration (minutes)']),
                        'category_name': row.get('Category', '')
                    })
    except Exception as e:
        print(f"Error reading CSV: {e}")
    
    return jsonify(tasks)

@app.route('/api/tasks/by-category/<int:category_id>')
def get_tasks_by_category(category_id):
    """Get tasks filtered by category"""
    # Find category name
    categories = read_categories()
    category_name = None
    for cat in categories:
        if cat['id'] == category_id:
            category_name = cat['name']
            break
    
    if not category_name:
        return jsonify({'error': 'Category not found'}), 404
    
    tasks = []
    try:
        with open(CSV_FILE, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['End Time'] and row['Category'] == category_name:
                    tasks.append({
                        'id': int(row['ID']) if row['ID'] else 0,
                        'task_description': row['Task Description'],
                        'start_time': row['Start Time'],
                        'end_time': row['End Time'],
                        'duration_minutes': float(row['Duration (minutes)']),
                        'category_name': row['Category']
                    })
    except Exception as e:
        print(f"Error reading CSV: {e}")
    
    return jsonify(tasks)

@app.route('/api/tasks/summary')
def get_task_summary():
    """Get task summary by category"""
    summary = {}
    categories = read_categories()
    
    # Initialize categories
    for cat in categories:
        summary[cat['name']] = {
            'total_minutes': 0,
            'task_count': 0,
            'color': cat['color']
        }
    
    try:
        with open(CSV_FILE, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['End Time'] and row['Category']:
                    category = row['Category']
                    if category in summary:
                        summary[category]['total_minutes'] += float(row['Duration (minutes)'])
                        summary[category]['task_count'] += 1
    except Exception as e:
        print(f"Error reading CSV: {e}")
    
    return jsonify(summary)

if __name__ == '__main__':
    print("=" * 60)
    print("TIME TRACKER WEB INTERFACE (Standalone)")
    print("=" * 60)
    print("Starting web server...")
    print("Features: Task tracking, Categories, Quick buttons, Reports")
    print("Storage: CSV files (no database required)")
    print()
    print("Once started, open your browser to:")
    print("http://localhost:5000")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting web server: {e}")
        print("\nMake sure Flask is installed:")
        print("pip install flask flask-cors")