# Time Tracker Desktop Application

## Overview

This is a lightweight time tracking desktop application built with Python and Tkinter. The application provides a simple interface for tracking time spent on tasks with automatic task management features including auto-switching, task conclusion, and inactivity-based task closing.

## System Architecture

The application follows a single-file monolithic architecture with the following design principles:

- **Single-threaded GUI**: Uses Tkinter for the main user interface
- **Background threading**: Implements threading for auto-close functionality and real-time updates
- **File-based persistence**: Uses CSV files for data storage
- **Event-driven architecture**: Responds to user actions and timer events

## Key Components

### 1. Main Application Class (`TimeTracker`)
- **Purpose**: Central controller managing all application functionality
- **Responsibilities**: GUI setup, task management, data persistence, timer handling
- **Architecture Decision**: Single class design for simplicity and maintainability

### 2. GUI Components
- **Technology**: Tkinter with ttk widgets for modern appearance
- **Layout**: Vertical layout with task entry, control buttons, and status display
- **Design Choice**: Simple, functional interface prioritizing ease of use

### 3. Task Management System
- **Current Task Tracking**: Maintains active task state with start time
- **Auto-switching**: Automatically concludes previous tasks when starting new ones
- **Auto-close**: Closes tasks after 2 hours of inactivity
- **Rationale**: Reduces manual overhead and prevents forgotten running tasks

### 4. Data Persistence
- **Format**: CSV file storage
- **File**: `time_tracker.csv`
- **Structure**: Task name, start time, end time, duration
- **Choice Rationale**: CSV provides Excel compatibility and human readability

## Data Flow

1. **Task Start**: User enters task name → Current task updated → Start time recorded
2. **Task Switch**: New task started → Previous task auto-concluded → New task begins
3. **Manual Stop**: User stops task → End time recorded → Data saved to CSV
4. **Auto-close**: Inactivity timer triggers → Task concluded automatically
5. **Export**: CSV data exported to user-selected location

## External Dependencies

- **Python Standard Library**:
  - `tkinter`: GUI framework
  - `csv`: Data file handling
  - `datetime`: Time management
  - `threading`: Background operations
  - `time`: Timer functionality
  - `os`: File system operations
  - `pathlib`: Path handling

- **No external packages required**: Application uses only built-in Python modules for maximum portability

## Deployment Strategy

- **Standalone Python Script**: Single file execution
- **No Installation Required**: Runs directly with Python interpreter
- **Cross-platform**: Compatible with Windows, macOS, and Linux
- **Data Portability**: CSV files can be moved between systems

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

- July 01, 2025: Successfully deployed lightweight time tracking desktop application
- Application confirmed working on user's desktop with full GUI functionality
- All core features operational: task switching, auto-close, CSV logging, real-time display
- Enhanced window resizing: larger default size (600x500), minimum size limits, fully resizable interface
- Added task categorization with color-coded categories (Work, Personal, Learning, Other)
- Implemented customizable quick-access task buttons with category assignment
- Integrated PostgreSQL online database for cloud storage and synchronization
- Added "Always on Top" checkbox feature to keep window visible above other applications
- Created tabbed interface with Categories, Quick Tasks, and Reports sections
- Advanced filtering and reporting capabilities by category
- Built comprehensive web interface accessible from any browser
- Automatic task resumption on startup for interrupted work sessions
- Configured timezone to match Windows system settings
- Hidden Python console window for clean desktop application appearance
- Added intelligent display environment detection for desktop applications
- Enhanced error handling with clear guidance when GUI environment unavailable
- Created comprehensive README.md with usage instructions for all interfaces
- Built simple_desktop.py as most reliable desktop version
- Created start_time_tracker.py launcher for automatic environment detection
- Fixed web interface to work with CSV fallback when database unavailable
- Resolved desktop application initialization issues with proper error handling

## Changelog

Changelog:
- July 01, 2025. Initial setup and successful deployment