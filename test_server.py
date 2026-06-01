#!/usr/bin/env python
import sys
sys.path.insert(0, 'C:\\Users\\aarul\\classification-logs')

print("Testing imports...")
try:
    print("1. Importing FastAPI...")
    from fastapi import FastAPI
    print("   ✓ FastAPI OK")
    
    print("2. Importing server module...")
    import server
    print("   ✓ Server module OK")
    
    print("3. Testing root endpoint...")
    import asyncio
    result = asyncio.run(server.root())
    print(f"   ✓ Root endpoint returned HTML: {len(result)} chars")
    
    print("\n✓ All imports successful!")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
