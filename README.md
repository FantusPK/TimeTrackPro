# Time Tracker Application

A comprehensive time tracking solution with desktop and web interfaces, designed to work reliably across different environments.

## 🚀 Quick Start

### Automatic Launcher (Recommended)
```bash
python start_time_tracker.py
```
This script automatically detects your environment and offers the best options.

### Manual Options

#### Web Interface (Works Everywhere)
```bash
python web_app.py
```
Then open your browser to: http://localhost:5000

#### Desktop Applications (Local Computer Only)
```bash
python simple_desktop.py     # Reliable, CSV-only version
python main_enhanced.py      # Full-featured with database
python main.py               # Original simple version
```

## 📋 Features

### Desktop Applications
- **Simple Desktop Tracker** (`simple_desktop.py`) - **MOST RELIABLE**
  - Basic task tracking with timestamps
  - Automatic task switching
  - CSV export and recent task display
  - Real-time duration display
  - Lightweight and stable

- **Enhanced Time Tracker** (`main_enhanced.py`)
  - All simple features plus:
  - Task categorization with color coding
  - Custom quick-access buttons
  - Database storage with offline CSV backup
  - Advanced filtering and reports
  - Always-on-top window option

- **Original Simple Tracker** (`main.py`)
  - Basic version with auto-close feature
  - 2-hour auto-close for inactive tasks
  - CSV export

### Web Interface (`web_app.py`)
- Browser-based access to all enhanced features
- Works on any device with a web browser
- Real-time task updates
- Category and quick task management
- Task reporting and filtering
- Mobile-friendly design

## 🔧 Installation

### Requirements
```bash
pip install flask flask-cors psycopg2-binary pytz
```

### Database Setup
The application uses PostgreSQL for cloud storage. If no database is available, it automatically falls back to CSV files for local storage.

## 💻 Environment Requirements

### Desktop Applications
- **Windows**: Runs directly
- **Mac/Linux**: Requires graphical desktop environment
- **Server/Cloud**: ❌ Cannot run (no display) - Use web interface instead

### Web Interface
- Runs anywhere Python is available
- Access from any browser
- Perfect for server deployments

## 📊 Data Storage

- **Primary**: PostgreSQL database (cloud sync)
- **Backup**: CSV files (local storage)
- **Export**: CSV format compatible with Excel

## 🎯 Usage

### Starting a Task
1. **Desktop**: Enter task name and press Enter or click "Start Task"
2. **Web**: Enter task name in the main input field and click "Start Task"

### Quick Tasks
1. Create custom buttons for frequently used tasks
2. Assign categories for better organization
3. One-click task starting

### Reports
- Filter tasks by category
- View time summaries
- Export data to CSV

## 🔧 Troubleshooting

### Desktop App Won't Start
If you see "DISPLAY ENVIRONMENT REQUIRED" error:
- You're running on a server without GUI support
- Solution: Use the web interface instead

### Database Connection Issues
- App automatically falls back to CSV-only mode
- All functionality remains available
- Data stored locally in `time_tracker.csv`

### Missing Dependencies
```bash
pip install -r requirements.txt
```

## 📁 Files

- `main.py` - Simple desktop time tracker
- `main_enhanced.py` - Enhanced desktop version
- `web_app.py` - Web interface server
- `models.py` - Database management
- `templates/index.html` - Web interface
- `time_tracker.csv` - Local data storage
- `replit.md` - Project documentation

## 🌐 Deployment

### Local Desktop
Download files and run the desktop applications directly.

### Web Server
1. Set up PostgreSQL database
2. Configure environment variables
3. Run `python web_app.py`
4. Access via browser

## 📝 License

This project is open source and available under standard terms.