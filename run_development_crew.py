#!/usr/bin/env python3
"""
Development Crew Runner
This script allows you to run the development crew with custom ideas
and demonstrates the storage functionality for all agent outputs.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vyuh.simple_crew import create_simple_crew
from dotenv import load_dotenv

def run_development_crew(idea, use_simple_crew=True):
    """Run the development crew with a custom idea"""
    
    # Load environment variables
    load_dotenv()
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key in a .env file or environment variable")
        return None
    
    print("🚀 Starting Development Crew...")
    print("=" * 60)
    
    try:
        if use_simple_crew:
            crew = create_simple_crew()
            crew_type = "Simple"
        else:
            # For now, we'll use simple crew since the full crew has YAML issues
            crew = create_simple_crew()
            crew_type = "Simple"
        
        print(f"✅ {crew_type} crew created successfully")
        print(f"📋 Agents: {len(crew.agents)}")
        print(f"📝 Tasks: {len(crew.tasks)}")
        print()
        
        print(f"💡 Idea: {idea}")
        print("=" * 60)
        print("🔄 Running crew tasks...")
        print()
        
        # Run the crew
        result = crew.kickoff(inputs={"input_idea": idea})
        
        print("=" * 60)
        print("✅ Development Crew completed successfully!")
        print()
        print("📊 Final Result:")
        print("-" * 40)
        print(result)
        print()
        
        # Check if resources were created
        resources_dir = Path("resources")
        if resources_dir.exists():
            print("�� Resources created:")
            total_files = 0
            for item in resources_dir.rglob("*"):
                if item.is_file():
                    print(f"  📄 {item}")
                    total_files += 1
            print(f"\n📊 Total files created: {total_files}")
        else:
            print("⚠️ No resources folder found")
            
        return result
        
    except Exception as e:
        print(f"❌ Error running development crew: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function to handle command line arguments"""
    
    parser = argparse.ArgumentParser(description="Run the Development Crew with a custom idea")
    parser.add_argument("--idea", "-i", 
                       default="A task management app for remote teams with real-time collaboration, file sharing, and progress tracking",
                       help="The app idea to develop")
    parser.add_argument("--simple", "-s", action="store_true", default=True,
                       help="Use simple crew (default)")
    parser.add_argument("--full", "-f", action="store_true", default=False,
                       help="Use full development crew")
    
    args = parser.parse_args()
    
    # Determine which crew to use
    use_simple_crew = not args.full
    
    print("🎯 Development Crew Runner")
    print("=" * 60)
    print(f"📝 Idea: {args.idea}")
    print(f"🔧 Crew Type: {'Simple' if use_simple_crew else 'Full'}")
    print()
    
    # Run the crew
    result = run_development_crew(args.idea, use_simple_crew)
    
    if result:
        print("🎉 Development crew execution completed successfully!")
        print("\n💡 Next steps:")
        print("  1. Check the 'resources' folder for all agent outputs")
        print("  2. Review the generated architecture and features")
        print("  3. Use the outputs to start building your application")
    else:
        print("❌ Development crew execution failed")

if __name__ == "__main__":
    main()
