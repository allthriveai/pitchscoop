#!/usr/bin/env python3
"""
Test that the new test structure works correctly.
"""
import sys
from pathlib import Path

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

def test_import_paths():
    """Test that we can import from the main codebase."""
    try:
        # Test importing from domains
        from api.domains.events.mcp.events_mcp_tools import EVENTS_MCP_TOOLS
        assert len(EVENTS_MCP_TOOLS) > 0, "Should have event tools"
        print("✅ Can import events tools")
        
        from api.domains.recordings.mcp.mcp_tools import MCP_TOOLS
        assert len(MCP_TOOLS) > 0, "Should have recording tools"
        print("✅ Can import recording tools")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

def test_directory_structure():
    """Test that the test directory structure is correct."""
    tests_dir = Path(__file__).parent
    
    expected_dirs = ['mcp', 'integration', 'unit', 'tools', 'e2e', 'fixtures', 'mocks']
    
    for dir_name in expected_dirs:
        dir_path = tests_dir / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/ directory exists")
        else:
            print(f"❌ {dir_name}/ directory missing")
            return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testing new test structure...")
    print("=" * 40)
    
    structure_ok = test_directory_structure()
    imports_ok = test_import_paths()
    
    if structure_ok and imports_ok:
        print("\n🎉 Test structure validation passed!")
        sys.exit(0)
    else:
        print("\n❌ Test structure validation failed!")
        sys.exit(1)