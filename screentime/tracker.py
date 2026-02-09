# File: tracker.py
# Location: screentime/tracker.py
"""Screen time tracking module."""

import os
import time
import signal
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime


class ScreenTimeTracker:
    """Track active window and application usage."""
    
    def __init__(self, database, interval: int = 5):
        """Initialize tracker with database and update interval."""
        self.db = database
        self.interval = interval
        self.pid_file = Path.home() / '.local' / 'share' / 'screentime' / 'tracker.pid'
        self.last_window = None
        self.last_check = None
    
    def _detect_session_type(self) -> str:
        """Detect if running X11 or Wayland."""
        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        
        if session_type == 'wayland':
            return 'wayland'
        elif session_type == 'x11' or os.environ.get('DISPLAY'):
            return 'x11'
        else:
            # Try to detect based on available commands
            if self._command_exists('swaymsg'):
                return 'wayland'
            elif self._command_exists('xdotool'):
                return 'x11'
            else:
                return 'unknown'
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        return subprocess.run(
            ['which', command],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ).returncode == 0
    
    def _get_active_window_x11(self) -> Optional[Tuple[str, str]]:
        """Get active window info using X11 tools."""
        try:
            # Get active window ID
            result = subprocess.run(
                ['xdotool', 'getactivewindow'],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if result.returncode != 0:
                return None
            
            window_id = result.stdout.strip()
            
            # Get window title
            result = subprocess.run(
                ['xdotool', 'getwindowname', window_id],
                capture_output=True,
                text=True,
                timeout=1
            )
            window_title = result.stdout.strip() if result.returncode == 0 else 'Unknown'
            
            # Get window class (application name)
            result = subprocess.run(
                ['xprop', '-id', window_id, 'WM_CLASS'],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if result.returncode == 0:
                # Parse WM_CLASS output: WM_CLASS(STRING) = "instance", "class"
                output = result.stdout.strip()
                if '=' in output:
                    class_info = output.split('=')[1].strip()
                    # Extract the second value (class name)
                    parts = class_info.split(',')
                    if len(parts) >= 2:
                        app_name = parts[1].strip().strip('"')
                    else:
                        app_name = parts[0].strip().strip('"')
                else:
                    app_name = 'Unknown'
            else:
                app_name = 'Unknown'
            
            return (app_name, window_title)
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            return None
    
    def _get_active_window_wayland(self) -> Optional[Tuple[str, str]]:
        """Get active window info using Wayland tools."""
        try:
            # Try swaymsg for Sway compositor
            if self._command_exists('swaymsg'):
                result = subprocess.run(
                    ['swaymsg', '-t', 'get_tree'],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                
                if result.returncode == 0:
                    import json
                    tree = json.loads(result.stdout)
                    focused = self._find_focused_window(tree)
                    
                    if focused:
                        app_name = focused.get('app_id') or focused.get('window_properties', {}).get('class', 'Unknown')
                        window_title = focused.get('name', 'Unknown')
                        return (app_name, window_title)
            
            # Try hyprctl for Hyprland compositor
            elif self._command_exists('hyprctl'):
                result = subprocess.run(
                    ['hyprctl', 'activewindow', '-j'],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                
                if result.returncode == 0:
                    import json
                    window = json.loads(result.stdout)
                    app_name = window.get('class', 'Unknown')
                    window_title = window.get('title', 'Unknown')
                    return (app_name, window_title)
            
            return None
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, Exception):
            return None
    
    def _find_focused_window(self, node: dict) -> Optional[dict]:
        """Recursively find the focused window in Sway tree."""
        if node.get('focused'):
            return node
        
        for child in node.get('nodes', []) + node.get('floating_nodes', []):
            result = self._find_focused_window(child)
            if result:
                return result
        
        return None
    
    def get_active_window(self) -> Optional[Tuple[str, str]]:
        """Get currently active window info (app_name, window_title)."""
        session_type = self._detect_session_type()
        
        if session_type == 'x11':
            return self._get_active_window_x11()
        elif session_type == 'wayland':
            return self._get_active_window_wayland()
        else:
            return None
    
    def start(self):
        """Start tracking in foreground."""
        print(f"Session type: {self._detect_session_type()}")
        
        while True:
            current_time = time.time()
            window_info = self.get_active_window()
            
            if window_info:
                app_name, window_title = window_info
                
                # If same window as before, record the time spent
                if self.last_window == window_info and self.last_check:
                    duration = int(current_time - self.last_check)
                    if duration > 0:
                        self.db.record_activity(app_name, window_title, duration)
                
                self.last_window = window_info
            
            self.last_check = current_time
            time.sleep(self.interval)
    
    def start_daemon(self):
        """Start tracking as a background daemon."""
        # Create PID file directory
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if already running
        if self.is_running():
            print("Tracker is already running!")
            return
        
        # Fork process
        pid = os.fork()
        
        if pid > 0:
            # Parent process - write PID and exit
            with open(self.pid_file, 'w') as f:
                f.write(str(pid))
            return
        
        # Child process - become session leader
        os.setsid()
        
        # Fork again to prevent zombie
        pid = os.fork()
        if pid > 0:
            os._exit(0)
        
        # Redirect standard file descriptors
        with open('/dev/null', 'r') as devnull:
            os.dup2(devnull.fileno(), 0)
        
        log_file = self.pid_file.parent / 'tracker.log'
        with open(log_file, 'a') as log:
            os.dup2(log.fileno(), 1)
            os.dup2(log.fileno(), 2)
        
        # Start tracking
        self.start()
    
    def stop_daemon(self) -> bool:
        """Stop the background daemon."""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Send SIGTERM
            os.kill(pid, signal.SIGTERM)
            
            # Wait a bit and check if stopped
            time.sleep(1)
            
            try:
                # Check if process still exists
                os.kill(pid, 0)
                # If we get here, process still exists, force kill
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                # Process is gone, good
                pass
            
            # Remove PID file
            self.pid_file.unlink()
            return True
            
        except (FileNotFoundError, ValueError, ProcessLookupError):
            # PID file exists but process is gone, clean up
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False
    
    def is_running(self) -> bool:
        """Check if tracker daemon is running."""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process exists
            os.kill(pid, 0)
            return True
            
        except (FileNotFoundError, ValueError, ProcessLookupError):
            # PID file exists but process is gone, clean up
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False
