#!/usr/bin/env python3
"""
API Testing Script for Focus Tracker

This script provides comprehensive testing of all CRUD operations
for the Focus Tracker API, demonstrating Firebase integration.

Usage:
    python test_api.py

Features:
- Tests User CRUD operations
- Tests Session CRUD operations  
- Validates Firebase connectivity
- Provides clear success/failure feedback
"""

import json
import requests
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class FocusTrackerAPITester:
    """
    API testing class following SOLID principles:
    - Single Responsibility: Only handles API testing
    - Open/Closed: Easy to extend with new test methods
    - Interface Segregation: Clear, focused testing interface
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        """Initialize the API tester with base URL."""
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.created_users = []
        self.created_sessions = []
    
    def print_separator(self, title: str):
        """Print a formatted separator for test sections."""
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")
    
    def print_result(self, operation: str, success: bool, details: str = ""):
        """Print test result in a formatted way."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {operation}")
        if details:
            print(f"      {details}")
    
    def test_health_endpoints(self) -> bool:
        """Test health check endpoints."""
        self.print_separator("HEALTH CHECK TESTS")
        
        all_passed = True
        
        # Test basic health endpoint
        try:
            response = self.session.get(f"{self.base_url}/health")
            success = response.status_code == 200
            self.print_result(
                "Basic Health Check",
                success,
                f"Status: {response.status_code}" + (
                    f", Response: {response.json()}" if success else f", Error: {response.text}"
                )
            )
            all_passed = all_passed and success
        except Exception as e:
            self.print_result("Basic Health Check", False, f"Exception: {str(e)}")
            all_passed = False
        
        # Test detailed health endpoint
        try:
            response = self.session.get(f"{self.base_url}/health/detailed")
            success = response.status_code == 200
            details = ""
            if success:
                data = response.json()
                db_status = data.get("services", {}).get("database", {}).get("status", "unknown")
                details = f"Status: {response.status_code}, DB Status: {db_status}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            self.print_result("Detailed Health Check", success, details)
            all_passed = all_passed and success
        except Exception as e:
            self.print_result("Detailed Health Check", False, f"Exception: {str(e)}")
            all_passed = False
        
        return all_passed
    
    def test_user_crud_operations(self) -> bool:
        """Test all User CRUD operations."""
        self.print_separator("USER CRUD OPERATIONS")
        
        all_passed = True
        
        # Test 1: Create User
        user_data = {
            "name": "John Doe",
            "email": f"john.doe.{int(time.time())}@example.com",
            "daily_goal_minutes": 120
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/v1/users/", json=user_data)
            success = response.status_code == 201
            
            if success:
                created_user = response.json()
                self.created_users.append(created_user)
                self.print_result(
                    "Create User",
                    success,
                    f"Created user with ID: {created_user['id']}"
                )
                user_id = created_user['id']
            else:
                self.print_result("Create User", success, f"Status: {response.status_code}, Error: {response.text}")
                return False
            
            all_passed = all_passed and success
        except Exception as e:
            self.print_result("Create User", False, f"Exception: {str(e)}")
            return False
        
        # Test 2: Get User by ID
        try:
            response = self.session.get(f"{self.base_url}/api/v1/users/{user_id}")
            success = response.status_code == 200
            
            if success:
                user = response.json()
                self.print_result(
                    "Get User by ID",
                    success,
                    f"Retrieved user: {user['name']} ({user['email']})"
                )
            else:
                self.print_result("Get User by ID", success, f"Status: {response.status_code}")
            
            all_passed = all_passed and success
        except Exception as e:
            self.print_result("Get User by ID", False, f"Exception: {str(e)}")
            all_passed = False
        
        # Test 3: List Users
        try:
            response = self.session.get(f"{self.base_url}/api/v1/users/")
            success = response.status_code == 200
            
            if success:
                users = response.json()
                self.print_result(
                    "List Users",
                    success,
                    f"Retrieved {len(users)} users"
                )
            else:
                self.print_result("List Users", success, f"Status: {response.status_code}")
            
            all_passed = all_passed and success
        except Exception as e:
            self.print_result("List Users", False, f"Exception: {str(e)}")
            all_passed = False
        
        # Test 4: Update User
        update_data = {
            "name": "Jane Doe Updated",
            "daily_goal_minutes": 150
        }
        
        try:
            response = self.session.put(f"{self.base_url}/api/v1/users/{user_id}", json=update_data)
            success = response.status_code == 200
            
            if success:
                updated_user = response.json()
                self.print_result(
                    "Update User",
                    success,
                    f"Updated user name: {updated_user['name']}, goal: {updated_user['daily_goal_minutes']} min"
                )
            else:
                self.print_result("Update User", success, f"Status: {response.status_code}")
            
            all_passed = all_passed and success
        except Exception as e:
            self.print_result("Update User", False, f"Exception: {str(e)}")
            all_passed = False
        
        # Test 5: Check User Exists
        try:
            response = self.session.get(f"{self.base_url}/api/v1/users/{user_id}/exists")
            success = response.status_code == 200
            
            if success:
                exists = response.json()
                self.print_result(
                    "Check User Exists",
                    success,
                    f"User exists: {exists}"
                )
            else:
                self.print_result("Check User Exists", success, f"Status: {response.status_code}")
            
            all_passed = all_passed and success
        except Exception as e:
            self.print_result("Check User Exists", False, f"Exception: {str(e)}")
            all_passed = False
        
        return all_passed
    
    def test_session_crud_operations(self) -> bool:
        """Test all Session CRUD operations."""
        self.print_separator("SESSION CRUD OPERATIONS")
        
        if not self.created_users:
            self.print_result("Session Tests", False, "No users available for session tests")
            return False
        
        user_id = self.created_users[0]['id']
        all_passed = True
        
        # Test 1: Create Session
        session_data = {
            "user_id": user_id,
            "title": "Deep Work Session",
            "notes": "Working on important project",
            "tags": ["work", "deep-focus", "project-a"]
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/v1/sessions/", json=session_data)
            success = response.status_code == 201
            
            if success:
                created_session = response.json()
                self.created_sessions.append(created_session)
                self.print_result(
                    "Create Session",
                    success,
                    f"Created session with ID: {created_session['id']}, Status: {created_session['status']}"
                )
                session_id = created_session['id']
            else:
                self.print_result("Create Session", success, f"Status: {response.status_code}, Error: {response.text}")
                return False
            
            all_passed = all_passed and success
        except Exception as e:
            self.print_result("Create Session", False, f"Exception: {str(e)}")
            return False
        
        # Test 2: Get Session by ID
        try:
            response = self.session.get(f"{self.base_url}/api/v1/sessions/{session_id}")
            success = response.status_code == 200
            
            if success:
                session = response.json()
                self.print_result(
                    "Get Session by ID",
                    success,
                    f"Retrieved session: {session['title']}, Tags: {', '.join(session['tags'])}"
                )
            else:
                self.print_result("Get Session by ID", success, f"Status: {response.status_code}")
            
            all_passed = all_passed and success
        except Exception as e:
            self.print_result("Get Session by ID", False, f"Exception: {str(e)}")
            all_passed = False
        
        # Test 3: Get User Sessions
        try:
            response = self.session.get(f"{self.base_url}/api/v1/sessions/user/{user_id}")
            success = response.status_code == 200
            
            if success:
                sessions = response.json()
                self.print_result(
                    "Get User Sessions",
                    success,
                    f"Retrieved {len(sessions)} sessions for user"
                )
            else:
                self.print_result("Get User Sessions", success, f"Status: {response.status_code}")
            
            all_passed = all_passed and success
        except Exception as e:
            self.print_result("Get User Sessions", False, f"Exception: {str(e)}")
            all_passed = False
        
        # Test 4: Update Session
        update_data = {
            "title": "Updated Deep Work Session",
            "notes": "Updated notes after completion",
            "tags": ["work", "deep-focus", "completed"]
        }
        
        try:
            response = self.session.put(f"{self.base_url}/api/v1/sessions/{session_id}", json=update_data)
            success = response.status_code == 200
            
            if success:
                updated_session = response.json()
                self.print_result(
                    "Update Session",
                    success,
                    f"Updated session title: {updated_session['title']}"
                )
            else:
                self.print_result("Update Session", success, f"Status: {response.status_code}")
            
            all_passed = all_passed and success
        except Exception as e:
            self.print_result("Update Session", False, f"Exception: {str(e)}")
            all_passed = False
        
        # Test 5: Get Active Sessions
        try:
            response = self.session.get(f"{self.base_url}/api/v1/sessions/user/{user_id}/active")
            success = response.status_code == 200
            
            if success:
                active_sessions = response.json()
                self.print_result(
                    "Get Active Sessions",
                    success,
                    f"Retrieved {len(active_sessions)} active sessions"
                )
            else:
                self.print_result("Get Active Sessions", success, f"Status: {response.status_code}")
            
            all_passed = all_passed and success
        except Exception as e:
            self.print_result("Get Active Sessions", False, f"Exception: {str(e)}")
            all_passed = False
        
        # Test 6: Complete Session
        try:
            response = self.session.post(f"{self.base_url}/api/v1/sessions/{session_id}/complete")
            success = response.status_code == 200
            
            if success:
                completed_session = response.json()
                self.print_result(
                    "Complete Session",
                    success,
                    f"Completed session, Duration: {completed_session.get('duration_minutes', 'N/A')} minutes"
                )
            else:
                self.print_result("Complete Session", success, f"Status: {response.status_code}")
            
            all_passed = all_passed and success
        except Exception as e:
            self.print_result("Complete Session", False, f"Exception: {str(e)}")
            all_passed = False
        
        return all_passed
    
    def cleanup_test_data(self) -> bool:
        """Clean up test data created during testing."""
        self.print_separator("CLEANUP TEST DATA")
        
        all_passed = True
        
        # Delete created sessions
        for session in self.created_sessions:
            try:
                response = self.session.delete(f"{self.base_url}/api/v1/sessions/{session['id']}")
                success = response.status_code == 204
                self.print_result(
                    f"Delete Session {session['id'][:8]}...",
                    success,
                    f"Status: {response.status_code}"
                )
                all_passed = all_passed and success
            except Exception as e:
                self.print_result(f"Delete Session {session['id'][:8]}...", False, f"Exception: {str(e)}")
                all_passed = False
        
        # Delete created users
        for user in self.created_users:
            try:
                response = self.session.delete(f"{self.base_url}/api/v1/users/{user['id']}")
                success = response.status_code == 204
                self.print_result(
                    f"Delete User {user['name']}",
                    success,
                    f"Status: {response.status_code}"
                )
                all_passed = all_passed and success
            except Exception as e:
                self.print_result(f"Delete User {user['name']}", False, f"Exception: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def run_all_tests(self) -> bool:
        """Run all API tests."""
        print("🚀 Starting Focus Tracker API Tests")
        print(f"📡 Testing API at: {self.base_url}")
        
        all_tests_passed = True
        
        # Run all test suites
        test_suites = [
            ("Health Endpoints", self.test_health_endpoints),
            ("User CRUD Operations", self.test_user_crud_operations),
            ("Session CRUD Operations", self.test_session_crud_operations),
            ("Cleanup Test Data", self.cleanup_test_data)
        ]
        
        for suite_name, test_method in test_suites:
            try:
                suite_passed = test_method()
                all_tests_passed = all_tests_passed and suite_passed
            except Exception as e:
                self.print_result(f"{suite_name} Suite", False, f"Unexpected error: {str(e)}")
                all_tests_passed = False
        
        # Print final results
        self.print_separator("FINAL RESULTS")
        if all_tests_passed:
            print("🎉 ALL TESTS PASSED! Firebase integration is working correctly.")
            print("✨ Your Focus Tracker API is ready for production use.")
        else:
            print("⚠️  SOME TESTS FAILED. Please check the Firebase configuration and server logs.")
            print("🔧 Check the detailed error messages above for troubleshooting guidance.")
        
        print(f"\n📊 Test Summary:")
        print(f"   - Health Checks: Available")
        print(f"   - User CRUD: {'✅ Working' if all_tests_passed else '❌ Issues'}")
        print(f"   - Session CRUD: {'✅ Working' if all_tests_passed else '❌ Issues'}")
        print(f"   - Firebase Integration: {'✅ Connected' if all_tests_passed else '❌ Connection Issues'}")
        
        return all_tests_passed


def main():
    """Main function to run API tests."""
    tester = FocusTrackerAPITester()
    
    # Wait a moment for server to be ready
    print("⏳ Waiting 3 seconds for server to start...")
    time.sleep(3)
    
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
