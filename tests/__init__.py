"""
Gran Tesoro VIP Gala & Reverie Summit RSVP System - Test Suite Package
"""
import os
import sys

# Ensure the root project directory is on sys.path for test discovery and direct test execution
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)