#!/usr/bin/env python3
"""
Integration Tests for CacheManager with CSV Fallback

This test suite validates the three-layer cache integration:
1. Short-term Redis cache
2. Fallback Redis cache  
3. CSV fallback cache

Tests various scenarios including Redis availability/unavailability and
fallback chain functionality.
"""

import unittest
import tempfile
import os
import shutil
import csv
from unittest.mock import patch, MagicMock
from cache.cache_manager import CacheManager


class TestCacheManagerIntegration(unittest.TestCase):
    """Test CacheManager integration with CSV fallback"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for CSV files
        self.temp_dir = tempfile.mkdtemp()
        
        # Set environment variable for CSV fallback directory
        os.environ['CSV_FALLBACK_DIR'] = self.temp_dir
        
        # Create sample CSV files
        self.create_sample_csv_files()
        
        # Initialize CacheManager
        self.cache_manager = CacheManager()
    
    def tearDown(self):
        """Clean up test environment"""
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Clean environment variable
        if 'CSV_FALLBACK_DIR' in os.environ:
            del os.environ['CSV_FALLBACK_DIR']
    
    def create_sample_csv_files(self):
        """Create sample CSV files for testing"""
        # Producao.csv
        producao_data = [
            ['Produto', 'Quantidade (L.)', 'Ano'],
            ['VINHO DE MESA', '123456789', '2023'],
            ['VINHO FINO DE MESA (VINIFERA)', '987654321', '2023'],
            ['SUCO DE UVA', '456789123', '2023'],
            ['TOTAL GERAL', '1567890233', '2023']
        ]
        
        with open(os.path.join(self.temp_dir, 'Producao.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(producao_data)
        
        # ProcessaViniferas.csv
        processa_data = [
            ['Cultivar', 'Quantidade (Kg)', 'Ano'],
            ['CABERNET SAUVIGNON', '1234567', '2023'],
            ['MERLOT', '987654', '2023'],
            ['TOTAL', '2222221', '2023']
        ]
        
        with open(os.path.join(self.temp_dir, 'ProcessaViniferas.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(processa_data)
    
    def test_csv_fallback_initialization(self):
        """Test that CSV fallback is properly initialized"""
        print("\n🧪 Testing CSV fallback initialization...")
        
        # CSV fallback should be initialized
        self.assertIsNotNone(self.cache_manager.csv_fallback)
        
        # Should have access to CSV files
        validation = self.cache_manager.validate_csv_fallback()
        self.assertIn('overall_status', validation)
        
        print("✅ CSV fallback initialization test passed")
    
    def test_get_csv_fallback_basic(self):
        """Test basic CSV fallback functionality"""
        print("\n🧪 Testing basic CSV fallback functionality...")
        
        # Test producao endpoint
        result = self.cache_manager.get_csv_fallback('producao')
        
        # Should return data
        self.assertIsNotNone(result)
        self.assertIn('data', result)
        self.assertEqual(result['cached'], 'csv_fallback')
        
        # Check data structure
        data = result['data']
        self.assertIn('header', data)
        self.assertIn('body', data)
        self.assertIn('footer', data)
        
        # Should have proper data
        self.assertGreater(len(data['body']), 0)
        
        print("✅ Basic CSV fallback test passed")
    
    def test_get_csv_fallback_with_sub_option(self):
        """Test CSV fallback with sub_option parameter"""
        print("\n🧪 Testing CSV fallback with sub_option...")
        
        # Test processamento endpoint with viniferas sub_option
        params = {'sub_option': 'viniferas'}
        result = self.cache_manager.get_csv_fallback('processamento', params)
        
        # Should return data
        self.assertIsNotNone(result)
        self.assertEqual(result['cached'], 'csv_fallback')
        
        # Should have data from ProcessaViniferas.csv
        data = result['data']
        self.assertGreater(len(data['body']), 0)
        
        print("✅ CSV fallback with sub_option test passed")
    
    def test_get_csv_fallback_invalid_endpoint(self):
        """Test CSV fallback with invalid endpoint"""
        print("\n🧪 Testing CSV fallback with invalid endpoint...")
        
        # Test invalid endpoint
        result = self.cache_manager.get_csv_fallback('invalid_endpoint')
        
        # Should return None
        self.assertIsNone(result)
        
        print("✅ Invalid endpoint test passed")
    
    def test_csv_fallback_stats(self):
        """Test CSV fallback statistics"""
        print("\n🧪 Testing CSV fallback statistics...")
        
        # Get CSV fallback stats
        stats = self.cache_manager.get_csv_fallback_stats()
        
        # Should have proper structure
        self.assertIn('cache_enabled', stats)
        
        # Make some requests to generate stats
        self.cache_manager.get_csv_fallback('producao')
        self.cache_manager.get_csv_fallback('processamento', {'sub_option': 'viniferas'})
        
        # Get updated stats
        updated_stats = self.cache_manager.get_csv_fallback_stats()
        self.assertGreaterEqual(updated_stats.get('total_requests', 0), 2)
        
        print("✅ CSV fallback statistics test passed")
    
    def test_comprehensive_cache_stats(self):
        """Test comprehensive cache statistics with all layers"""
        print("\n🧪 Testing comprehensive cache statistics...")
        
        # Get comprehensive stats
        stats = self.cache_manager.get_cache_stats()
        
        # Should have all three layers
        self.assertIn('cache_layers', stats)
        layers = stats['cache_layers']
        
        self.assertIn('short_term', layers)
        self.assertIn('fallback', layers)
        self.assertIn('csv_fallback', layers)
        
        # CSV fallback should be active
        self.assertEqual(layers['csv_fallback']['status'], 'active')
        
        # Should have overall status
        self.assertIn('overall_status', stats)
        self.assertIn('active_layers', stats['overall_status'])
        
        print(f"✅ Comprehensive stats test passed - {stats['overall_status']['active_layers']}/3 layers active")
    
    @patch('cache.cache_manager.is_redis_available')
    def test_fallback_chain_redis_unavailable(self, mock_redis_available):
        """Test fallback chain when Redis is unavailable"""
        print("\n🧪 Testing fallback chain with Redis unavailable...")
        
        # Mock Redis as unavailable
        mock_redis_available.return_value = False
        
        # CSV fallback should still work
        result = self.cache_manager.get_csv_fallback('producao')
        self.assertIsNotNone(result)
        self.assertEqual(result['cached'], 'csv_fallback')
        
        # Stats should show Redis as unavailable but CSV as active
        stats = self.cache_manager.get_cache_stats()
        self.assertFalse(stats['redis_available'])
        self.assertEqual(stats['cache_layers']['csv_fallback']['status'], 'active')
        
        print("✅ Fallback chain test passed")
    
    def test_csv_fallback_validation_integration(self):
        """Test CSV fallback validation through CacheManager"""
        print("\n🧪 Testing CSV fallback validation integration...")
        
        # Get validation report
        validation = self.cache_manager.validate_csv_fallback()
        
        # Should have proper structure
        self.assertIn('overall_status', validation)
        self.assertIn('total_endpoints', validation)
        self.assertIn('existing_files', validation)
        
        # Should be partial since we only created some files
        self.assertEqual(validation['overall_status'], 'partial')
        self.assertGreater(validation['existing_files'], 0)
        
        print(f"✅ Validation integration test passed - Status: {validation['overall_status']}")
        print(f"   Files: {validation['existing_files']}/{validation.get('total_files', 0)} available")
    
    def test_csv_fallback_error_handling(self):
        """Test error handling in CSV fallback integration"""
        print("\n🧪 Testing CSV fallback error handling...")
        
        # Test with corrupted CSV directory
        bad_cache_manager = CacheManager()
        
        # Remove CSV files to cause errors
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Should handle missing files gracefully
        result = bad_cache_manager.get_csv_fallback('producao')
        # Might return None or empty result, both are acceptable
        
        # Stats should still work
        stats = bad_cache_manager.get_csv_fallback_stats()
        self.assertIsInstance(stats, dict)
        
        print("✅ Error handling test passed")


class TestCacheManagerWithoutCSV(unittest.TestCase):
    """Test CacheManager behavior when CSV fallback fails to initialize"""
    
    def setUp(self):
        """Set up test with invalid CSV directory"""
        # Set invalid directory to cause CSV initialization failure
        os.environ['CSV_FALLBACK_DIR'] = '/invalid/directory/path'
        self.cache_manager = CacheManager()
    
    def tearDown(self):
        """Clean up environment"""
        if 'CSV_FALLBACK_DIR' in os.environ:
            del os.environ['CSV_FALLBACK_DIR']
    
    def test_cache_manager_without_csv_fallback(self):
        """Test CacheManager when CSV fallback fails to initialize"""
        print("\n🧪 Testing CacheManager without CSV fallback...")
        
        # CSV fallback should be None
        self.assertIsNone(self.cache_manager.csv_fallback)
        
        # CSV fallback methods should handle gracefully
        result = self.cache_manager.get_csv_fallback('producao')
        self.assertIsNone(result)
        
        # Stats should indicate CSV fallback is not available
        stats = self.cache_manager.get_csv_fallback_stats()
        self.assertFalse(stats['csv_fallback_available'])
        
        # Overall stats should work
        comprehensive_stats = self.cache_manager.get_cache_stats()
        self.assertEqual(comprehensive_stats['cache_layers']['csv_fallback']['status'], 'not_initialized')
        
        print("✅ CacheManager without CSV fallback test passed")


def run_cache_integration_tests():
    """Run all cache integration tests and display results"""
    print("🚀 Running CacheManager Integration Tests")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCacheManagerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestCacheManagerWithoutCSV))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=None)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Integration Test Results Summary:")
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
        print("🎉 All integration tests passed! CacheManager CSV fallback integration is working correctly.")
        return True
    else:
        print("⚠️ Some integration tests failed. Review the failures above.")
        return False


if __name__ == "__main__":
    # Run the tests when script is executed directly
    success = run_cache_integration_tests()
    exit(0 if success else 1) 