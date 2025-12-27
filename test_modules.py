#!/usr/bin/env python3
"""Simple test script to verify TradeBrain modules are working."""

import sys
import os

# Add server_src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server_src'))

def test_imports():
    """Test that all modules import correctly."""
    print("🔍 Testing imports...")
    try:
        import config
        print("  ✅ config imported")
        
        from database import DatabaseManager
        print("  ✅ DatabaseManager imported")
        
        from model_engine import ModelEngine
        print("  ✅ ModelEngine imported")
        
        from server_core import ServerCore
        print("  ✅ ServerCore imported")
        
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_initialization():
    """Test that core objects initialize."""
    print("\n🔨 Testing initialization...")
    try:
        from database import DatabaseManager
        from model_engine import ModelEngine
        from server_core import ServerCore
        
        print("  Initializing DatabaseManager...")
        db = DatabaseManager()
        print("  ✅ DatabaseManager initialized")
        
        print("  Initializing ModelEngine...")
        model = ModelEngine()
        print("  ✅ ModelEngine initialized")
        
        print("  Initializing ServerCore...")
        server = ServerCore(db, model)
        print("  ✅ ServerCore initialized")
        
        return True
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_server_start():
    """Test that server starts."""
    print("\n🚀 Testing server start...")
    try:
        from database import DatabaseManager
        from model_engine import ModelEngine
        from server_core import ServerCore
        
        db = DatabaseManager()
        model = ModelEngine()
        server = ServerCore(db, model)
        server.start()
        print("  ✅ Server started successfully")
        return True
    except Exception as e:
        print(f"  ❌ Server start failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("TradeBrain v1.0 Module Test")
    print("=" * 50)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Initialization", test_initialization()))
    results.append(("Server Start", test_server_start()))
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:20} {status}")
    
    all_passed = all(p for _, p in results)
    print("=" * 50)
    if all_passed:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed")
        sys.exit(1)
