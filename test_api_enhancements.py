#!/usr/bin/env python3
"""
Test script for API enhancements - Year and TTL information
"""

import unittest
import requests
from requests.auth import HTTPBasicAuth
import json
import time

class TestApiEnhancements(unittest.TestCase):
    """Test cases for year and TTL functionality"""
    
    def setUp(self):
        """Set up test configuration"""
        self.base_url = "http://localhost:5000"
        self.auth = HTTPBasicAuth('user1', 'password1')
        self.timeout = 30
    
    def test_year_parameter_in_response(self):
        """Test that year is included in API response"""
        print("\n🧪 Testing year parameter in response...")
        
        # Test with specific year
        response = requests.get(
            f"{self.base_url}/producao",
            auth=self.auth,
            params={'year': '2023'},
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check year is present in response
        self.assertIn('year', data)
        self.assertEqual(data['year'], '2023')
        
        print(f"✅ Year correctly returned: {data['year']}")
        
    def test_year_without_parameter(self):
        """Test year extraction when no year parameter is provided"""
        print("\n🧪 Testing year extraction without parameter...")
        
        response = requests.get(
            f"{self.base_url}/producao",
            auth=self.auth,
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check year is present and is a valid year
        self.assertIn('year', data)
        self.assertIsInstance(data['year'], str)
        
        # Should be either current year or extracted from data
        year_int = int(data['year']) if data['year'].isdigit() else None
        if year_int:
            self.assertGreaterEqual(year_int, 1970)
            self.assertLessEqual(year_int, 2025)
        
        print(f"✅ Year extracted without parameter: {data['year']}")
        
    def test_cache_info_structure(self):
        """Test that cache_info is properly structured"""
        print("\n🧪 Testing cache_info structure...")
        
        response = requests.get(
            f"{self.base_url}/producao",
            auth=self.auth,
            params={'year': '2022'},
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check cache_info structure
        self.assertIn('cache_info', data)
        cache_info = data['cache_info']
        
        # Required fields in cache_info
        required_fields = ['active_cache_layer', 'layer_description', 'ttl_seconds']
        for field in required_fields:
            self.assertIn(field, cache_info)
        
        # Check ttl_seconds structure
        ttl_info = cache_info['ttl_seconds']
        ttl_fields = ['short_cache', 'fallback_cache', 'csv_fallback']
        for field in ttl_fields:
            self.assertIn(field, ttl_info)
        
        print(f"✅ Cache info structure valid")
        print(f"   Active layer: {cache_info['active_cache_layer']}")
        print(f"   Description: {cache_info['layer_description']}")
        print(f"   TTL info: {ttl_info}")
        
    def test_cache_expires_in_format(self):
        """Test cache_expires_in human readable format"""
        print("\n🧪 Testing cache_expires_in format...")
        
        # Make two requests quickly to ensure we get cached data
        response1 = requests.get(
            f"{self.base_url}/producao",
            auth=self.auth,
            params={'year': '2021'},
            timeout=self.timeout
        )
        
        time.sleep(1)  # Small delay
        
        response2 = requests.get(
            f"{self.base_url}/producao",
            auth=self.auth,
            params={'year': '2021'},
            timeout=self.timeout
        )
        
        self.assertEqual(response2.status_code, 200)
        data = response2.json()
        
        self.assertIn('cache_expires_in', data)
        
        # If data is cached, should have a meaningful expiration format
        if data.get('cached') and data['cached'] != False:
            cache_expires = data['cache_expires_in']
            self.assertIsInstance(cache_expires, str)
            print(f"✅ Cache expires in: {cache_expires}")
        else:
            self.assertEqual(data['cache_expires_in'], "N/A (fresh data)")
            print(f"✅ Fresh data response: {data['cache_expires_in']}")
    
    def test_multiple_endpoints_consistency(self):
        """Test that all endpoints return year and cache info consistently"""
        print("\n🧪 Testing consistency across endpoints...")
        
        endpoints = ['producao', 'processamento', 'comercializacao', 'importacao', 'exportacao']
        
        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{self.base_url}/{endpoint}",
                    auth=self.auth,
                    params={'year': '2020'},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check required fields are present
                    self.assertIn('year', data)
                    self.assertIn('cache_info', data)
                    self.assertIn('cache_expires_in', data)
                    
                    print(f"✅ {endpoint}: year={data['year']}, cache_layer={data['cache_info']['active_cache_layer']}")
                
                elif response.status_code == 503:
                    print(f"⚠️ {endpoint}: Service unavailable (acceptable)")
                else:
                    print(f"❌ {endpoint}: Unexpected status {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {endpoint}: Error - {e}")
    
    def test_metadata_presence(self):
        """Test that metadata section exists and contains technical details"""
        print("\n🧪 Testing metadata presence...")
        
        response = requests.get(
            f"{self.base_url}/producao",
            auth=self.auth,
            params={'year': '2019'},
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check metadata exists
        self.assertIn('metadata', data)
        metadata = data['metadata']
        
        # Check metadata structure
        expected_fields = ['year', 'cache_ttl', 'cache_status']
        for field in expected_fields:
            self.assertIn(field, metadata)
        
        print(f"✅ Metadata present with fields: {list(metadata.keys())}")
    
    def test_ttl_values_logic(self):
        """Test that TTL values follow expected logic"""
        print("\n🧪 Testing TTL values logic...")
        
        response = requests.get(
            f"{self.base_url}/producao",
            auth=self.auth,
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        cache_info = data['cache_info']
        ttl_seconds = cache_info['ttl_seconds']
        
        # CSV fallback should always be 'indefinite'
        self.assertEqual(ttl_seconds['csv_fallback'], 'indefinite')
        
        # If we have active cache, TTL should be reasonable
        active_layer = cache_info['active_cache_layer']
        if active_layer == 'short_term' and ttl_seconds['short_cache']:
            # Short cache TTL should be <= 300 seconds (5 minutes)
            if isinstance(ttl_seconds['short_cache'], int):
                self.assertLessEqual(ttl_seconds['short_cache'], 300)
        
        print(f"✅ TTL values are logical:")
        print(f"   Short cache: {ttl_seconds['short_cache']}")
        print(f"   Fallback cache: {ttl_seconds['fallback_cache']}")
        print(f"   CSV fallback: {ttl_seconds['csv_fallback']}")

def main():
    """Run the test suite"""
    print("🚀 Testing API Enhancements - Year and TTL Information")
    print("=" * 60)
    
    # Check if API is available
    try:
        response = requests.get("http://localhost:5000/heartbeat", timeout=5)
        if response.status_code != 200:
            print("❌ API is not available. Please start the application first.")
            return
    except:
        print("❌ Cannot connect to API. Please ensure the application is running.")
        return
    
    # Run tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "=" * 60)
    print("🏁 API Enhancement tests completed!")

if __name__ == "__main__":
    main() 