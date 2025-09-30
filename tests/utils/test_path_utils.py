#!/usr/bin/env python3
"""
Test and example for path utilities.

This demonstrates the proper way to handle imports in test files
without hardcoding paths.
"""
import os
import sys
from pathlib import Path

# Add parent directory to find utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from tests.utils.path_utils import setup_imports, find_project_root, get_api_dir

def test_path_utilities():
    """Test that path utilities work correctly."""
    print("🧪 Testing Path Utilities")
    print("=" * 40)
    
    # Test finding project root
    try:
        project_root = find_project_root()
        print(f"✅ Project root found: {project_root}")
        
        # Verify it looks like a project root
        expected_files = ['docker-compose.yml', 'README.md']
        for file in expected_files:
            if (project_root / file).exists():
                print(f"✅ Found expected file: {file}")
            else:
                print(f"⚠️  Missing expected file: {file}")
                
    except Exception as e:
        print(f"❌ Failed to find project root: {e}")
        return False
    
    # Test setup imports
    try:
        setup_imports()
        print("✅ Import paths setup successfully")
        
        # Test that we can now import from api
        from api.main import app  # This should work now
        print("✅ Successfully imported from api module")
        
    except ImportError as e:
        print(f"❌ Failed to import from api: {e}")
        return False
    except Exception as e:
        print(f"❌ Setup imports failed: {e}")
        return False
    
    # Test API directory
    try:
        api_dir = get_api_dir()
        print(f"✅ API directory: {api_dir}")
        
        if (api_dir / 'main.py').exists():
            print("✅ API directory contains expected files")
        else:
            print("⚠️  API directory missing expected files")
            
    except Exception as e:
        print(f"❌ Failed to get API directory: {e}")
        return False
    
    print("\n🎉 All path utility tests passed!")
    print("\n📝 Usage in test files:")
    print("""
    import os
    import sys
    
    # Add project root to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from tests.utils.path_utils import setup_imports
    setup_imports()
    
    # Now you can import from api
    from api.domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler
    """)
    
    return True

if __name__ == '__main__':
    success = test_path_utilities()
    sys.exit(0 if success else 1)