# Focus Tracker

A mobile-first web application designed to help users track the time they spend on focused creative work each day.

## 📋 Project Overview

Focus Tracker is a productivity application that allows users to monitor and record their focused work sessions throughout the day. The application emphasizes simplicity and ease of use with a clean, mobile-first interface.

## 🛠 Tech Stack

### Frontend
- **Next.js** - React framework for production
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Mobile-first design** - Optimized for mobile devices

### Backend
- **Python** - Backend development language
- **REST API** - Communication protocol between frontend and backend
- **Firebase Database** - Cloud-based NoSQL database for data storage

### Authentication
- **Google Firebase** - User authentication and authorization

### Architecture
- **Separation of Concerns** - Frontend and backend as separate, independent services
- **RESTful Communication** - Clean API interface between services

## 🎯 Core Features

### Authentication System
- **Login/Signup Page** - Users can create accounts or sign in
- **Persistent Sessions** - Returning users are automatically logged in
- **Firebase Integration** - Secure authentication via Google Firebase

### Main Application Interface

#### Focus Timer
- **Start/Stop Button** - Large, easy-to-tap button for mobile users
- **Continuous Timer** - Tracks active focused work sessions
- **Session Recording** - Each start-to-stop interval is recorded as one focused work segment
- **Multiple Sessions** - Users can start and stop multiple sessions throughout the day

#### Daily Progress Tracking
- **Time Indicator** - Real-time display of total focused time for the current day
- **Session Management** - All focused work segments are stored in the database by date

#### Analytics Dashboard
- **30-Day Graph** - Visual representation of daily focused work time
- **Historical Data** - Track progress and patterns over the last month
- **Bottom Placement** - Positioned at the bottom of the main page for easy access

## 🏗 Application Flow

1. **User Authentication**
   - New users: Sign up via Firebase
   - Returning users: Automatic login (if previously authenticated)
   - Direct redirect to main application upon successful authentication

2. **Main Dashboard**
   - Large start/stop button prominently displayed
   - Current session timer (when active)
   - Daily total time indicator
   - 30-day progress graph at bottom

3. **Focus Session Workflow**
   - User taps "Start" to begin focused work
   - Timer runs continuously until "Stop" is pressed
   - Session data is immediately saved to database
   - Process can be repeated multiple times per day

## 📱 Design Principles

- **Mobile-First Approach** - Optimized for touch interactions
- **Simple Interface** - Minimal cognitive load for users
- **Clear Visual Feedback** - Easy-to-read timers and progress indicators
- **Responsive Design** - Works seamlessly across all device sizes

## 🔧 Development Goals

- Clean separation between frontend and backend services
- RESTful API design for scalable communication
- Secure user authentication and data storage
- Intuitive user experience focused on productivity tracking
