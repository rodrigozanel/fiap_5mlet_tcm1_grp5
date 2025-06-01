#!/usr/bin/env python3
"""
Simplified Error Handling and Logging Tests

This test suite validates the robust error handling and logging implementation
for the three-layer cache system, focusing on cache layer functionality.

Tests various failure scenarios to ensure graceful degradation and proper logging.
"""

import unittest
import tempfile
import os
import shutil
import csv
import logging
from unittest.mock import patch, MagicMock, Mock
from io import StringIO
from cache.cache_manager import CacheManager
from utils import get_content_with_cache
import requests


class TestCacheErrorHandling(unittest.TestCase):
    """Test cache error handling and logging functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for CSV files
        self.temp_dir = tempfile.mkdtemp()
        
        # Set environment variable for CSV fallback directory
        os.environ['CSV_FALLBACK_DIR'] = self.temp_dir
        
        # Create sample CSV files
        self.create_sample_csv_files()
        
        # Set up logging capture
        self.log_capture = StringIO()
        self.log_handler = logging.StreamHandler(self.log_capture)
        self.log_handler.setLevel(logging.DEBUG)
        
        # Set up logger
        self.logger = logging.getLogger('test_logger')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.log_handler)
        
        # Initialize CacheManager
        self.cache_manager = CacheManager()
    
    def tearDown(self):
        """Clean up test environment"""
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Clean environment variable
        if 'CSV_FALLBACK_DIR' in os.environ:
            del os.environ['CSV_FALLBACK_DIR']
        
        # Remove log handler
        self.logger.removeHandler(self.log_handler)
    
    def create_sample_csv_files(self):
        """Create sample CSV files for testing"""
        # Producao.csv
        producao_data = [
            ['Produto', 'Quantidade (L.)', 'Ano'],
            ['VINHO DE MESA', '123456789', '2023'],
            ['VINHO FINO DE MESA (VINIFERA)', '987654321', '2023'],
            ['TOTAL GERAL', '1567890233', '2023']
        ]
        
        with open(os.path.join(self.temp_dir, 'Producao.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(producao_data)
    
    def get_log_contents(self):
        """Get captured log contents"""
        return self.log_capture.getvalue()
    
    def test_csv_fallback_success_logging(self):
        """Test logging for successful CSV fallback"""
        print("\n🧪 Testing CSV fallback success logging...")
        
        # Mock Redis as unavailable to force CSV fallback
        with patch('cache.cache_manager.is_redis_available', return_value=False):
            # Test CSV fallback directly
            result = self.cache_manager.get_csv_fallback('producao')
            
            # Should return data
            self.assertIsNotNone(result)
            self.assertEqual(result['cached'], 'csv_fallback')
            
            print("✅ CSV fallback success logging test passed")
    
    def test_error_context_logging(self):
        """Test error context logging for debugging"""
        print("\n🧪 Testing error context logging...")
        
        # Test CSV fallback with invalid endpoint
        result = self.cache_manager.get_csv_fallback('invalid_endpoint', {'sub_option': 'test'})
        
        # Should return None
        self.assertIsNone(result)
        
        print("✅ Error context logging test passed")
    
    @patch('cache.cache_manager.is_redis_available')
    def test_redis_unavailable_logging(self, mock_redis_available):
        """Test logging when Redis is unavailable"""
        print("\n🧪 Testing Redis unavailable logging...")
        
        # Mock Redis as unavailable
        mock_redis_available.return_value = False
        
        # Test short cache
        result = self.cache_manager.get_short_cache('test_endpoint')
        self.assertIsNone(result)
        
        # Test fallback cache
        result = self.cache_manager.get_fallback_cache('test_endpoint')
        self.assertIsNone(result)
        
        # Test cache storage
        success = self.cache_manager.set_short_cache('test_endpoint', {'test': 'data'})
        self.assertFalse(success)
        
        success = self.cache_manager.set_fallback_cache('test_endpoint', {'test': 'data'})
        self.assertFalse(success)
        
        print("✅ Redis unavailable logging test passed")
    
    def test_corrupted_cache_data_logging(self):
        """Test logging for corrupted cache data"""
        print("\n🧪 Testing corrupted cache data logging...")
        
        # Mock Redis with corrupted data
        with patch('cache.cache_manager.is_redis_available', return_value=True):
            with patch('cache.cache_manager.get_redis_client') as mock_redis:
                mock_client = Mock()
                mock_client.get.return_value = 'corrupted json data'
                mock_redis.return_value = mock_client
                
                # Test short cache retrieval
                result = self.cache_manager.get_short_cache('test_endpoint')
                
                # Should return None due to corruption
                self.assertIsNone(result)
                
                print("✅ Corrupted cache data logging test passed")
    
    @patch('requests.get')
    @patch('cache.cache_manager.is_redis_available')
    def test_three_layer_fallback_chain(self, mock_redis_available, mock_requests):
        """Test the complete three-layer fallback chain"""
        print("\n🧪 Testing three-layer fallback chain...")
        
        # Mock Redis as unavailable
        mock_redis_available.return_value = False
        
        # Mock requests to raise timeout
        mock_requests.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # Test get_content_with_cache with valid endpoint that has CSV mapping
        result, cached = get_content_with_cache(
            'producao',  # Use valid endpoint
            'http://test.com', 
            self.cache_manager, 
            self.logger
        )
        
        # Should return CSV fallback data
        self.assertIsNotNone(result)
        self.assertEqual(cached, 'csv_fallback')
        
        print("✅ Three-layer fallback chain test passed")
    
    @patch('requests.get')
    @patch('cache.cache_manager.is_redis_available')
    def test_all_layers_fail_logging(self, mock_redis_available, mock_requests):
        """Test logging when all three layers fail"""
        print("\n🧪 Testing all layers failure logging...")
        
        # Mock Redis as unavailable
        mock_redis_available.return_value = False
        
        # Mock requests to raise error
        mock_requests.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        # Test get_content_with_cache with invalid endpoint
        result, cached = get_content_with_cache(
            'invalid_endpoint', 
            'http://test.com', 
            self.cache_manager, 
            self.logger
        )
        
        # Should return None
        self.assertIsNone(result)
        self.assertFalse(cached)
        
        # Check logs for proper failure chain
        logs = self.get_log_contents()
        self.assertIn("Layer 1 MISS", logs)
        self.assertIn("CONNECTION ERROR", logs)
        self.assertIn("Layer 2 MISS", logs)
        self.assertIn("Layer 3 MISS", logs)
        self.assertIn("ALL LAYERS FAILED", logs)
        
        print("✅ All layers failure logging test passed")
    
    def test_cache_stats_functionality(self):
        """Test comprehensive cache statistics"""
        print("\n🧪 Testing cache statistics functionality...")
        
        # Get cache stats
        stats = self.cache_manager.get_cache_stats()
        
        # Should have proper structure
        self.assertIn('timestamp', stats)
        self.assertIn('cache_layers', stats)
        self.assertIn('short_term', stats['cache_layers'])
        self.assertIn('fallback', stats['cache_layers'])
        self.assertIn('csv_fallback', stats['cache_layers'])
        
        print("✅ Cache statistics functionality test passed")


def run_simplified_error_tests():
    """Run simplified error handling tests and display results"""
    print("🚀 Running Simplified Error Handling Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test class
    suite.addTests(loader.loadTestsFromTestCase(TestCacheErrorHandling))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=None)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Simplified Error Handling Test Results:")
    print(f"✅ Tests Run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"🚫 Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, trace in result.failures:
            print(f"  - {test}: {trace}")
    
    if result.errors:
        print("\n🚫 ERRORS:")
        for test, trace in result.errors:
            print(f"  - {test}: {trace}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if result.wasSuccessful():
        print("🎉 All simplified error handling tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Review the failures above.")
        return False


if __name__ == "__main__":
    # Run the tests when script is executed directly
    success = run_simplified_error_tests()
    exit(0 if success else 1) 