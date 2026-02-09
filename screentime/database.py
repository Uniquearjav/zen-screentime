# File: database.py
# Location: screentime/database.py
"""Database module for storing screen time data."""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class Database:
    """Handle all database operations for screen time tracking."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection."""
        if db_path is None:
            # Store in user's home directory
            db_dir = Path.home() / '.local' / 'share' / 'screentime'
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = db_dir / 'screentime.db'
        
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Create necessary database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Main activity tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                app_name TEXT NOT NULL,
                window_title TEXT,
                duration INTEGER NOT NULL,
                date DATE NOT NULL
            )
        ''')
        
        # Index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_date 
            ON activity(date)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_app_name 
            ON activity(app_name)
        ''')
        
        self.conn.commit()
    
    def record_activity(self, app_name: str, window_title: str, duration: int):
        """Record a window activity entry."""
        cursor = self.conn.cursor()
        timestamp = datetime.now()
        date = timestamp.date()
        
        cursor.execute('''
            INSERT INTO activity (timestamp, app_name, window_title, duration, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, app_name, window_title, duration, date))
        
        self.conn.commit()
    
    def get_stats(self, start_date: datetime, group_by: str = 'app') -> List[Dict]:
        """Get aggregated statistics since start_date."""
        cursor = self.conn.cursor()
        
        if group_by == 'app':
            query = '''
                SELECT app_name, SUM(duration) as duration
                FROM activity
                WHERE timestamp >= ?
                GROUP BY app_name
                ORDER BY duration DESC
            '''
        else:  # window
            query = '''
                SELECT app_name, window_title, SUM(duration) as duration
                FROM activity
                WHERE timestamp >= ?
                GROUP BY app_name, window_title
                ORDER BY duration DESC
            '''
        
        cursor.execute(query, (start_date,))
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            item = {
                'app_name': row['app_name'],
                'duration': row['duration']
            }
            if group_by == 'window':
                item['window_title'] = row['window_title']
            result.append(item)
        
        return result
    
    def get_daily_breakdown(self, target_date: datetime) -> List[Dict]:
        """Get breakdown for a specific day."""
        cursor = self.conn.cursor()
        date = target_date.date()
        
        cursor.execute('''
            SELECT app_name, SUM(duration) as duration
            FROM activity
            WHERE date = ?
            GROUP BY app_name
            ORDER BY duration DESC
        ''', (date,))
        
        rows = cursor.fetchall()
        return [{'app_name': row['app_name'], 'duration': row['duration']} for row in rows]
    
    def get_weekly_summary(self) -> List[Dict]:
        """Get daily totals for the past 7 days."""
        cursor = self.conn.cursor()
        start_date = (datetime.now() - timedelta(days=7)).date()
        
        cursor.execute('''
            SELECT date, SUM(duration) as total_duration
            FROM activity
            WHERE date >= ?
            GROUP BY date
            ORDER BY date DESC
        ''', (start_date,))
        
        rows = cursor.fetchall()
        result = []
        for row in rows:
            result.append({
                'date': datetime.strptime(row['date'], '%Y-%m-%d'),
                'total_duration': row['total_duration']
            })
        
        return result
    
    def reset(self):
        """Delete all recorded data."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM activity')
        self.conn.commit()
    
    def close(self):
        """Close database connection."""
        self.conn.close()
