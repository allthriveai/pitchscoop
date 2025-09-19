#!/usr/bin/env python3
"""
import sys
from pathlib import Path

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

Test Market MCP Tools Integration

Tests the new market domain MCP tools with real Bright Data integration.
Run this script to verify the Bright Data integration is working properly.

Usage:
    python test_market_integration.py
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Add the domains directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'domains'))

from domains.market.mcp.market_mcp_tools import execute_market_mcp_tool


async def test_health_check():
    """Test the health check tool first."""
    print("🔍 Testing Market Health Check...")
    
    result = await execute_market_mcp_tool("market.health_check", {
        "event_id": "test_event_001"
    })
    
    print(f"Health Check Result: {json.dumps(result, indent=2)}")
    return result.get("status") != "unhealthy"


async def test_market_validation():
    """Test market validation with real claims."""
    print("\n💰 Testing Market Validation...")
    
    result = await execute_market_mcp_tool("market.validate_claims", {
        "market_claims": "$50B AI-powered fintech market opportunity",
        "industry": "fintech", 
        "event_id": "test_event_001",
        "team_name": "TestTeam AI Lending"
    })
    
    print(f"Market Validation Result: {json.dumps(result, indent=2)}")
    return result.get("success", False)


async def test_competitor_analysis():
    """Test competitor analysis."""
    print("\n🏢 Testing Competitor Analysis...")
    
    result = await execute_market_mcp_tool("market.analyze_competitors", {
        "company_description": "AI-powered micro-lending platform for underbanked populations using machine learning for credit scoring",
        "industry": "fintech",
        "event_id": "test_event_001", 
        "team_name": "TestTeam AI Lending",
        "max_competitors": 5
    })
    
    print(f"Competitor Analysis Result: {json.dumps(result, indent=2)}")
    return result.get("success", False)


async def test_industry_trends():
    """Test industry trends analysis."""
    print("\n📈 Testing Industry Trends Analysis...")
    
    result = await execute_market_mcp_tool("market.industry_trends", {
        "industry": "artificial intelligence",
        "keywords": ["AI lending", "fintech", "credit scoring"],
        "event_id": "test_event_001",
        "timeframe": "3months"
    })
    
    print(f"Industry Trends Result: {json.dumps(result, indent=2)}")
    return result.get("success", False)


async def test_error_handling():
    """Test error handling with invalid inputs."""
    print("\n⚠️  Testing Error Handling...")
    
    # Test with missing required parameter
    result = await execute_market_mcp_tool("market.validate_claims", {
        "industry": "fintech",
        "event_id": "test_event_001"
        # Missing required 'market_claims'
    })
    
    print(f"Error Handling Test: {json.dumps(result, indent=2)}")
    return "error" in result and "missing_parameters" in result.get("error_type", "")


async def test_unknown_tool():
    """Test with unknown tool name."""
    print("\n❌ Testing Unknown Tool Handling...")
    
    result = await execute_market_mcp_tool("market.fake_tool", {
        "event_id": "test_event_001"
    })
    
    print(f"Unknown Tool Test: {json.dumps(result, indent=2)}")
    return "error" in result and "unknown_tool" in result.get("error_type", "")


def print_summary(test_results):
    """Print test summary."""
    print("\n" + "="*60)
    print("🧪 MARKET MCP TOOLS TEST SUMMARY")
    print("="*60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<30} {status}")
    
    print(f"\nTests Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Market MCP integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        
        # Print troubleshooting tips
        print("\n🔧 TROUBLESHOOTING TIPS:")
        print("- Make sure Docker containers are running: docker-compose up")
        print("- Check .env file has BRIGHT_DATA_API_KEY set (or it will use mock mode)")
        print("- Verify Redis is accessible on localhost:6379")
        print("- Check the logs for detailed error information")
    
    return passed_tests == total_tests


async def main():
    """Run all market integration tests."""
    print("🚀 Starting Market MCP Tools Integration Test")
    print(f"📅 Test Time: {datetime.now().isoformat()}")
    print("="*60)
    
    # Check if we're in mock mode
    api_key = os.getenv("BRIGHT_DATA_API_KEY")
    if not api_key or api_key == "your_bright_data_api_key_here":
        print("⚠️  No BRIGHT_DATA_API_KEY found - running in MOCK MODE")
        print("   This will test the integration without making real API calls")
        print("   Set BRIGHT_DATA_API_KEY in your environment for real testing")
    else:
        print("✅ BRIGHT_DATA_API_KEY found - will make real API calls")
    
    print("-" * 60)
    
    # Run all tests
    test_results = {}
    
    try:
        test_results["Health Check"] = await test_health_check()
        test_results["Market Validation"] = await test_market_validation()
        test_results["Competitor Analysis"] = await test_competitor_analysis()
        test_results["Industry Trends"] = await test_industry_trends()
        test_results["Error Handling"] = await test_error_handling()
        test_results["Unknown Tool"] = await test_unknown_tool()
    
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR during testing: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
    
    # Print results
    all_passed = print_summary(test_results)
    
    if all_passed:
        print("\n🎯 NEXT STEPS:")
        print("1. Integration is working! You can now use these MCP tools:")
        print("   - market.validate_claims")
        print("   - market.analyze_competitors") 
        print("   - market.industry_trends")
        print("   - market.health_check")
        print("2. Add real Bright Data API key to test with live data")
        print("3. Integrate these tools into your chat or scoring domains")
        
    return all_passed


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)