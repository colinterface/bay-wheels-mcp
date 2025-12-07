#!/usr/bin/env python3
"""
Test script for Bay Wheels MCP Server (HTTP/StreamableHTTP transport)

Usage:
    python test_mcp_server.py <server_url>

Examples:
    python test_mcp_server.py http://localhost:8000
    python test_mcp_server.py https://your-server.fly.io
"""

import sys
import json
import httpx
import asyncio


async def test_health_check(base_url: str):
    """Test the /health endpoint"""
    print(f"\n🏥 Testing health check endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def test_mcp_initialize(base_url: str):
    """Test MCP initialization"""
    print(f"\n🔧 Testing MCP initialization...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }

            response = await client.post(
                f"{base_url}/mcp",
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )

            print(f"   Status: {response.status_code}")
            result = response.json()
            print(f"   Server: {result.get('result', {}).get('serverInfo', {}).get('name', 'unknown')}")
            print(f"   Version: {result.get('result', {}).get('serverInfo', {}).get('version', 'unknown')}")
            print(f"   Protocol: {result.get('result', {}).get('protocolVersion', 'unknown')}")

            # Check for tools
            if 'tools' in result.get('result', {}).get('capabilities', {}):
                print(f"   ✅ Server supports tools")

            return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def test_list_tools(base_url: str):
    """Test listing available tools"""
    print(f"\n🛠️  Testing tools/list...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }

            response = await client.post(
                f"{base_url}/mcp",
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )

            print(f"   Status: {response.status_code}")
            result = response.json()

            tools = result.get('result', {}).get('tools', [])
            print(f"   Available tools: {len(tools)}")
            for tool in tools:
                print(f"      - {tool.get('name')}: {tool.get('description', 'No description')[:60]}...")

            return response.status_code == 200 and len(tools) > 0
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def test_find_nearest_bike(base_url: str):
    """Test the find_nearest_bike tool with SF coordinates"""
    print(f"\n🚲 Testing find_nearest_bike tool...")
    print(f"   Location: San Francisco Ferry Building (37.7955, -122.3937)")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "find_nearest_bike",
                    "arguments": {
                        "latitude": 37.7955,
                        "longitude": -122.3937,
                        "count": 1
                    }
                }
            }

            response = await client.post(
                f"{base_url}/mcp",
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )

            print(f"   Status: {response.status_code}")
            result = response.json()

            if 'result' in result:
                content = result['result'].get('content', [])
                if content and len(content) > 0:
                    text = content[0].get('text', '')
                    print(f"   Result:\n      {text.replace(chr(10), chr(10) + '      ')}")
                    return True
                else:
                    print(f"   ⚠️  No content in result")
                    return False
            else:
                print(f"   ❌ Error in response: {result.get('error', 'Unknown error')}")
                return False

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def test_find_nearest_dock(base_url: str):
    """Test the find_nearest_dock_spaces tool"""
    print(f"\n🅿️  Testing find_nearest_dock_spaces tool...")
    print(f"   Location: SF Ferry Building (37.7955, -122.3937)")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            request = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "find_nearest_dock_spaces",
                    "arguments": {
                        "latitude": 37.7955,
                        "longitude": -122.3937,
                        "count": 1
                    }
                }
            }

            response = await client.post(
                f"{base_url}/mcp",
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )

            print(f"   Status: {response.status_code}")
            result = response.json()

            if 'result' in result:
                content = result['result'].get('content', [])
                if content and len(content) > 0:
                    text = content[0].get('text', '')
                    print(f"   Result:\n      {text.replace(chr(10), chr(10) + '      ')}")
                    return True
                else:
                    print(f"   ⚠️  No content in result")
                    return False
            else:
                print(f"   ❌ Error in response: {result.get('error', 'Unknown error')}")
                return False

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_mcp_server.py <server_url>")
        print("\nExamples:")
        print("  python test_mcp_server.py http://localhost:8000")
        print("  python test_mcp_server.py https://your-server.fly.io")
        sys.exit(1)

    base_url = sys.argv[1].rstrip('/')

    print("=" * 70)
    print(f"🧪 Testing Bay Wheels MCP Server")
    print(f"📍 Server URL: {base_url}")
    print("=" * 70)

    results = {}

    # Run tests
    results['health'] = await test_health_check(base_url)
    results['initialize'] = await test_mcp_initialize(base_url)
    results['list_tools'] = await test_list_tools(base_url)
    results['find_bike'] = await test_find_nearest_bike(base_url)
    results['find_dock'] = await test_find_nearest_dock(base_url)

    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")

    print(f"\n   Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Server is working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
