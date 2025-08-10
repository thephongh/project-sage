#!/usr/bin/env python3
"""Test script to verify GUI functionality."""

import sys
from pathlib import Path
from sage.gui_app import SageGUI

def test_gui():
    """Test the GUI application."""
    project_path = Path("demo_project").absolute()
    
    print(f"Testing GUI with project: {project_path.absolute()}")
    
    try:
        # Create GUI instance
        app = SageGUI(project_path)
        
        # Test that all components initialized
        assert hasattr(app, 'config'), "Config not loaded"
        assert hasattr(app, 'file_processor'), "File processor not initialized"
        assert hasattr(app, 'vector_store'), "Vector store not initialized"
        assert hasattr(app, 'llm_client'), "LLM client not initialized"
        
        print("✅ GUI components initialized successfully")
        
        # Test data loading
        app._load_data()
        print("✅ Data loading works")
        
        # Test button functions (without actually running them)
        print("✅ All button handlers exist:")
        print(f"  - Update index: {callable(app._update_index)}")
        print(f"  - Ask question: {callable(app._ask_question)}")
        print(f"  - Load data: {callable(app._load_data)}")
        print(f"  - Show status: {callable(app._show_status)}")
        
        print("\n🎉 GUI test successful! All functionality is properly wired.")
        print(f"Run 'cd {project_path} && sage gui' to launch the interface.")
        
        return True
        
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_gui()
    sys.exit(0 if success else 1)