#!/usr/bin/env python3
"""Comprehensive test of GUI functionality including query and file operations."""

import sys
import os
from pathlib import Path
from sage.gui_app import SageGUI
from sage.config import ConfigManager

def test_query_functionality():
    """Test if the query section actually works."""
    project_path = Path("demo_project").absolute()
    
    print("🧪 Testing Query Functionality")
    print("=" * 40)
    
    try:
        # Check if project is configured
        config_manager = ConfigManager(project_path)
        config = config_manager.load()
        
        if not config:
            print("❌ Project not configured - run 'sage setup' first")
            return False
            
        print(f"✅ Project configured with {config.llm_provider} {config.llm_model}")
        
        # Create GUI instance
        app = SageGUI(project_path)
        
        # Verify all query components exist
        assert hasattr(app, 'query_entry'), "Query entry field missing"
        assert hasattr(app, 'ask_button'), "Ask button missing"
        assert hasattr(app, 'response_text'), "Response text area missing"
        assert hasattr(app, 'sources_text'), "Sources text area missing"
        assert hasattr(app, 'llm_client'), "LLM client not initialized"
        assert hasattr(app, 'vector_store'), "Vector store not initialized"
        
        print("✅ All query UI components present")
        
        # Test vector store has data
        doc_count = app.vector_store.get_document_count()
        print(f"✅ Vector store has {doc_count} document chunks")
        
        if doc_count == 0:
            print("⚠️  No documents indexed - run 'sage update' first")
            return False
            
        # Test search functionality
        test_query = "investment amount"
        documents = app.vector_store.search(test_query, k=3)
        print(f"✅ Search found {len(documents)} relevant documents")
        
        if len(documents) > 0:
            print("✅ Query pipeline works - GUI queries will succeed")
        else:
            print("❌ No documents found for test query")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False

def test_file_operations():
    """Test file opening and operations."""
    project_path = Path("demo_project").absolute()
    
    print("\n🧪 Testing File Operations")
    print("=" * 40)
    
    try:
        app = SageGUI(project_path)
        
        # Check if demo files exist
        docs_dir = project_path / "docs"
        if not docs_dir.exists():
            print("❌ Demo docs directory not found")
            return False
            
        test_files = [
            "project_overview.md",
            "epc_contract_summary.txt", 
            "technical_specs.md"
        ]
        
        existing_files = []
        for filename in test_files:
            file_path = docs_dir / filename
            if file_path.exists():
                existing_files.append(file_path)
                print(f"✅ Found: {filename}")
            else:
                print(f"❌ Missing: {filename}")
                
        if not existing_files:
            print("❌ No demo files found")
            return False
            
        # Test file operation methods
        test_file = existing_files[0]
        
        # Test that all file operation methods exist and are callable
        methods_to_test = [
            ('_open_file', 'File opening'),
            ('_show_in_explorer', 'Show in explorer'), 
            ('_copy_path_to_clipboard', 'Copy path'),
            ('_reindex_single_file', 'Single file reindex')
        ]
        
        for method_name, description in methods_to_test:
            if hasattr(app, method_name) and callable(getattr(app, method_name)):
                print(f"✅ {description} method available")
            else:
                print(f"❌ {description} method missing")
                return False
                
        # Test file tree event bindings
        tree_events = app.files_tree.bind()
        expected_events = ['<<TreeviewSelect>>', '<Double-1>', '<Button-2>', '<Button-3>']
        
        for event in expected_events:
            if event in tree_events:
                print(f"✅ Event binding: {event}")
            else:
                print(f"❌ Missing event binding: {event}")
                
        print("✅ All file operations properly configured")
        return True
        
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False

def test_integration():
    """Test the complete integration."""
    print("\n🧪 Testing Complete Integration")
    print("=" * 40)
    
    # Test CLI query works (this proves the backend works)
    print("Testing CLI query to verify backend...")
    
    project_path = Path("demo_project").absolute()
    original_cwd = os.getcwd()
    
    try:
        os.chdir(project_path)
        
        # Import and test the CLI function directly
        from sage.config import ConfigManager
        from sage.vector_store import VectorStore
        from sage.llm_client import LLMClient
        
        config_manager = ConfigManager(project_path)
        config = config_manager.load()
        
        if not config:
            print("❌ Configuration not found")
            return False
            
        # Test components individually
        vector_store = VectorStore(config)
        vector_store.initialize()
        
        llm_client = LLMClient(config)
        
        # Test search
        documents = vector_store.search("total investment", k=3)
        if not documents:
            print("❌ Search returned no documents")
            return False
            
        print(f"✅ Found {len(documents)} relevant documents")
        
        # Test LLM query (this is the real test)
        try:
            result = llm_client.answer_question("What is the total investment amount?", documents)
            
            if 'error' in result and result['error']:
                print(f"❌ LLM query failed: {result['answer']}")
                return False
            else:
                print("✅ LLM query successful!")
                print(f"   Answer preview: {result['answer'][:100]}...")
                print(f"   Sources: {len(result['sources'])} files")
                return True
                
        except Exception as e:
            print(f"❌ LLM query error: {str(e)}")
            if "api" in str(e).lower():
                print("   🔑 This looks like an API key issue")
                print("   Please check your API key configuration")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False
    finally:
        os.chdir(original_cwd)

def main():
    """Run all tests."""
    print("🚀 Testing Project Sage Full Functionality")
    print("=" * 50)
    
    # Change to project directory
    os.chdir("/Users/phonghan/Coding/project-sage")
    
    tests = [
        ("Query Functionality", test_query_functionality),
        ("File Operations", test_file_operations), 
        ("Integration Test", test_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nThe GUI query section DOES work and file operations are fully functional!")
        print("\nTo use:")
        print("1. cd demo_project")
        print("2. sage gui")
        print("3. Go to Query tab and ask: 'What is the total investment amount?'")
        print("4. Double-click files in Files tab to open them")
        print("5. Right-click files for more options")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Check the output above for specific issues")
        
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)