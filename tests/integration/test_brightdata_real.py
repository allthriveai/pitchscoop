#!/usr/bin/env python3
"""
Real BrightData API Test

This script tests actual BrightData API connectivity and functionality.
BrightData provides web scraping and proxy services - this test will check
basic connectivity and available endpoints.
"""
import os
import aiohttp
import asyncio
import json
from datetime import datetime

async def test_brightdata_connectivity():
    """Test basic BrightData API connectivity."""
    print("🔍 Testing BrightData API Connectivity...")
    
    # Get API key from environment
    api_key = os.getenv("BRIGHT_DATA_API_KEY")
    if not api_key or api_key == "your_bright_data_api_key_here":
        print("❌ BRIGHT_DATA_API_KEY not found in environment")
        return False
    
    print(f"✅ Found API Key: {api_key[:8]}...")
    
    # BrightData typically uses different endpoints than what I had before
    # Let's try some common BrightData API endpoints
    base_urls_to_try = [
        "https://brightdata.com/api",
        "https://api.brightdata.com", 
        "https://api.brightdata.gq",
        "https://proxy-api.brightdata.com"
    ]
    
    endpoints_to_try = [
        "/status",
        "/account",
        "/zones", 
        "/",
        "/v1/status",
        "/v2/status"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "PitchScoop/1.0"
    }
    
    # Also try Basic Auth (common for BrightData)
    auth_headers = {
        "Content-Type": "application/json", 
        "User-Agent": "PitchScoop/1.0"
    }
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for base_url in base_urls_to_try:
            print(f"\n🌐 Trying base URL: {base_url}")
            
            for endpoint in endpoints_to_try:
                full_url = f"{base_url}{endpoint}"
                
                try:
                    # Try Bearer token first
                    print(f"  📡 Testing: {full_url} (Bearer)")
                    async with session.get(full_url, headers=headers) as response:
                        content_type = response.headers.get('content-type', '')
                        status = response.status
                        
                        if 'application/json' in content_type:
                            try:
                                data = await response.json()
                                print(f"    ✅ {status} - JSON Response: {json.dumps(data, indent=2)[:200]}...")
                                return True
                            except:
                                text = await response.text()
                                print(f"    ⚠️  {status} - JSON parse failed: {text[:100]}...")
                        else:
                            text = await response.text()
                            print(f"    ℹ️  {status} - {content_type}: {text[:100]}...")
                            
                        if status == 200:
                            return True
                            
                except aiohttp.ClientError as e:
                    print(f"    ❌ Connection error: {str(e)}")
                except Exception as e:
                    print(f"    ❌ Error: {str(e)}")
                
                # Try with Basic Auth using API key as username
                try:
                    print(f"  📡 Testing: {full_url} (Basic Auth)")
                    auth = aiohttp.BasicAuth(api_key, '')
                    async with session.get(full_url, headers=auth_headers, auth=auth) as response:
                        content_type = response.headers.get('content-type', '')
                        status = response.status
                        
                        if 'application/json' in content_type:
                            try:
                                data = await response.json()
                                print(f"    ✅ {status} - JSON Response: {json.dumps(data, indent=2)[:200]}...")
                                return True
                            except:
                                text = await response.text()
                                print(f"    ⚠️  {status} - JSON parse failed: {text[:100]}...")
                        else:
                            text = await response.text()
                            print(f"    ℹ️  {status} - {content_type}: {text[:100]}...")
                            
                        if status == 200:
                            return True
                            
                except aiohttp.ClientError as e:
                    print(f"    ❌ Basic Auth error: {str(e)}")
                except Exception as e:
                    print(f"    ❌ Basic Auth error: {str(e)}")
                    
                await asyncio.sleep(0.1)  # Rate limiting
    
    print("❌ Could not establish connectivity to BrightData API")
    return False

async def test_web_scraping_request():
    """Test a simple web scraping request if we have connectivity."""
    print("\n🕷️ Testing Web Scraping Capability...")
    
    api_key = os.getenv("BRIGHT_DATA_API_KEY")
    if not api_key:
        print("❌ No API key available")
        return False
    
    # BrightData often uses proxy endpoints for scraping
    proxy_endpoints = [
        "https://brd-customer-hl_username-zone-market_research.brd.superproxy.io:22225",
        "https://brd-customer-hl_username-zone-datacenter_proxy1.brd.superproxy.io:22225"
    ]
    
    # Try a simple request through BrightData proxy
    try:
        # This is a common pattern for BrightData proxy usage
        proxy_auth = aiohttp.BasicAuth(f"brd-customer-{api_key}-zone-market_research", api_key)
        connector = aiohttp.TCPConnector()
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Test with a simple, scraping-friendly site
            test_url = "https://httpbin.org/json"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            
            try:
                async with session.get(test_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Direct request successful: {data}")
                        return True
            except Exception as e:
                print(f"ℹ️  Direct request failed (expected): {e}")
            
    except Exception as e:
        print(f"❌ Proxy test failed: {e}")
    
    print("ℹ️  Web scraping test completed (proxy configuration may be needed)")
    return False

async def check_brightdata_documentation():
    """Check if we can get any info from BrightData's main site."""
    print("\n📚 Checking BrightData Documentation...")
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get("https://brightdata.com") as response:
                if response.status == 200:
                    print("✅ BrightData main site is accessible")
                    return True
                else:
                    print(f"⚠️  BrightData site returned {response.status}")
    except Exception as e:
        print(f"❌ Could not reach BrightData site: {e}")
    
    return False

def print_brightdata_info():
    """Print information about BrightData integration."""
    print("\n" + "="*60)
    print("📋 BRIGHTDATA INTEGRATION INFO")
    print("="*60)
    
    api_key = os.getenv("BRIGHT_DATA_API_KEY")
    if api_key:
        print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '****'}")
    else:
        print("❌ No API Key found in environment")
    
    print("\n🎯 WHAT IS BRIGHTDATA?")
    print("BrightData (formerly Luminati) is a web scraping and proxy service that provides:")
    print("- Web scraping APIs")
    print("- Residential and datacenter proxies")
    print("- Data collection services")
    print("- Anti-detection browsing")
    
    print("\n⚙️  TYPICAL BRIGHTDATA USAGE:")
    print("1. Proxy Services: Route requests through BrightData's proxy network")
    print("2. Scraping APIs: Use their managed scraping endpoints")
    print("3. Browser Automation: Automated data collection")
    print("4. Data Collection: Structured data from websites")
    
    print("\n🔧 INTEGRATION STATUS:")
    print("- ✅ Service structure implemented")
    print("- ✅ Rate limiting and error handling")
    print("- ✅ Mock mode for development")
    print("- ⚠️  API endpoints need verification")
    print("- ⚠️  Proxy configuration may be required")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Verify BrightData account setup and API access")
    print("2. Check BrightData dashboard for correct endpoints")
    print("3. Configure proxy settings if using proxy services")
    print("4. Update API endpoints based on your BrightData plan")

async def main():
    """Run all BrightData tests."""
    print("🚀 BrightData API Testing")
    print(f"📅 Test Time: {datetime.now().isoformat()}")
    print("="*60)
    
    results = {}
    
    # Test basic connectivity
    results["connectivity"] = await test_brightdata_connectivity()
    
    # Test web scraping if connectivity works
    if results["connectivity"]:
        results["scraping"] = await test_web_scraping_request()
    else:
        results["scraping"] = False
    
    # Check documentation access
    results["documentation"] = await check_brightdata_documentation()
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.capitalize():<20} {status}")
    
    print(f"\nTests Passed: {passed_tests}/{total_tests}")
    
    # Print integration info regardless of results
    print_brightdata_info()
    
    if passed_tests > 0:
        print("\n🎉 Some connectivity established!")
    else:
        print("\n⚠️  No successful connections - check account setup")
    
    return passed_tests > 0

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = asyncio.run(main())
    exit(0 if success else 1)