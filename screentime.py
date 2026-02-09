#!/usr/bin/env python3
"""
Screentime - A CLI application to track screen time on Arch Linux
Supports both X11 and Wayland
"""

import click
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the screentime package to path
sys.path.insert(0, str(Path(__file__).parent))

from screentime.database import Database
from screentime.tracker import ScreenTimeTracker
from screentime.utils import format_duration, format_stats


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Track and analyze your screen time on Arch Linux."""
    pass


@cli.command()
@click.option('--interval', default=5, help='Update interval in seconds (default: 5)')
@click.option('--daemon', is_flag=True, help='Run as daemon in background')
def start(interval, daemon):
    """Start tracking screen time."""
    db = Database()
    tracker = ScreenTimeTracker(db, interval)
    
    if daemon:
        click.echo("Starting screentime tracker in background...")
        tracker.start_daemon()
    else:
        click.echo(f"Starting screentime tracker (interval: {interval}s)")
        click.echo("Press Ctrl+C to stop")
        try:
            tracker.start()
        except KeyboardInterrupt:
            click.echo("\nTracker stopped.")
            sys.exit(0)


@cli.command()
def stop():
    """Stop the background tracker daemon."""
    tracker = ScreenTimeTracker(Database())
    if tracker.stop_daemon():
        click.echo("Tracker stopped.")
    else:
        click.echo("No tracker daemon running.")


@cli.command()
@click.option('--days', default=1, help='Number of days to show (default: 1 for today)')
@click.option('--group-by', type=click.Choice(['app', 'window']), default='app', 
              help='Group statistics by application or window title')
def stats(days, group_by):
    """Show screen time statistics."""
    db = Database()
    
    if days == 1:
        click.echo("=== Today's Screen Time ===\n")
        # Start from midnight today, not 24 hours ago
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        click.echo(f"=== Screen Time (Last {days} days) ===\n")
        start_date = datetime.now() - timedelta(days=days)
    
    data = db.get_stats(start_date, group_by=group_by)
    
    if not data:
        click.echo("No data recorded yet. Start tracking with 'screentime start'")
        return
    
    total_time = sum(item['duration'] for item in data)
    
    click.echo(f"Total screen time: {format_duration(total_time)}\n")
    click.echo(format_stats(data, group_by))


@cli.command()
@click.option('--date', help='Date to show (YYYY-MM-DD format)')
def daily(date):
    """Show daily screen time breakdown."""
    db = Database()
    
    if date:
        try:
            target_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            click.echo("Invalid date format. Use YYYY-MM-DD")
            return
    else:
        target_date = datetime.now()
    
    click.echo(f"=== Screen Time for {target_date.strftime('%Y-%m-%d')} ===\n")
    
    data = db.get_daily_breakdown(target_date)
    
    if not data:
        click.echo("No data recorded for this date.")
        return
    
    total_time = sum(item['duration'] for item in data)
    click.echo(f"Total: {format_duration(total_time)}\n")
    
    for item in data[:10]:  # Top 10
        app_name = item['app_name']
        duration = format_duration(item['duration'])
        percentage = (item['duration'] / total_time) * 100 if total_time > 0 else 0
        
        bar_width = 30
        filled = int((item['duration'] / total_time) * bar_width) if total_time > 0 else 0
        bar = '█' * filled + '░' * (bar_width - filled)
        
        click.echo(f"{app_name:<30} {bar} {duration:>12} ({percentage:>5.1f}%)")


@cli.command()
def week():
    """Show weekly screen time summary."""
    db = Database()
    
    click.echo("=== Weekly Screen Time Summary ===\n")
    
    weekly_data = db.get_weekly_summary()
    
    if not weekly_data:
        click.echo("No data recorded yet.")
        return
    
    for day_data in weekly_data:
        date_str = day_data['date'].strftime('%a %Y-%m-%d')
        duration = format_duration(day_data['total_duration'])
        click.echo(f"{date_str}: {duration}")
    
    total_week = sum(d['total_duration'] for d in weekly_data)
    avg_day = total_week / len(weekly_data) if weekly_data else 0
    
    click.echo(f"\nTotal: {format_duration(total_week)}")
    click.echo(f"Daily average: {format_duration(avg_day)}")


@cli.command()
def status():
    """Check if tracker is running."""
    tracker = ScreenTimeTracker(Database())
    if tracker.is_running():
        click.echo("✓ Tracker is running")
    else:
        click.echo("✗ Tracker is not running")


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to reset all data?')
def reset():
    """Reset all tracked data (destructive!)."""
    db = Database()
    db.reset()
    click.echo("All data has been reset.")


@cli.group()
def blocklist():
    """Manage blocklist of apps to ignore."""
    pass


@blocklist.command('add')
@click.argument('app_name')
def blocklist_add(app_name):
    """Add an app to the blocklist."""
    db = Database()
    if db.add_to_blocklist(app_name):
        click.echo(f"✓ Added '{app_name}' to blocklist")
    else:
        click.echo(f"'{app_name}' is already in blocklist")
    db.close()


@blocklist.command('remove')
@click.argument('app_name')
def blocklist_remove(app_name):
    """Remove an app from the blocklist."""
    db = Database()
    if db.remove_from_blocklist(app_name):
        click.echo(f"✓ Removed '{app_name}' from blocklist")
    else:
        click.echo(f"'{app_name}' is not in blocklist")
    db.close()


@blocklist.command('list')
def blocklist_list():
    """List all blocked apps."""
    db = Database()
    blocked_apps = db.get_blocklist()
    
    if not blocked_apps:
        click.echo("No apps in blocklist")
    else:
        click.echo(f"\\n=== Blocked Apps ({len(blocked_apps)}) ===\\n")
        for item in blocked_apps:
            added_date = datetime.fromisoformat(item['added_date']).strftime('%Y-%m-%d')
            click.echo(f"  • {item['app_name']:<30} (added: {added_date})")
    
    db.close()


@blocklist.command('clear')
@click.confirmation_option(prompt='Are you sure you want to clear the blocklist?')
def blocklist_clear():
    """Clear all apps from blocklist."""
    db = Database()
    cursor = db.conn.cursor()
    cursor.execute('DELETE FROM blocklist')
    db.conn.commit()
    count = cursor.rowcount
    click.echo(f"Removed {count} apps from blocklist")
    db.close()


if __name__ == '__main__':
    cli()
