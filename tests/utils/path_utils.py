#!/usr/bin/env python3
"""
Path utilities for test files to avoid hardcoded paths.

This module provides utilities to dynamically find the project root
and add necessary paths to sys.path for imports.
"""
import os
import sys
from pathlib import Path


def find_project_root(marker_files=None):
    """
    Find the project root by looking for marker files.
    
    Args:
        marker_files: List of files that indicate project root.
                     Defaults to common Python project markers.
    
    Returns:
        Path to project root directory.
    """
    if marker_files is None:
        # Prioritize stronger indicators first - these should be unique to project root
        marker_files = [
            'docker-compose.yml',  # Strong indicator - only in project root
            '.git',               # Strong indicator - only in project root
            'pyproject.toml',      # Strong indicator
            'setup.py',           # Strong indicator  
            ('api', 'tests', 'README.md'),  # All three must exist together
            'requirements.txt',    # Only if no stronger matches
        ]
    
    current_dir = Path(__file__).resolve()
    
    # Walk up the directory tree
    for parent in [current_dir] + list(current_dir.parents):
        for marker in marker_files:
            if isinstance(marker, tuple):
                # All items in tuple must exist
                if all((parent / item).exists() for item in marker):
                    return parent
            else:
                # Single file/directory exists
                if (parent / marker).exists():
                    return parent
    
    raise RuntimeError("Could not find project root directory")


def setup_project_paths():
    """
    Add project root and api directory to sys.path for imports.
    
    Returns:
        tuple: (project_root, api_path) as Path objects
    """
    project_root = find_project_root()
    api_path = project_root / 'api'
    
    # Add to sys.path if not already present
    project_root_str = str(project_root)
    api_path_str = str(api_path)
    
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    if api_path_str not in sys.path:
        sys.path.insert(0, api_path_str)
    
    return project_root, api_path


def get_test_data_dir():
    """
    Get the test data directory path.
    
    Returns:
        Path to tests/data directory
    """
    project_root = find_project_root()
    return project_root / 'tests' / 'data'


def get_api_dir():
    """
    Get the API directory path.
    
    Returns:
        Path to api directory
    """
    project_root = find_project_root()
    return project_root / 'api'


# Convenience function for common use case
def setup_imports():
    """
    Quick setup for test imports. Call this at the top of test files.
    
    Example:
        from tests.utils.path_utils import setup_imports
        setup_imports()
        
        # Now you can import from api
        from api.domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler
    """
    setup_project_paths()