# Save this as test_claude_simple.py and run: python3.10 test_claude_simple.py

import os
import sys
import django

# Add the project path
sys.path.append('/home/TAKnox/crm_system/crm_system')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

print("=== Testing Claude AI in Django ===")

# Test 1: Import the service
try:
    from tenders.services.ai_analysis import ClaudeAIService
    print("✅ ClaudeAIService imported successfully")
    
    # Test 2: Create the service
    service = ClaudeAIService()
    print(f"✅ ClaudeAIService created")
    print(f"   Claude available: {service.claude_available}")
    print(f"   Client exists: {service.client is not None}")
    
    # Test 3: Test a simple analysis
    if service.claude_available and service.client:
        print("\n🚀 Testing Claude AI analysis...")
        result = service.analyze_tender_documents(
            "Test Project",
            "Test Location", 
            ["This is a test document for electrical work and plumbing."]
        )
        print(f"✅ Analysis completed!")
        print(f"   Method: {result.get('analysis_method', 'Unknown')}")
        print(f"   Confidence: {result.get('analysis_confidence', 0)}%")
        print(f"   Risk Level: {result.get('risk_level', 'Unknown')}")
        print(f"   Required Trades: {result.get('required_trades', [])}")
    else:
        print("❌ Claude AI not available - service using fallback mode")
        
except Exception as e:
    print(f"❌ Error testing ClaudeAIService: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")