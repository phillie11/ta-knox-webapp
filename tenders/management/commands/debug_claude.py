#!/usr/bin/env python3
# debug_claude.py - Run this to debug Claude AI installation

import sys
import os

print("=== Claude AI Installation Debug ===")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")
print(f"Current directory: {os.getcwd()}")

# Test basic imports
print("\n1. Testing basic imports...")
try:
    import django
    print(f"✅ Django {django.VERSION} imported successfully")
except ImportError as e:
    print(f"❌ Django import failed: {e}")

# Test anthropic import
print("\n2. Testing anthropic import...")
try:
    import anthropic
    print(f"✅ Anthropic imported successfully")
    print(f"   Version: {getattr(anthropic, '__version__', 'unknown')}")
    
    # Test creating client (without API key)
    try:
        client = anthropic.Anthropic(api_key="test-key")
        print("✅ Anthropic client creation works")
    except Exception as e:
        print(f"⚠️  Anthropic client creation failed: {e}")
        
except ImportError as e:
    print(f"❌ Anthropic import failed: {e}")
    
    # Check what's installed
    print("\n3. Checking installed packages...")
    import subprocess
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True)
        if 'anthropic' in result.stdout:
            print("✅ anthropic package is installed")
            for line in result.stdout.split('\n'):
                if 'anthropic' in line.lower():
                    print(f"   {line}")
        else:
            print("❌ anthropic package not found in pip list")
    except Exception as e:
        print(f"❌ Could not check pip list: {e}")

# Test pydantic
print("\n4. Testing pydantic...")
try:
    import pydantic
    print(f"✅ Pydantic imported successfully")
    print(f"   Version: {getattr(pydantic, 'VERSION', getattr(pydantic, '__version__', 'unknown'))}")
except ImportError as e:
    print(f"❌ Pydantic import failed: {e}")

# Test pydantic_core
print("\n5. Testing pydantic_core...")
try:
    import pydantic_core
    print(f"✅ pydantic_core imported successfully")
except ImportError as e:
    print(f"❌ pydantic_core import failed: {e}")

print("\n=== Debug Complete ===")
print("\nTo run this script:")
print("1. Save this as debug_claude.py in your project directory")
print("2. Run: python3.10 debug_claude.py")