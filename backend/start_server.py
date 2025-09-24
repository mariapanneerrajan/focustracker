#!/usr/bin/env python3
"""
Development Server Starter

Simple script to start the FastAPI development server.
Follows SOLID principles with single responsibility: server startup.
"""

import subprocess
import sys
import os

def start_server():
    """
    Start the FastAPI development server.
    
    Returns:
        int: Exit code
    """
    print("🚀 Starting Focus Tracker Backend Server")
    print("=" * 50)
    print("🌐 Server will be available at: http://127.0.0.1:8000")
    print("📚 API Documentation at: http://127.0.0.1:8000/docs")
    print("🔍 Alternative docs at: http://127.0.0.1:8000/redoc")
    print("💚 Health check at: http://127.0.0.1:8000/health")
    print("=" * 50)
    
    # Ensure we're in the backend directory
    if not os.path.exists("app"):
        print("❌ Error: Must run from backend directory")
        return 1
    
    try:
        # Start the server using uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ], check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

if __name__ == "__main__":
    exit_code = start_server()
    sys.exit(exit_code)
