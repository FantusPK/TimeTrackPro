#!/usr/bin/env python3
"""
Web Interface for Enhanced Time Tracker
Provides browser-based access to time tracking functionality
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import datetime
import json
from models import DatabaseManager

app = Flask(__name__)
CORS(app)

# Initialize database with fallback to CSV
db = None
try:
    db = DatabaseManager()
    db.initialize_database()
    print("Web app connected to database successfully")
except Exception as e:
    print(f"Database connection failed: {e}")
    print("Web app will run in CSV-only mode")
    db = None

# CSV fallback for offline mode
import csv
import os
from pathlib import Path

CSV_FILE = "time_tracker.csv"
CATEGORIES_FILE = "categories.csv"
BUTTONS_FILE = "quick_buttons.csv"

def initialize_csv_files():
    """Initialize CSV files if they don't exist"""
    # Initialize main CSV
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Task Description', 'Start Time', 'End Time', 'Duration (minutes)', 'Date', 'Category'])
    
    # Initialize categories CSV
    if not os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'name', 'color'])
            # Add default categories
            writer.writerow([1, 'Work', '#2196F3'])
            writer.writerow([2, 'Personal', '#4CAF50'])
            writer.writerow([3, 'Learning', '#FF9800'])
            writer.writerow([4, 'Other', '#9E9E9E'])
    
    # Initialize buttons CSV
    if not os.path.exists(BUTTONS_FILE):
        with open(BUTTONS_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'task_name', 'category_id'])

# Initialize CSV files for offline mode
initialize_csv_files()

# Global variable for current task (CSV mode)
current_task_csv = None

def read_csv_categories():
    """Read categories from CSV file"""
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
        print(f"Error reading categories CSV: {e}")
    return categories

def read_csv_buttons():
    """Read quick buttons from CSV file"""
    buttons = []
    try:
        with open(BUTTONS_FILE, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Get category name
                category_name = None
                if row['category_id']:
                    categories = read_csv_categories()
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
        print(f"Error reading buttons CSV: {e}")
    return buttons

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/categories')
def get_categories():
    """Get all categories"""
    if db:
        try:
            categories = db.get_categories()
            return jsonify([dict(cat) for cat in categories])
        except Exception as e:
            print(f"Database error, falling back to CSV: {e}")
    
    # Fallback to CSV
    categories = read_csv_categories()
    return jsonify(categories)

@app.route('/api/categories', methods=['POST'])
def add_category():
    """Add a new category"""
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    data = request.get_json()
    name = data.get('name', '').strip()
    color = data.get('color', '#4CAF50')
    
    if not name:
        return jsonify({'error': 'Category name is required'}), 400
    
    try:
        category_id = db.add_category(name, color)
        return jsonify({'id': category_id, 'name': name, 'color': color})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quick-buttons')
def get_quick_buttons():
    """Get all quick task buttons"""
    if db:
        try:
            buttons = db.get_custom_buttons()
            return jsonify([dict(btn) for btn in buttons])
        except Exception as e:
            print(f"Database error, falling back to CSV: {e}")
    
    # Fallback to CSV
    buttons = read_csv_buttons()
    return jsonify(buttons)

@app.route('/api/quick-buttons', methods=['POST'])
def add_quick_button():
    """Add a new quick task button"""
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    data = request.get_json()
    task_name = data.get('task_name', '').strip()
    category_id = data.get('category_id')
    
    if not task_name:
        return jsonify({'error': 'Task name is required'}), 400
    
    try:
        button_id = db.add_custom_button(task_name, category_id)
        return jsonify({'id': button_id, 'task_name': task_name, 'category_id': category_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quick-buttons/<int:button_id>', methods=['DELETE'])
def delete_quick_button(button_id):
    """Delete a quick task button"""
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        db.delete_custom_button(button_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete a category"""
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        db.delete_category(category_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/current')
def get_current_task():
    """Get current running task"""
    if db:
        try:
            task = db.get_last_incomplete_task()
            if task:
                # Calculate duration
                duration = datetime.datetime.now() - task['start_time']
                task_dict = dict(task)
                task_dict['duration_seconds'] = int(duration.total_seconds())
                task_dict['start_time'] = task['start_time'].isoformat()
                return jsonify(task_dict)
            else:
                return jsonify(None)
        except Exception as e:
            print(f"Database error, falling back to CSV: {e}")
    
    # Fallback to CSV mode - return current task if any
    return jsonify(current_task_csv)

@app.route('/api/tasks/start', methods=['POST'])
def start_task():
    """Start a new task"""
    data = request.get_json()
    task_description = data.get('task_description', '').strip()
    category_id = data.get('category_id')
    
    if not task_description:
        return jsonify({'error': 'Task description is required'}), 400
    
    if db:
        try:
            # End any current task
            current_task = db.get_last_incomplete_task()
            if current_task:
                end_time = datetime.datetime.now()
                duration = (end_time - current_task['start_time']).total_seconds() / 60
                db.end_task(current_task['id'], end_time, duration)
            
            # Start new task
            start_time = datetime.datetime.now()
            task_id = db.add_task(task_description, category_id, start_time)
            
            return jsonify({
                'id': task_id,
                'task_description': task_description,
                'category_id': category_id,
                'start_time': start_time.isoformat()
            })
        except Exception as e:
            print(f"Database error, falling back to CSV: {e}")
    
    # Fallback to CSV mode
    global current_task_csv
    
    # End current task if any
    if current_task_csv:
        end_time = datetime.datetime.now()
        start_time = datetime.datetime.fromisoformat(current_task_csv['start_time'])
        duration = (end_time - start_time).total_seconds() / 60
        
        # Write completed task to CSV
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                current_task_csv['task_description'],
                start_time.strftime('%Y-%m-%d %H:%M:%S'),
                end_time.strftime('%Y-%m-%d %H:%M:%S'),
                round(duration, 2),
                start_time.strftime('%Y-%m-%d'),
                current_task_csv.get('category_name', '')
            ])
    
    # Start new task
    start_time = datetime.datetime.now()
    category_name = None
    if category_id:
        categories = read_csv_categories()
        for cat in categories:
            if cat['id'] == category_id:
                category_name = cat['name']
                break
    
    current_task_csv = {
        'id': int(start_time.timestamp()),
        'task_description': task_description,
        'category_id': category_id,
        'category_name': category_name,
        'start_time': start_time.isoformat()
    }
    
    return jsonify(current_task_csv)

@app.route('/api/tasks/stop', methods=['POST'])
def stop_task():
    """Stop the current task"""
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        current_task = db.get_last_incomplete_task()
        if not current_task:
            return jsonify({'error': 'No active task to stop'}), 400
        
        end_time = datetime.datetime.now()
        duration = (end_time - current_task['start_time']).total_seconds() / 60
        db.end_task(current_task['id'], end_time, duration)
        
        return jsonify({
            'success': True,
            'duration_minutes': round(duration, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/recent')
def get_recent_tasks():
    """Get recent completed tasks"""
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    limit = request.args.get('limit', 20, type=int)
    
    try:
        tasks = db.get_recent_tasks(limit)
        result = []
        for task in tasks:
            task_dict = dict(task)
            if task_dict['start_time']:
                task_dict['start_time'] = task_dict['start_time'].isoformat()
            if task_dict['end_time']:
                task_dict['end_time'] = task_dict['end_time'].isoformat()
            result.append(task_dict)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/by-category/<int:category_id>')
def get_tasks_by_category(category_id):
    """Get tasks filtered by category"""
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        tasks = db.get_tasks_by_category(category_id)
        result = []
        for task in tasks:
            task_dict = dict(task)
            if task_dict['start_time']:
                task_dict['start_time'] = task_dict['start_time'].isoformat()
            if task_dict['end_time']:
                task_dict['end_time'] = task_dict['end_time'].isoformat()
            result.append(task_dict)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/summary')
def get_task_summary():
    """Get task summary by category"""
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        summary = db.get_task_summary()
        return jsonify([dict(item) for item in summary])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)