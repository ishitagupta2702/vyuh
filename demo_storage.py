#!/usr/bin/env python3
"""
Demo script for the Storage Tool
This script demonstrates how the storage tool works independently.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vyuh.tools.development_tools import storage_tool

def demo_storage():
    """Demonstrate the storage tool functionality"""
    
    print("🔧 Storage Tool Demo")
    print("=" * 40)
    
    # Sample content to store
    sample_content = """
# Sample Agent Output

This is a sample output from a development agent.

## Features
- Feature 1: User authentication
- Feature 2: Task management
- Feature 3: Real-time collaboration

## Technical Stack
- Frontend: React
- Backend: Node.js
- Database: MongoDB
"""
    
    print("📝 Sample content to store:")
    print(sample_content)
    print()
    
    # Store the content
    print("💾 Storing content...")
    result = storage_tool._run(
        content=sample_content,
        agent_name="Demo Agent",
        task_name="Sample Task",
        content_type="markdown",
        project_name="demo_project"
    )
    
    print("📊 Storage result:")
    print(result)
    print()
    
    # Check what was created
    resources_dir = Path("resources")
    if resources_dir.exists():
        print("📁 Files created:")
        for item in resources_dir.rglob("*"):
            if item.is_file():
                print(f"  📄 {item}")
    else:
        print("⚠️ No resources folder found")

if __name__ == "__main__":
    demo_storage()
