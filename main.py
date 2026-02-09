#!/usr/bin/env python3
# File: main.py
# Location: main.py
"""
GTK4 GUI alternative for Screentime tracker
For users who prefer GTK over Qt
"""

import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
from pathlib import Path
from datetime import datetime, timedelta
import threading
import time

# Add the screentime package to path
sys.path.insert(0, str(Path(__file__).parent))

from screentime.database import Database
from screentime.tracker import ScreenTimeTracker
from screentime.utils import format_duration


class TrackerThread(threading.Thread):
    """Background thread for tracking."""
    
    def __init__(self, db, callback, interval=5):
        super().__init__(daemon=True)
        self.tracker = ScreenTimeTracker(db, interval)
        self.callback = callback
        self.running = False
    
    def run(self):
        self.running = True
        last_window = None
        last_check = None
        
        while self.running:
            current_time = time.time()
            window_info = self.tracker.get_active_window()
            
            if window_info:
                app_name, window_title = window_info
                GLib.idle_add(self.callback, app_name, window_title)
                
                if last_window == window_info and last_check:
                    duration = int(current_time - last_check)
                    if duration > 0:
                        self.tracker.db.record_activity(app_name, window_title, duration)
                
                last_window = window_info
            
            last_check = current_time
            time.sleep(self.tracker.interval)
    
    def stop(self):
        self.running = False


class AppListRow(Gtk.ListBoxRow):
    """Custom row for application list."""
    
    def __init__(self, app_name, duration, percentage):
        super().__init__()
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.set_margin_start(10)
        box.set_margin_end(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        # Top row
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        app_label = Gtk.Label(label=app_name)
        app_label.set_halign(Gtk.Align.START)
        app_label.add_css_class('heading')
        
        duration_label = Gtk.Label(label=format_duration(duration))
        duration_label.set_halign(Gtk.Align.END)
        duration_label.add_css_class('accent')
        
        top_box.append(app_label)
        top_box.append(Gtk.Box())  # Spacer
        top_box.set_hexpand(True)
        top_box.append(duration_label)
        
        # Progress bar
        progress = Gtk.ProgressBar()
        progress.set_fraction(percentage / 100.0)
        progress.add_css_class('osd')
        
        box.append(top_box)
        box.append(progress)
        
        self.set_child(box)


class ScreentimeWindow(Adw.ApplicationWindow):
    """Main application window."""
    
    def __init__(self, app, db):
        super().__init__(application=app)
        self.db = db
        self.tracker_thread = None
        self.tracking = False
        
        self.set_title("Screentime Tracker")
        self.set_default_size(900, 650)
        
        self.setup_ui()
        self.load_data()
        
        # Auto-refresh timer
        GLib.timeout_add_seconds(60, self.on_refresh_timer)
    
    def setup_ui(self):
        """Setup the user interface."""
        
        # Header bar
        header = Adw.HeaderBar()
        
        # Track button
        self.track_button = Gtk.Button(label="▶ Start Tracking")
        self.track_button.add_css_class('suggested-action')
        self.track_button.connect('clicked', self.on_track_clicked)
        header.pack_end(self.track_button)
        
        # Status label
        self.status_label = Gtk.Label(label="⭕ Not tracking")
        header.pack_end(self.status_label)
        
        # Main content
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Tab view
        self.tab_view = Adw.TabView()
        tab_bar = Adw.TabBar(view=self.tab_view)
        
        main_box.append(header)
        main_box.append(tab_bar)
        main_box.append(self.tab_view)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_stats_tab()
        self.create_daily_tab()
        
        self.set_content(main_box)
    
    def create_dashboard_tab(self):
        """Create dashboard tab."""
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        
        # Stats cards
        stats_box = Gtk.Box(spacing=20)
        
        # Total time card
        self.today_total_label = Gtk.Label(label="0h 0m")
        self.today_total_label.add_css_class('title-1')
        total_card = self.create_stat_card("Total Screen Time", self.today_total_label)
        
        # Apps count card
        self.today_apps_label = Gtk.Label(label="0")
        self.today_apps_label.add_css_class('title-1')
        apps_card = self.create_stat_card("Applications Used", self.today_apps_label)
        
        stats_box.append(total_card)
        stats_box.append(apps_card)
        stats_box.set_homogeneous(True)
        
        # App list
        list_label = Gtk.Label(label="🎯 Top Applications Today")
        list_label.set_halign(Gtk.Align.START)
        list_label.add_css_class('title-2')
        
        self.today_list = Gtk.ListBox()
        self.today_list.add_css_class('boxed-list')
        
        box.append(stats_box)
        box.append(list_label)
        box.append(self.today_list)
        
        scroll.set_child(box)
        
        page = self.tab_view.append(scroll)
        page.set_title("Dashboard")
        page.set_icon(Gio.ThemedIcon.new("view-grid-symbolic"))
    
    def create_stats_tab(self):
        """Create statistics tab."""
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        
        # Filters
        filter_box = Gtk.Box(spacing=10)
        
        filter_box.append(Gtk.Label(label="Time Period:"))
        self.stats_days_combo = Gtk.DropDown.new_from_strings(
            ["Today", "Last 7 days", "Last 30 days", "Last 90 days"]
        )
        self.stats_days_combo.connect('notify::selected', lambda *_: self.load_stats_data())
        filter_box.append(self.stats_days_combo)
        
        filter_box.append(Gtk.Label(label="Group By:"))
        self.stats_group_combo = Gtk.DropDown.new_from_strings(
            ["Application", "Window Title"]
        )
        self.stats_group_combo.connect('notify::selected', lambda *_: self.load_stats_data())
        filter_box.append(self.stats_group_combo)
        
        # Total time
        self.stats_total_label = Gtk.Label(label="0h 0m")
        self.stats_total_label.add_css_class('title-1')
        total_card = self.create_stat_card("Total Screen Time", self.stats_total_label)
        
        # App list
        self.stats_list = Gtk.ListBox()
        self.stats_list.add_css_class('boxed-list')
        
        box.append(filter_box)
        box.append(total_card)
        box.append(self.stats_list)
        
        scroll.set_child(box)
        
        page = self.tab_view.append(scroll)
        page.set_title("Statistics")
        page.set_icon(Gio.ThemedIcon.new("view-list-symbolic"))
    
    def create_daily_tab(self):
        """Create daily view tab."""
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        
        # Date selector (simplified - GTK4 doesn't have a built-in date picker)
        date_box = Gtk.Box(spacing=10)
        date_box.append(Gtk.Label(label="Daily View"))
        
        today_button = Gtk.Button(label="Today")
        today_button.connect('clicked', lambda *_: self.load_daily_data())
        date_box.append(today_button)
        
        # Total time
        self.daily_total_label = Gtk.Label(label="0h 0m")
        self.daily_total_label.add_css_class('title-1')
        total_card = self.create_stat_card("Total Time", self.daily_total_label)
        
        # App list
        self.daily_list = Gtk.ListBox()
        self.daily_list.add_css_class('boxed-list')
        
        box.append(date_box)
        box.append(total_card)
        box.append(self.daily_list)
        
        scroll.set_child(box)
        
        page = self.tab_view.append(scroll)
        page.set_title("Daily View")
        page.set_icon(Gio.ThemedIcon.new("view-calendar-symbolic"))
    
    def create_stat_card(self, title, value_widget):
        """Create a statistic card."""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.set_margin_start(20)
        card.set_margin_end(20)
        card.set_margin_top(20)
        card.set_margin_bottom(20)
        
        title_label = Gtk.Label(label=title)
        title_label.add_css_class('title-4')
        
        card.append(title_label)
        card.append(value_widget)
        
        frame = Gtk.Frame()
        frame.set_child(card)
        
        return frame
    
    def on_track_clicked(self, button):
        """Handle track button click."""
        if not self.tracking:
            self.start_tracking()
        else:
            self.stop_tracking()
    
    def start_tracking(self):
        """Start tracking."""
        if self.tracker_thread is None:
            self.tracker_thread = TrackerThread(self.db, self.update_status)
        
        self.tracker_thread.start()
        self.tracking = True
        self.track_button.set_label("⏹ Stop Tracking")
        self.status_label.set_label("🟢 Tracking active")
    
    def stop_tracking(self):
        """Stop tracking."""
        if self.tracker_thread:
            self.tracker_thread.stop()
            self.tracker_thread = None
        
        self.tracking = False
        self.track_button.set_label("▶ Start Tracking")
        self.status_label.set_label("⭕ Not tracking")
    
    def update_status(self, app_name, window_title):
        """Update status label."""
        short_title = window_title[:40] + "..." if len(window_title) > 40 else window_title
        self.status_label.set_label(f"🟢 {app_name} - {short_title}")
        return False
    
    def load_data(self):
        """Load all data."""
        self.load_dashboard_data()
        self.load_stats_data()
        self.load_daily_data()
    
    def load_dashboard_data(self):
        """Load dashboard data."""
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_data = self.db.get_stats(start_date, group_by='app')
        
        today_total = sum(item['duration'] for item in today_data) if today_data else 0
        self.today_total_label.set_label(format_duration(today_total))
        self.today_apps_label.set_label(str(len(today_data)))
        
        # Clear and populate list
        while True:
            row = self.today_list.get_row_at_index(0)
            if row is None:
                break
            self.today_list.remove(row)
        
        for item in today_data[:10]:
            percentage = (item['duration'] / today_total * 100) if today_total > 0 else 0
            row = AppListRow(item['app_name'], item['duration'], percentage)
            self.today_list.append(row)
    
    def load_stats_data(self):
        """Load stats data."""
        days_map = [0, 7, 30, 90]
        days = days_map[self.stats_days_combo.get_selected()]
        
        group_by = 'app' if self.stats_group_combo.get_selected() == 0 else 'window'
        
        start_date = datetime.now() - timedelta(days=days)
        data = self.db.get_stats(start_date, group_by=group_by)
        
        total_time = sum(item['duration'] for item in data) if data else 0
        self.stats_total_label.set_label(format_duration(total_time))
        
        # Clear and populate list
        while True:
            row = self.stats_list.get_row_at_index(0)
            if row is None:
                break
            self.stats_list.remove(row)
        
        for item in data:
            percentage = (item['duration'] / total_time * 100) if total_time > 0 else 0
            
            display_name = item['app_name']
            if group_by == 'window' and item.get('window_title'):
                display_name += f" - {item['window_title']}"
            
            row = AppListRow(display_name, item['duration'], percentage)
            self.stats_list.append(row)
    
    def load_daily_data(self):
        """Load daily data."""
        target_date = datetime.now()
        data = self.db.get_daily_breakdown(target_date)
        
        total_time = sum(item['duration'] for item in data) if data else 0
        self.daily_total_label.set_label(format_duration(total_time))
        
        # Clear and populate list
        while True:
            row = self.daily_list.get_row_at_index(0)
            if row is None:
                break
            self.daily_list.remove(row)
        
        for item in data:
            percentage = (item['duration'] / total_time * 100) if total_time > 0 else 0
            row = AppListRow(item['app_name'], item['duration'], percentage)
            self.daily_list.append(row)
    
    def on_refresh_timer(self):
        """Auto-refresh callback."""
        self.load_data()
        return True


class ScreentimeApp(Adw.Application):
    """Main application class."""
    
    def __init__(self):
        super().__init__(application_id='com.screentime.tracker')
        self.db = Database()
    
    def do_activate(self):
        """Activate the application."""
        win = self.get_active_window()
        if not win:
            win = ScreentimeWindow(self, self.db)
        win.present()


def main():
    """Main entry point."""
    app = ScreentimeApp()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
