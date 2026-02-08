"""Utility functions for screentime app."""

from typing import List, Dict


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m {seconds % 60}s"
    
    hours = minutes // 60
    minutes = minutes % 60
    
    if hours < 24:
        return f"{hours}h {minutes}m"
    
    days = hours // 24
    hours = hours % 24
    return f"{days}d {hours}h {minutes}m"


def format_stats(data: List[Dict], group_by: str = 'app') -> str:
    """Format statistics data for display."""
    if not data:
        return "No data available."
    
    lines = []
    total_duration = sum(item['duration'] for item in data)
    
    # Header
    if group_by == 'app':
        lines.append(f"{'Application':<30} {'Duration':>15} {'Percentage':>12}")
    else:
        lines.append(f"{'Application':<20} {'Window':<30} {'Duration':>15} {'Percentage':>12}")
    
    lines.append("=" * 80)
    
    # Data rows (limit to top 20)
    for item in data[:20]:
        duration_str = format_duration(item['duration'])
        percentage = (item['duration'] / total_duration * 100) if total_duration > 0 else 0
        percentage_str = f"{percentage:.1f}%"
        
        if group_by == 'app':
            app_name = item['app_name'][:29]  # Truncate if too long
            lines.append(f"{app_name:<30} {duration_str:>15} {percentage_str:>12}")
        else:
            app_name = item['app_name'][:19]
            window_title = item.get('window_title', 'Unknown')[:29]
            lines.append(f"{app_name:<20} {window_title:<30} {duration_str:>15} {percentage_str:>12}")
    
    if len(data) > 20:
        lines.append(f"\n... and {len(data) - 20} more")
    
    return "\n".join(lines)
