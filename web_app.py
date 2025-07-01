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

# Initialize database
try:
    db = DatabaseManager()
    db.initialize_database()
    print("Web app connected to database successfully")
except Exception as e:
    print(f"Database connection failed: {e}")
    db = None

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/categories')
def get_categories():
    """Get all categories"""
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        categories = db.get_categories()
        return jsonify([dict(cat) for cat in categories])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        buttons = db.get_custom_buttons()
        return jsonify([dict(btn) for btn in buttons])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
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
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/start', methods=['POST'])
def start_task():
    """Start a new task"""
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    data = request.get_json()
    task_description = data.get('task_description', '').strip()
    category_id = data.get('category_id')
    
    if not task_description:
        return jsonify({'error': 'Task description is required'}), 400
    
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
        return jsonify({'error': str(e)}), 500

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