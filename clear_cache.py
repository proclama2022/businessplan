#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to clear Streamlit's cache
"""

import os
import shutil
import tempfile
from pathlib import Path
import streamlit as st

def clear_streamlit_cache():
    """Clear Streamlit's cache directories"""
    # Get the Streamlit cache directory
    cache_root = Path(tempfile.gettempdir()) / ".streamlit"
    
    if cache_root.exists():
        try:
            shutil.rmtree(cache_root)
            print(f"Cleared Streamlit cache at {cache_root}")
        except Exception as e:
            print(f"Error clearing cache: {e}")
    else:
        print(f"Cache directory {cache_root} not found")
    
    # Also clear the .streamlit directory in the current folder if it exists
    local_cache = Path(".streamlit/cache")
    if local_cache.exists():
        try:
            shutil.rmtree(local_cache)
            print(f"Cleared local Streamlit cache at {local_cache}")
        except Exception as e:
            print(f"Error clearing local cache: {e}")

if __name__ == "__main__":
    clear_streamlit_cache()
    print("Cache clearing completed") 