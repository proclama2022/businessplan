#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple test script to verify FinancialUI can be imported
"""

try:
    from financial.ui import FinancialUI
    print("Successfully imported FinancialUI")
    
    # Create an instance to verify it works
    ui = FinancialUI()
    print("Successfully created FinancialUI instance")
except Exception as e:
    print(f"Error importing FinancialUI: {e}")
    import traceback
    traceback.print_exc()

print("Test completed") 