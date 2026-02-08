#!/usr/bin/env python3
"""
Flask web interface for Screentime tracker
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add the screentime package to path
sys.path.insert(0, str(Path(__file__).parent))

from screentime.database import Database
from screentime.utils import format_duration

app = Flask(__name__)
db = Database()


@app.route('/')
def index():
    """Main dashboard page."""
    # Get today's stats
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_data = db.get_stats(start_date, group_by='app')
    
    # Get weekly summary
    weekly_data = db.get_weekly_summary()
    
    # Calculate totals
    today_total = sum(item['duration'] for item in today_data) if today_data else 0
    
    return render_template('index.html', 
                         today_data=today_data,
                         today_total=today_total,
                         weekly_data=weekly_data,
                         format_duration=format_duration)


@app.route('/stats')
def stats():
    """Detailed statistics page."""
    days = request.args.get('days', default=1, type=int)
    group_by = request.args.get('group_by', default='app', type=str)
    
    start_date = datetime.now() - timedelta(days=days)
    data = db.get_stats(start_date, group_by=group_by)
    
    total_time = sum(item['duration'] for item in data) if data else 0
    
    return render_template('stats.html',
                         data=data,
                         total_time=total_time,
                         days=days,
                         group_by=group_by,
                         format_duration=format_duration)


@app.route('/daily')
def daily():
    """Daily breakdown page."""
    date_str = request.args.get('date')
    
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            target_date = datetime.now()
    else:
        target_date = datetime.now()
    
    data = db.get_daily_breakdown(target_date)
    total_time = sum(item['duration'] for item in data) if data else 0
    
    return render_template('daily.html',
                         data=data,
                         total_time=total_time,
                         date=target_date,
                         format_duration=format_duration)


@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics data."""
    days = request.args.get('days', default=7, type=int)
    start_date = datetime.now() - timedelta(days=days)
    data = db.get_stats(start_date, group_by='app')
    
    return jsonify({
        'stats': data,
        'total': sum(item['duration'] for item in data) if data else 0
    })


@app.route('/api/weekly')
def api_weekly():
    """API endpoint for weekly summary."""
    weekly_data = db.get_weekly_summary()
    
    # Format for JSON
    result = []
    for item in weekly_data:
        result.append({
            'date': item['date'].strftime('%Y-%m-%d'),
            'total_duration': item['total_duration']
        })
    
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
