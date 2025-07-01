#!/usr/bin/env python3
"""
Database models for Time Tracker Application
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import json

class DatabaseManager:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
    def get_connection(self):
        """Get a database connection"""
        return psycopg2.connect(self.database_url)
    
    def initialize_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create categories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    color VARCHAR(7) DEFAULT '#4CAF50',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create custom_buttons table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS custom_buttons (
                    id SERIAL PRIMARY KEY,
                    task_name VARCHAR(200) NOT NULL,
                    category_id INTEGER REFERENCES categories(id),
                    button_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    task_description TEXT NOT NULL,
                    category_id INTEGER REFERENCES categories(id),
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_minutes DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default categories if they don't exist
            cursor.execute("""
                INSERT INTO categories (name, color) 
                VALUES ('Work', '#2196F3'), ('Personal', '#4CAF50'), ('Learning', '#FF9800'), ('Other', '#9E9E9E')
                ON CONFLICT (name) DO NOTHING
            """)
            
            conn.commit()
            print("Database initialized successfully")
            
        except Exception as e:
            conn.rollback()
            print(f"Error initializing database: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_categories(self):
        """Get all categories"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("SELECT * FROM categories ORDER BY name")
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
    
    def add_category(self, name, color='#4CAF50'):
        """Add a new category"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO categories (name, color) VALUES (%s, %s) RETURNING id",
                (name, color)
            )
            category_id = cursor.fetchone()[0]
            conn.commit()
            return category_id
        except psycopg2.IntegrityError:
            conn.rollback()
            raise ValueError(f"Category '{name}' already exists")
        finally:
            cursor.close()
            conn.close()
    
    def get_custom_buttons(self):
        """Get all custom buttons with category info"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("""
                SELECT cb.*, c.name as category_name, c.color as category_color
                FROM custom_buttons cb
                LEFT JOIN categories c ON cb.category_id = c.id
                ORDER BY cb.button_order, cb.task_name
            """)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
    
    def add_custom_button(self, task_name, category_id=None):
        """Add a new custom button"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get next order
            cursor.execute("SELECT COALESCE(MAX(button_order), 0) + 1 FROM custom_buttons")
            next_order = cursor.fetchone()[0]
            
            cursor.execute(
                "INSERT INTO custom_buttons (task_name, category_id, button_order) VALUES (%s, %s, %s) RETURNING id",
                (task_name, category_id, next_order)
            )
            button_id = cursor.fetchone()[0]
            conn.commit()
            return button_id
        finally:
            cursor.close()
            conn.close()
    
    def delete_custom_button(self, button_id):
        """Delete a custom button"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM custom_buttons WHERE id = %s", (button_id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    
    def add_task(self, task_description, category_id, start_time):
        """Add a new task to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO tasks (task_description, category_id, start_time) VALUES (%s, %s, %s) RETURNING id",
                (task_description, category_id, start_time)
            )
            task_id = cursor.fetchone()[0]
            conn.commit()
            return task_id
        finally:
            cursor.close()
            conn.close()
    
    def end_task(self, task_id, end_time, duration_minutes):
        """End a task by updating end time and duration"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE tasks SET end_time = %s, duration_minutes = %s WHERE id = %s",
                (end_time, duration_minutes, task_id)
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    
    def get_recent_tasks(self, limit=10):
        """Get recent completed tasks"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("""
                SELECT t.*, c.name as category_name, c.color as category_color
                FROM tasks t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.end_time IS NOT NULL
                ORDER BY t.end_time DESC
                LIMIT %s
            """, (limit,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
    
    def get_tasks_by_category(self, category_id, start_date=None, end_date=None):
        """Get tasks filtered by category and date range"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            query = """
                SELECT t.*, c.name as category_name, c.color as category_color
                FROM tasks t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.category_id = %s AND t.end_time IS NOT NULL
            """
            params = [category_id]
            
            if start_date:
                query += " AND t.start_time >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND t.start_time <= %s"
                params.append(end_date)
            
            query += " ORDER BY t.start_time DESC"
            
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
    
    def get_last_incomplete_task(self):
        """Get the most recent task that hasn't been completed (no end_time)"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("""
                SELECT t.*, c.name as category_name, c.color as category_color
                FROM tasks t
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.end_time IS NULL
                ORDER BY t.start_time DESC
                LIMIT 1
            """)
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()
    
    def get_task_summary(self, start_date=None, end_date=None):
        """Get task summary grouped by category"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            query = """
                SELECT 
                    c.name as category_name,
                    c.color as category_color,
                    COUNT(t.id) as task_count,
                    COALESCE(SUM(t.duration_minutes), 0) as total_minutes
                FROM categories c
                LEFT JOIN tasks t ON c.id = t.category_id AND t.end_time IS NOT NULL
            """
            params = []
            
            if start_date:
                query += " AND t.start_time >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND t.start_time <= %s"
                params.append(end_date)
            
            query += " GROUP BY c.id, c.name, c.color ORDER BY total_minutes DESC"
            
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()