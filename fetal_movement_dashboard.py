import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import re
import numpy as np
import os
from datetime import datetime as dt

class FetalMovementAnalyzer:
    def __init__(self):
        self.movements = []
        self.stats = {}
        
    def parse_time(self, time_str):
        """Parse various time formats into datetime objects"""
        time_str = time_str.strip().replace('*', '')
        
        # Handle 12-hour format (4pm, 5:30am, etc.)
        if 'pm' in time_str.lower() or 'am' in time_str.lower():
            clean_time = time_str.lower().replace('pm', '').replace('am', '').strip()
            is_pm = 'pm' in time_str.lower()
            
            if ':' in clean_time:
                hours, minutes = clean_time.split(':')
            else:
                hours, minutes = clean_time, '00'
                
            hour = int(hours)
            minute = int(minutes)
            
            # Convert to 24-hour format
            if is_pm and hour != 12:
                hour += 12
            elif not is_pm and hour == 12:
                hour = 0
                
        # Handle 24-hour format (16:30, 23:45, etc.)
        else:
            if ':' in time_str:
                hours, minutes = time_str.split(':')
            else:
                hours, minutes = time_str, '00'
            hour = int(hours)
            minute = int(minutes)
            
        return datetime(2024, 1, 1, hour, minute)
    
    def analyze_movements(self, raw_data):
        """Analyze movement detection data and calculate comprehensive statistics"""
        print("🔍 Analyzing fetal movement detections...")
        
        # Parse movement detection times
        times = [t.strip() for t in raw_data.split(',') if t.strip()]
        self.movements = []
        
        for i, time_str in enumerate(times):
            try:
                parsed_time = self.parse_time(time_str)
                self.movements.append({
                    'id': i + 1,
                    'original': time_str,
                    'datetime': parsed_time,
                    'hour': parsed_time.hour,
                    'minute': parsed_time.minute,
                    'time_str': f"{parsed_time.hour:02d}:{parsed_time.minute:02d}",
                    'hour_decimal': parsed_time.hour + parsed_time.minute/60
                })
            except Exception as e:
                print(f"⚠️ Warning: Could not parse time '{time_str}': {e}")
        
        # Sort by time
        self.movements.sort(key=lambda x: x['datetime'])
        
        # Calculate intervals between detections
        intervals = []
        for i in range(1, len(self.movements)):
            interval_minutes = (self.movements[i]['datetime'] - self.movements[i-1]['datetime']).total_seconds() / 60
            # Handle day rollover
            if interval_minutes < 0:
                interval_minutes += 24 * 60
            
            status = 'concern' if interval_minutes > 120 else 'monitor' if interval_minutes > 60 else 'normal'
            intervals.append({
                'id': i,
                'from_time': self.movements[i-1]['time_str'],
                'to_time': self.movements[i]['time_str'],
                'interval': round(interval_minutes),
                'status': status,
                'from_original': self.movements[i-1]['original'],
                'to_original': self.movements[i]['original']
            })
        
        # Calculate hourly distribution of detections
        hourly_counts = {hour: 0 for hour in range(24)}
        for movement in self.movements:
            hourly_counts[movement['hour']] += 1
            
        # Calculate comprehensive statistics
        total_detections = len(self.movements)
        avg_interval = np.mean([i['interval'] for i in intervals]) if intervals else 0
        max_interval = max([i['interval'] for i in intervals]) if intervals else 0
        min_interval = min([i['interval'] for i in intervals]) if intervals else 0
        concern_intervals = len([i for i in intervals if i['status'] == 'concern'])
        monitor_intervals = len([i for i in intervals if i['status'] == 'monitor'])
        normal_intervals = len([i for i in intervals if i['status'] == 'normal'])
        active_hours = len([count for count in hourly_counts.values() if count > 0])
        
        # Determine compliance based on medical guidelines
        if concern_intervals == 0 and max_interval <= 120:
            compliance = 'Excellent'
        elif concern_intervals == 0:
            compliance = 'Good'
        elif concern_intervals <= 2:
            compliance = 'Monitor'
        else:
            compliance = 'Attention Needed'
        
        # Calculate movement patterns
        morning_movements = len([m for m in self.movements if 6 <= m['hour'] < 12])
        afternoon_movements = len([m for m in self.movements if 12 <= m['hour'] < 18])
        evening_movements = len([m for m in self.movements if 18 <= m['hour'] < 24])
        night_movements = len([m for m in self.movements if 0 <= m['hour'] < 6])
        
        self.stats = {
            'total_detections': total_detections,
            'avg_interval': round(avg_interval, 1),
            'max_interval': max_interval,
            'min_interval': min_interval,
            'concern_intervals': concern_intervals,
            'monitor_intervals': monitor_intervals,
            'normal_intervals': normal_intervals,
            'active_hours': active_hours,
            'compliance': compliance,
            'intervals': intervals,
            'hourly_counts': hourly_counts,
            'morning_movements': morning_movements,
            'afternoon_movements': afternoon_movements,
            'evening_movements': evening_movements,
            'night_movements': night_movements
        }
        
        return self.stats
    
    def create_24hour_timeline_chart(self):
        """Create beautiful 24-hour movement timeline chart"""
        timeline_data = pd.DataFrame(self.movements)
        
        fig = go.Figure()
        
        # Add gradient line
        fig.add_trace(go.Scatter(
            x=timeline_data['hour_decimal'],
            y=[1] * len(timeline_data),
            mode='lines+markers',
            line=dict(
                color='rgba(139, 92, 246, 0.8)',
                width=4,
                shape='spline'
            ),
            marker=dict(
                size=12,
                color=[f'hsl({240 + i*10}, 70%, 60%)' for i in range(len(timeline_data))],
                line=dict(width=2, color='rgba(255, 255, 255, 0.8)'),
                symbol='circle'
            ),
            name='Movement Detections',
            hovertemplate='<b>Detection #%{text}</b><br>' +
                         'Time: %{customdata[0]}<br>' +
                         'Original: %{customdata[1]}<br>' +
                         '<extra></extra>',
            text=timeline_data['id'],
            customdata=[[row['time_str'], row['original']] for _, row in timeline_data.iterrows()]
        ))
        
        # Add time periods background
        periods = [
            {'start': 0, 'end': 6, 'color': 'rgba(59, 130, 246, 0.1)', 'name': 'Night'},
            {'start': 6, 'end': 12, 'color': 'rgba(16, 185, 129, 0.1)', 'name': 'Morning'},
            {'start': 12, 'end': 18, 'color': 'rgba(245, 158, 11, 0.1)', 'name': 'Afternoon'},
            {'start': 18, 'end': 24, 'color': 'rgba(139, 92, 246, 0.1)', 'name': 'Evening'}
        ]
        
        for period in periods:
            fig.add_vrect(
                x0=period['start'], x1=period['end'],
                fillcolor=period['color'],
                layer="below", line_width=0,
                annotation_text=period['name'],
                annotation_position="top"
            )
        
        fig.update_layout(
            title={
                'text': '🕐 24-Hour Movement Detection Timeline',
                'font': {'size': 24, 'color': '#6366f1', 'family': 'Arial Black'},
                'x': 0.5
            },
            xaxis=dict(
                title='Hour of Day',
                tickmode='linear',
                tick0=0,
                dtick=2,
                ticktext=[f'{h:02d}:00' for h in range(0, 24, 2)],
                tickvals=list(range(0, 24, 2)),
                showgrid=True,
                gridcolor='rgba(99, 102, 241, 0.2)',
                range=[-0.5, 23.5]
            ),
            yaxis=dict(
                title='Movement Detections',
                showticklabels=False,
                showgrid=False,
                range=[0.5, 1.5]
            ),
            plot_bgcolor='rgba(248, 250, 252, 0.8)',
            paper_bgcolor='rgba(139, 92, 246, 0.05)',
            font=dict(family="Arial, sans-serif", size=14, color="#374151"),
            height=400,
            margin=dict(l=60, r=60, t=80, b=60)
        )
        
        return fig
    
    def create_hourly_distribution_chart(self):
        """Create beautiful hourly distribution chart"""
        hours = list(range(24))
        counts = [self.stats['hourly_counts'][h] for h in hours]
        
        # Create beautiful color gradient
        colors = []
        for count in counts:
            if count == 0:
                colors.append('#ef4444')  # Red for no activity
            elif count <= 2:
                colors.append('#f59e0b')  # Yellow for low activity
            elif count <= 4:
                colors.append('#10b981')  # Green for normal activity
            else:
                colors.append('#3b82f6')  # Blue for high activity
        
        fig = go.Figure(data=[
            go.Bar(
                x=[f"{h:02d}:00" for h in hours],
                y=counts,
                marker=dict(
                    color=colors,
                    line=dict(color='rgba(255, 255, 255, 0.8)', width=1.5),
                    opacity=0.9
                ),
                name='Movement Detections',
                hovertemplate='<b>%{x}</b><br>' +
                             'Detections: %{y}<br>' +
                             'Status: %{customdata}<br>' +
                             '<extra></extra>',
                customdata=[
                    'No Activity' if c == 0 else 
                    'Low Activity' if c <= 2 else 
                    'Normal Activity' if c <= 4 else 
                    'High Activity' for c in counts
                ]
            )
        ])
        
        fig.update_layout(
            title={
                'text': '📊 Hourly Movement Detection Distribution',
                'font': {'size': 24, 'color': '#047857', 'family': 'Arial Black'},
                'x': 0.5
            },
            xaxis=dict(
                title='Hour of Day',
                tickangle=45,
                showgrid=True,
                gridcolor='rgba(16, 185, 129, 0.2)'
            ),
            yaxis=dict(
                title='Number of Detections',
                showgrid=True,
                gridcolor='rgba(16, 185, 129, 0.2)'
            ),
            plot_bgcolor='rgba(240, 253, 244, 0.8)',
            paper_bgcolor='rgba(16, 185, 129, 0.05)',
            font=dict(family="Arial, sans-serif", size=14, color="#374151"),
            height=450,
            margin=dict(l=60, r=60, t=80, b=100)
        )
        
        return fig
    
    def create_pattern_analysis_chart(self):
        """Create movement pattern analysis scatter plot"""
        timeline_data = pd.DataFrame(self.movements)
        
        fig = go.Figure()
        
        # Create beautiful scatter plot with size based on sequence
        fig.add_trace(go.Scatter(
            x=timeline_data['hour'],
            y=timeline_data['minute'],
            mode='markers',
            marker=dict(
                size=[8 + i*2 for i in range(len(timeline_data))],
                color=timeline_data['hour'],
                colorscale='Viridis',
                opacity=0.8,
                line=dict(width=2, color='rgba(255, 255, 255, 0.8)'),
                colorbar=dict(
                    title="Hour of Day",
                    titleside="right",
                    tickmode="linear",
                    tick0=0,
                    dtick=4
                )
            ),
            name='Movement Detections',
            hovertemplate='<b>Detection #%{text}</b><br>' +
                         'Time: %{customdata[0]}<br>' +
                         'Original: %{customdata[1]}<br>' +
                         'Hour: %{x}, Minute: %{y}<br>' +
                         '<extra></extra>',
            text=timeline_data['id'],
            customdata=[[row['time_str'], row['original']] for _, row in timeline_data.iterrows()]
        ))
        
        fig.update_layout(
            title={
                'text': '🎯 Movement Pattern Analysis',
                'font': {'size': 24, 'color': '#be185d', 'family': 'Arial Black'},
                'x': 0.5
            },
            xaxis=dict(
                title='Hour of Day',
                tickmode='linear',
                tick0=0,
                dtick=2,
                showgrid=True,
                gridcolor='rgba(244, 63, 94, 0.2)',
                range=[-0.5, 23.5]
            ),
            yaxis=dict(
                title='Minutes',
                showgrid=True,
                gridcolor='rgba(244, 63, 94, 0.2)',
                range=[0, 60]
            ),
            plot_bgcolor='rgba(253, 242, 248, 0.8)',
            paper_bgcolor='rgba(244, 63, 94, 0.05)',
            font=dict(family="Arial, sans-serif", size=14, color="#374151"),
            height=450,
            margin=dict(l=60, r=60, t=80, b=60)
        )
        
        return fig
    
    def create_intervals_safety_chart(self):
        """Create intervals and safety analysis chart"""
        if not self.stats['intervals']:
            fig = go.Figure()
            fig.add_annotation(
                text="No interval data available - need at least 2 detections",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=16)
            )
            return fig
        
        interval_data = pd.DataFrame(self.stats['intervals'])
        
        # Create color mapping
        color_map = {'normal': '#10b981', 'monitor': '#f59e0b', 'concern': '#ef4444'}
        colors = [color_map[status] for status in interval_data['status']]
        
        fig = go.Figure()
        
        # Add interval line chart
        fig.add_trace(go.Scatter(
            x=interval_data['id'],
            y=interval_data['interval'],
            mode='lines+markers',
            line=dict(color='rgba(99, 102, 241, 0.8)', width=3),
            marker=dict(
                size=12,
                color=colors,
                line=dict(width=2, color='rgba(255, 255, 255, 0.8)')
            ),
            name='Interval Duration',
            hovertemplate='<b>Interval #%{x}</b><br>' +
                         'Duration: %{y} minutes<br>' +
                         'From: %{customdata[0]} (%{customdata[2]})<br>' +
                         'To: %{customdata[1]} (%{customdata[3]})<br>' +
                         'Status: %{customdata[4]}<br>' +
                         '<extra></extra>',
            customdata=[[row['from_time'], row['to_time'], row['from_original'], 
                        row['to_original'], row['status'].title()] 
                       for _, row in interval_data.iterrows()]
        ))
        
        # Add safety threshold lines
        fig.add_hline(y=120, line_dash="dash", line_color="red", line_width=3,
                     annotation_text="⚠️ ALERT THRESHOLD (120 min)", 
                     annotation_position="top right")
        
        fig.add_hline(y=60, line_dash="dot", line_color="orange", line_width=2,
                     annotation_text="⚡ MONITOR THRESHOLD (60 min)", 
                     annotation_position="bottom right")
        
        fig.update_layout(
            title={
                'text': '⏱️ Movement Intervals & Safety Analysis',
                'font': {'size': 24, 'color': '#4f46e5', 'family': 'Arial Black'},
                'x': 0.5
            },
            xaxis=dict(
                title='Interval Number',
                showgrid=True,
                gridcolor='rgba(99, 102, 241, 0.2)'
            ),
            yaxis=dict(
                title='Minutes Between Detections',
                showgrid=True,
                gridcolor='rgba(99, 102, 241, 0.2)'
            ),
            plot_bgcolor='rgba(238, 242, 255, 0.8)',
            paper_bgcolor='rgba(99, 102, 241, 0.05)',
            font=dict(family="Arial, sans-serif", size=14, color="#374151"),
            height=450,
            margin=dict(l=60, r=60, t=80, b=60)
        )
        
        return fig
    
    def create_intervals_table_html(self):
        """Create beautiful HTML table for movement intervals"""
        if not self.stats['intervals']:
            return "<p>No interval data available - need at least 2 movement detections.</p>"
        
        table_html = """
        <div class="table-container">
            <h3 class="table-title">📋 Movement Intervals Analysis</h3>
            <div class="table-wrapper">
                <table class="intervals-table">
                    <thead>
                        <tr>
                            <th>From</th>
                            <th>To</th>
                            <th>Interval (min)</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for interval in self.stats['intervals']:
            status_class = interval['status']
            status_text = interval['status'].title()
            status_icon = '🟢' if status_class == 'normal' else '🟡' if status_class == 'monitor' else '🔴'
            
            table_html += f"""
                        <tr class="interval-row {status_class}">
                            <td><span class="time-badge">{interval['from_time']}</span><br><small>{interval['from_original']}</small></td>
                            <td><span class="time-badge">{interval['to_time']}</span><br><small>{interval['to_original']}</small></td>
                            <td><span class="interval-value">{interval['interval']}</span></td>
                            <td><span class="status-badge {status_class}">{status_icon} {status_text}</span></td>
                        </tr>
            """
        
        table_html += """
                    </tbody>
                </table>
            </div>
        </div>
        """
        
        return table_html
    
    def create_dashboard(self, raw_data):
        """Create comprehensive beautiful HTML dashboard"""
        print("🎨 Creating beautiful dashboard...")
        stats = self.analyze_movements(raw_data)
        
        # Create all charts
        timeline_chart = self.create_24hour_timeline_chart()
        hourly_chart = self.create_hourly_distribution_chart()
        pattern_chart = self.create_pattern_analysis_chart()
        intervals_chart = self.create_intervals_safety_chart()
        intervals_table = self.create_intervals_table_html()
        
        # Generate comprehensive HTML dashboard
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤱 Professional Fetal Movement Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.98);
            border-radius: 25px;
            padding: 40px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 20px;
            color: white;
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
        }}
        
        .header h1 {{
            font-size: 3em;
            margin-bottom: 15px;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.3);
            position: relative;
            z-index: 1;
        }}
        
        .header p {{
            font-size: 1.3em;
            opacity: 0.95;
            position: relative;
            z-index: 1;
        }}
        
        .timestamp {{
            position: absolute;
            top: 20px;
            right: 30px;
            background: rgba(255, 255, 255, 0.2);
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 0.9em;
            backdrop-filter: blur(10px);
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #f8fafc, #e2e8f0);
            padding: 30px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            border: 2px solid rgba(255, 255, 255, 0.5);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: 900;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .stat-label {{
            font-size: 1.1em;
            color: #64748b;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        
        .stat-description {{
            font-size: 0.9em;
            color: #94a3b8;
            font-style: italic;
        }}
        
        .excellent {{ 
            background: linear-gradient(135deg, #10b981, #059669);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .good {{ 
            background: linear-gradient(135deg, #10b981, #059669);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .monitor {{ 
            background: linear-gradient(135deg, #f59e0b, #d97706);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .concern {{ 
            background: linear-gradient(135deg, #ef4444, #dc2626);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .chart-container {{
            background: rgba(255, 255, 255, 0.9);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.5);
            backdrop-filter: blur(10px);
        }}
        
        .chart-title {{
            font-size: 1.8em;
            font-weight: 700;
            margin-bottom: 20px;
            text-align: center;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .table-container {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.5);
        }}
        
        .table-title {{
            font-size: 1.8em;
            font-weight: 700;
            margin-bottom: 25px;
            text-align: center;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .table-wrapper {{
            overflow-x: auto;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }}
        
        .intervals-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 15px;
            overflow: hidden;
        }}
        
        .intervals-table th {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px 15px;
            text-align: center;
            font-weight: 700;
            font-size: 1.1em;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        }}
        
        .intervals-table td {{
            padding: 18px 15px;
            text-align: center;
            border-bottom: 1px solid #e5e7eb;
            transition: background-color 0.2s ease;
        }}
        
        .interval-row:hover {{
            background: rgba(102, 126, 234, 0.05);
        }}
        
        .time-badge {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 1.1em;
            display: inline-block;
            box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
        }}
        
        .interval-value {{
            font-size: 1.4em;
            font-weight: 800;
            color: #374151;
        }}
        
        .status-badge {{
            padding: 8px 16px;
            border-radius: 25px;
            font-weight: 700;
            font-size: 0.95em;
            display: inline-block;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .status-badge.normal {{
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            box-shadow: 0 3px 10px rgba(16, 185, 129, 0.3);
        }}
        
        .status-badge.monitor {{
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
            box-shadow: 0 3px 10px rgba(245, 158, 11, 0.3);
        }}
        
        .status-badge.concern {{
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            box-shadow: 0 3px 10px rgba(239, 68, 68, 0.3);
        }}
        
        .data-input-section {{
            background: linear-gradient(135deg, #e0f2fe, #b3e5fc);
            padding: 35px;
            border-radius: 20px;
            margin-bottom: 40px;
            border: 3px solid #0891b2;
            box-shadow: 0 10px 30px rgba(8, 145, 178, 0.15);
        }}
        
        .data-input-section h3 {{
            color: #0c4a6e;
            margin-bottom: 20px;
            font-size: 1.6em;
            font-weight: 700;
        }}
        
        .input-area {{
            width: 100%;
            min-height: 120px;
            padding: 20px;
            border: 3px solid #0891b2;
            border-radius: 15px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 15px;
            resize: vertical;
            background: rgba(255, 255, 255, 0.9);
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .input-area:focus {{
            outline: none;
            border-color: #0e7490;
            box-shadow: 0 0 20px rgba(8, 145, 178, 0.3);
        }}
        
        .update-btn {{
            background: linear-gradient(135deg, #0891b2, #0e7490);
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 15px;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            margin-top: 15px;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(8, 145, 178, 0.3);
        }}
        
        .update-btn:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(8, 145, 178, 0.4);
        }}
        
        .recommendations {{
            background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
            padding: 35px;
            border-radius: 20px;
            border-left: 6px solid #0891b2;
            box-shadow: 0 10px 30px rgba(8, 145, 178, 0.1);
        }}
        
        .recommendations h3 {{
            color: #0c4a6e;
            margin-bottom: 25px;
            font-size: 1.6em;
            font-weight: 700;
        }}
        
        .recommendations-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
        }}
        
        .recommendations h4 {{
            color: #0c4a6e;
            margin-bottom: 15px;
            font-size: 1.2em;
            font-weight: 600;
        }}
        
        .recommendations ul {{
            list-style-type: none;
        }}
        
        .recommendations li {{
            margin-bottom: 12px;
            padding-left: 25px;
            position: relative;
            color: #374151;
            font-weight: 500;
        }}
        
        .recommendations li:before {{
            content: "✅";
            position: absolute;
            left: 0;
            font-size: 1.2em;
        }}
        
        .pattern-summary {{
            background: linear-gradient(135deg, #fef7ff, #f3e8ff);
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 30px;
            border: 2px solid #a855f7;
            box-shadow: 0 10px 30px rgba(168, 85, 247, 0.1);
        }}
        
        .pattern-summary h3 {{
            color: #7c3aed;
            margin-bottom: 20px;
            font-size: 1.6em;
            font-weight: 700;
        }}
        
        .pattern-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        
        .pattern-item {{
            text-align: center;
            padding: 20px;
            background: rgba(255, 255, 255, 0.7);
            border-radius: 15px;
            border: 1px solid rgba(168, 85, 247, 0.2);
        }}
        
        .pattern-value {{
            font-size: 2em;
            font-weight: 800;
            color: #7c3aed;
            margin-bottom: 5px;
        }}
        
        .pattern-label {{
            font-size: 0.9em;
            color: #6b7280;
            font-weight: 600;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 20px;
                margin: 10px;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
                gap: 15px;
            }}
            
            .recommendations-grid {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}
            
            .pattern-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="timestamp">Generated: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            <h1>🤱 Professional Fetal Movement Dashboard</h1>
            <p>Advanced Medical Analysis & Real-time Monitoring</p>
        </div>
        
        <!-- Data Input Section -->
        <div class="data-input-section">
            <h3>📝 Update Movement Detection Data</h3>
            <textarea class="input-area" id="movementData" placeholder="Enter movement detection times here (e.g., 4pm, 5:30pm, 8:15am, 14:30, 23:45)...">{raw_data}</textarea>
            <br>
            <button class="update-btn" onclick="updateDashboard()">🔄 Update Dashboard</button>
            <p style="margin-top: 15px; color: #0c4a6e; font-size: 15px; font-weight: 500;">
                <strong>Supported formats:</strong> 12-hour (4pm, 5:30am), 24-hour (14:30, 23:45), mixed formats
            </p>
        </div>
        
        <!-- Key Statistics -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['total_detections']}</div>
                <div class="stat-label">Total Detections</div>
                <div class="stat-description">Movement instances recorded</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['avg_interval']} min</div>
                <div class="stat-label">Average Interval</div>
                <div class="stat-description">Between detections</div>
            </div>
            <div class="stat-card">
                <div class="stat-value {'concern' if stats['max_interval'] > 120 else 'monitor' if stats['max_interval'] > 60 else 'good'}">{stats['max_interval']} min</div>
                <div class="stat-label">Maximum Gap</div>
                <div class="stat-description">Longest quiet period</div>
            </div>
            <div class="stat-card">
                <div class="stat-value {stats['compliance'].lower().replace(' ', '_')}">{stats['compliance']}</div>
                <div class="stat-label">Compliance Status</div>
                <div class="stat-description">Medical assessment</div>
            </div>
        </div>
        
        <!-- Movement Pattern Summary -->
        <div class="pattern-summary">
            <h3>📊 Daily Movement Pattern Summary</h3>
            <div class="pattern-grid">
                <div class="pattern-item">
                    <div class="pattern-value">{stats['morning_movements']}</div>
                    <div class="pattern-label">Morning (6AM-12PM)</div>
                </div>
                <div class="pattern-item">
                    <div class="pattern-value">{stats['afternoon_movements']}</div>
                    <div class="pattern-label">Afternoon (12PM-6PM)</div>
                </div>
                <div class="pattern-item">
                    <div class="pattern-value">{stats['evening_movements']}</div>
                    <div class="pattern-label">Evening (6PM-12AM)</div>
                </div>
                <div class="pattern-item">
                    <div class="pattern-value">{stats['night_movements']}</div>
                    <div class="pattern-label">Night (12AM-6AM)</div>
                </div>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="chart-container">
            <div id="timelineChart"></div>
        </div>
        
        <div class="chart-container">
            <div id="hourlyChart"></div>
        </div>
        
        <div class="chart-container">
            <div id="patternChart"></div>
        </div>
        
        <div class="chart-container">
            <div id="intervalsChart"></div>
        </div>
        
        <!-- Movement Intervals Table -->
        {intervals_table}
        
        <!-- Medical Recommendations -->
        <div class="recommendations">
            <h3>🏥 Clinical Recommendations & Analysis</h3>
            <div class="recommendations-grid">
                <div>
                    <h4>Current Analysis:</h4>
                    <ul>
                        <li>Total movement detections: {stats['total_detections']}</li>
                        <li>Active monitoring hours: {stats['active_hours']}</li>
                        <li>Normal intervals: {stats['normal_intervals']}</li>
                        <li>Monitor intervals: {stats['monitor_intervals']}</li>
                        <li>Concerning intervals: {stats['concern_intervals']}</li>
                        <li>Overall assessment: {stats['compliance']}</li>
                        <li>Peak activity period: {'Morning' if stats['morning_movements'] == max(stats['morning_movements'], stats['afternoon_movements'], stats['evening_movements'], stats['night_movements']) else 'Afternoon' if stats['afternoon_movements'] == max(stats['morning_movements'], stats['afternoon_movements'], stats['evening_movements'], stats['night_movements']) else 'Evening' if stats['evening_movements'] == max(stats['morning_movements'], stats['afternoon_movements'], stats['evening_movements'], stats['night_movements']) else 'Night'}</li>
                    </ul>
                </div>
                <div>
                    <h4>Medical Guidelines:</h4>
                    <ul>
                        <li>Monitor for 10 movements in 2 hours</li>
                        <li>Contact provider if no movement >2 hours</li>
                        <li>Normal: Intervals <60 minutes</li>
                        <li>Monitor: Intervals 60-120 minutes</li>
                        <li>Alert: Intervals >120 minutes</li>
                        <li>Maintain consistent daily monitoring</li>
                        <li>Record any concerning pattern changes</li>
                        <li>Most active periods typically evening</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Chart configurations with enhanced styling
        const timelineData = {timeline_chart.to_json()};
        const hourlyData = {hourly_chart.to_json()};
        const patternData = {pattern_chart.to_json()};
        const intervalsData = {intervals_chart.to_json()};
        
        // Configure responsive and beautiful charts
        const config = {{
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            displaylogo: false,
            toImageButtonOptions: {{
                format: 'png',
                filename: 'fetal_movement_chart',
                height: 500,
                width: 800,
                scale: 2
            }}
        }};
        
        // Render all charts with beautiful styling
        Plotly.newPlot('timelineChart', timelineData.data, timelineData.layout, config);
        Plotly.newPlot('hourlyChart', hourlyData.data, hourlyData.layout, config);
        Plotly.newPlot('patternChart', patternData.data, patternData.layout, config);
        Plotly.newPlot('intervalsChart', intervalsData.data, intervalsData.layout, config);
        
        function updateDashboard() {{
            const newData = document.getElementById('movementData').value;
            if (newData.trim()) {{
                // Create download link for new data
                const blob = new Blob([newData], {{ type: 'text/plain' }});
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'new_movement_data.txt';
                
                alert('📊 To update dashboard with new data:\\n\\n1. Your data has been prepared\\n2. Copy the new data and update the MOVEMENT_DATA variable in Python\\n3. Run the Python script again\\n4. Dashboard will be automatically regenerated!\\n\\nNew data: ' + newData);
                
                // Auto-select text for easy copying
                document.getElementById('movementData').select();
                
                window.URL.revokeObjectURL(url);
            }} else {{
                alert('⚠️ Please enter movement detection data first.');
            }}
        }}
        
        // Add smooth scroll animations
        document.querySelectorAll('.stat-card').forEach((card, index) => {{
            card.style.animation = `fadeInUp 0.6s ease forwards ${{index * 0.1}}s`;
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
        }});
        
        // CSS animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeInUp {{
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>
"""
        
        return html_content

# Example usage and main execution
if __name__ == "__main__":
    # Your movement detection data - UPDATE THIS WITH NEW DATA
    # Each timestamp represents when a fetal movement was DETECTED/RECORDED
    MOVEMENT_DATA = "4pm, 5pm,5:56pm,8:57pm,9:00pm,9:15pm,9:22pm,9:43pm,10:04pm,10:42pm,23:05,11:34pm,12:41am,12:56am,1:35am,6:37am,7:20am,7:55am,8:05am,1:13pm,2:06pm,2:28pm,3:54pm,4:11pm,4:50pm,5:17pm,5:41pm,5:55pm,7:48pm"
    
    # Define the target folder
    TARGET_FOLDER = r"C:\Users\USER\Documents\Movements"
    
    # Create the folder if it doesn't exist
    try:
        os.makedirs(TARGET_FOLDER, exist_ok=True)
        print(f"📁 Target folder ready: {TARGET_FOLDER}")
    except Exception as e:
        print(f"❌ Error creating folder: {e}")
        print("💡 Using current directory instead...")
        TARGET_FOLDER = "."
    
    # Create analyzer and generate dashboard
    print("🔄 Analyzing fetal movement detection data...")
    analyzer = FetalMovementAnalyzer()
    html_dashboard = analyzer.create_dashboard(MOVEMENT_DATA)
    
    # Generate filename with timestamp
    timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
    filename = f"fetal_movement_dashboard_{timestamp}.html"
    main_filename = "fetal_movement_dashboard.html"
    
    # Full file paths
    timestamped_filepath = os.path.join(TARGET_FOLDER, filename)
    main_filepath = os.path.join(TARGET_FOLDER, main_filename)
    
    try:
        # Save dashboard with timestamp (for history)
        with open(timestamped_filepath, 'w', encoding='utf-8') as f:
            f.write(html_dashboard)
        
        # Save/update main dashboard file (always current)
        with open(main_filepath, 'w', encoding='utf-8') as f:
            f.write(html_dashboard)
        
        print("✅ Beautiful dashboard created successfully!")
        print(f"📁 Main file: {main_filepath}")
        print(f"📁 Backup file: {timestamped_filepath}")
        print("🌐 Open either HTML file in your browser to view the dashboard")
        
        # Try to open the main file automatically
        try:
            import webbrowser
            webbrowser.open(f'file:///{main_filepath.replace(os.sep, "/")}')
            print("🚀 Dashboard opened in your default browser!")
        except:
            print("💡 Manually open the HTML file to view the dashboard")
            
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        # Fallback to current directory
        with open('fetal_movement_dashboard.html', 'w', encoding='utf-8') as f:
            f.write(html_dashboard)
        print("💾 Saved to current directory as fallback")
    
    print("\n📊 Comprehensive Analysis Summary:")
    stats = analyzer.stats
    print(f"   • Total movement detections: {stats['total_detections']}")
    print(f"   • Average interval: {stats['avg_interval']} minutes")
    print(f"   • Maximum gap: {stats['max_interval']} minutes")
    print(f"   • Minimum gap: {stats['min_interval']} minutes")
    print(f"   • Normal intervals: {stats['normal_intervals']}")
    print(f"   • Monitor intervals: {stats['monitor_intervals']}")
    print(f"   • Concerning intervals: {stats['concern_intervals']}")
    print(f"   • Compliance status: {stats['compliance']}")
    print(f"   • Active hours: {stats['active_hours']}")
    print(f"   • Peak activity: {'Morning' if stats['morning_movements'] == max(stats['morning_movements'], stats['afternoon_movements'], stats['evening_movements'], stats['night_movements']) else 'Afternoon' if stats['afternoon_movements'] == max(stats['morning_movements'], stats['afternoon_movements'], stats['evening_movements'], stats['night_movements']) else 'Evening' if stats['evening_movements'] == max(stats['morning_movements'], stats['afternoon_movements'], stats['evening_movements'], stats['night_movements']) else 'Night'}")
    print(f"   • Generated at: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show file location for easy access
    print(f"\n📂 Files saved to:")
    print(f"   {TARGET_FOLDER}")
    
    # Instructions for next run
    print(f"\n🔄 To update with new movement detection data:")
    print(f"   1. Edit MOVEMENT_DATA variable in the Python script")
    print(f"   2. Run: python fetal_dashboard.py")
    print(f"   3. Dashboard will be automatically updated with new analysis!")
    
def quick_update(new_movement_data):
    """
    Quick function to update dashboard with new movement detection data
    Usage: quick_update("8:30am, 9:15am, 10:45am, 12:30pm")
    """
    global MOVEMENT_DATA
    MOVEMENT_DATA = new_movement_data
    
    # Run the main execution
    TARGET_FOLDER = r"C:\Users\USER\Documents\Movements"
    os.makedirs(TARGET_FOLDER, exist_ok=True)
    
    analyzer = FetalMovementAnalyzer()
    html_dashboard = analyzer.create_dashboard(MOVEMENT_DATA)
    
    main_filepath = os.path.join(TARGET_FOLDER, "fetal_movement_dashboard.html")
    
    with open(main_filepath, 'w', encoding='utf-8') as f:
        f.write(html_dashboard)
    
    print(f"✅ Dashboard updated with new movement detection data!")
    print(f"📁 File: {main_filepath}")
    
    return analyzer.stats
