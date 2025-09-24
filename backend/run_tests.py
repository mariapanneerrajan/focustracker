#!/usr/bin/env python3
"""
Test Runner Script

Provides a simple way to run tests for the Focus Tracker backend.
Follows SOLID principles by having a single responsibility: test execution.
"""

import subprocess
import sys
import os

def run_tests():
    """
    Run the complete test suite.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    print("🧪 Running Focus Tracker Backend Tests")
    print("=" * 50)
    
    # Ensure we're in the backend directory
    if not os.path.exists("app"):
        print("❌ Error: Must run from backend directory")
        return 1
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "app/tests/",
            "-v",
            "--tb=short",
            "--color=yes"
        ], check=False)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            print("🚀 Phase 1 Backend is ready!")
        else:
            print("\n❌ Some tests failed!")
            
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
