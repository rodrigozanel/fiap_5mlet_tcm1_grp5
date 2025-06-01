"""
CSV Fallback Manager for providing local data when Redis and web scraping fail.

This module implements a third layer of fallback using local CSV files to ensure
API availability even when both Redis and web scraping services are unavailable.
"""

import csv
import os
import logging
import threading
import time
from typing import Dict, List, Any, Optional
from pathlib import Path


# Custom Exceptions for CSV Fallback Manager
class CsvFallbackError(Exception):
    """Base exception for CSV Fallback Manager"""
    pass


class CsvFileError(CsvFallbackError):
    """Exception raised for CSV file-related errors"""
    pass


class CsvParseError(CsvFallbackError):
    """Exception raised for CSV parsing errors"""
    pass


class CsvFormatError(CsvFallbackError):
    """Exception raised for CSV format conversion errors"""
    pass


class CsvCacheError(CsvFallbackError):
    """Exception raised for cache-related errors"""
    pass


class CsvFallbackManager:
    """
    CSV Fallback Manager with optimized caching for providing local data when Redis and web scraping fail.
    
    This class implements a sophisticated third layer of fallback using local CSV files with advanced caching
    to ensure optimal API performance even when both Redis and web scraping services are unavailable.
    """
    
    # Endpoint-to-CSV mapping based on API structure and available CSV files
    ENDPOINT_CSV_MAP = {
        # Produção endpoint
        'producao': {
            'default': 'Producao.csv',
            'sub_options': {
                'VINHO DE MESA': 'Producao.csv',
                'VINHO FINO DE MESA (VINIFERA)': 'Producao.csv',
                'SUCO DE UVA': 'Producao.csv',
                'DERIVADOS': 'Producao.csv'
            }
        },
        
        # Processamento endpoint
        'processamento': {
            'default': 'ProcessaViniferas.csv',
            'sub_options': {
                'viniferas': 'ProcessaViniferas.csv',
                'americanas': 'ProcessaAmericanas.csv',
                'mesa': 'ProcessaMesa.csv',
                'semclass': 'ProcessaSemclass.csv'
            }
        },
        
        # Comercialização endpoint
        'comercializacao': {
            'default': 'Comercio.csv',
            'sub_options': {
                'VINHO DE MESA': 'Comercio.csv',
                'ESPUMANTES': 'Comercio.csv',
                'UVAS FRESCAS': 'Comercio.csv',
                'SUCO DE UVA': 'Comercio.csv'
            }
        },
        
        # Importação endpoint
        'importacao': {
            'default': 'ImpVinhos.csv',
            'sub_options': {
                'vinhos': 'ImpVinhos.csv',
                'espumantes': 'ImpEspumantes.csv',
                'frescas': 'ImpFrescas.csv',
                'passas': 'ImpPassas.csv',
                'suco': 'ImpSuco.csv'
            }
        },
        
        # Exportação endpoint
        'exportacao': {
            'default': 'ExpVinho.csv',
            'sub_options': {
                'vinho': 'ExpVinho.csv',
                'uva': 'ExpUva.csv',
                'espumantes': 'ExpEspumantes.csv',
                'suco': 'ExpSuco.csv'
            }
        }
    }
    
    def __init__(self, csv_directory: str = "data/fallback", cache_enabled: bool = True, 
                 max_cache_size: int = 100, cache_ttl_seconds: int = 3600):
        """
        Initialize the CSV Fallback Manager with enhanced caching configuration.
        
        Args:
            csv_directory (str): Directory containing CSV fallback files
            cache_enabled (bool): Enable in-memory caching for parsed data
            max_cache_size (int): Maximum number of files to cache (default: 100)
            cache_ttl_seconds (int): Cache time-to-live in seconds (default: 3600 = 1 hour)
            
        Raises:
            CsvFileError: If the CSV directory cannot be accessed or created
            CsvCacheError: If cache initialization fails
        """
        try:
            self.csv_directory = Path(csv_directory)
            self.cache_enabled = cache_enabled
            self.max_cache_size = max(1, max_cache_size)  # Ensure at least 1
            self.cache_ttl_seconds = max(60, cache_ttl_seconds)  # Minimum 1 minute TTL
            
            # Initialize logging
            self.logger = logging.getLogger(self.__class__.__name__)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
            
            # Initialize advanced cache with thread safety
            try:
                self._cache: Dict[str, Any] = {}
                self._cache_lock = threading.RLock()  # Reentrant lock for nested operations
                self._cache_access_times: Dict[str, float] = {}  # Track access times for LRU
                self._cache_stats = {
                    'hits': 0,
                    'misses': 0,
                    'errors': 0,
                    'total_files_cached': 0,
                    'evictions': 0,
                    'expired_entries': 0,
                    'cache_size_violations': 0
                }
                
                # Cache configuration
                self._cache_config = {
                    'max_size': self.max_cache_size,
                    'ttl_seconds': self.cache_ttl_seconds,
                    'cleanup_interval': max(300, self.cache_ttl_seconds // 12),  # Cleanup every ~5 minutes or TTL/12
                    'last_cleanup': time.time()
                }
                
                self.logger.debug(f"Advanced cache initialized successfully with max_size={self.max_cache_size}, ttl={self.cache_ttl_seconds}s")
            except Exception as e:
                raise CsvCacheError(f"Failed to initialize advanced cache: {str(e)}") from e
            
            # Validate and create CSV directory if needed
            try:
                if not self.csv_directory.exists():
                    self.logger.warning(f"CSV directory '{csv_directory}' does not exist. Attempting to create...")
                    self.csv_directory.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Created CSV directory: {self.csv_directory}")
                
                # Test directory accessibility
                if not self.csv_directory.is_dir():
                    raise CsvFileError(f"Path '{csv_directory}' exists but is not a directory")
                
                # Test read permissions
                if not os.access(self.csv_directory, os.R_OK):
                    raise CsvFileError(f"No read permission for directory '{csv_directory}'")
                    
                self.logger.info(f"CSV Fallback Manager initialized successfully. Directory: {self.csv_directory}")
                
            except (OSError, PermissionError) as e:
                error_msg = f"Failed to access or create CSV directory '{csv_directory}': {str(e)}"
                self.logger.error(error_msg)
                raise CsvFileError(error_msg) from e
                
        except Exception as e:
            if not isinstance(e, CsvFallbackError):
                # Wrap unexpected errors
                raise CsvFallbackError(f"Unexpected error during initialization: {str(e)}") from e
            raise
    
    def parse_csv_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a CSV file and return its contents as a list of dictionaries with robust error handling.
        
        Args:
            file_path (str): Path to the CSV file to parse (relative to csv_directory)
            
        Returns:
            List[Dict[str, Any]]: Parsed CSV data as list of dictionaries
            
        Raises:
            CsvFileError: If the CSV file cannot be accessed or does not exist
            CsvParseError: If the CSV file is malformed or cannot be parsed
            CsvCacheError: If cache operations fail
        """
        if not file_path:
            raise CsvFileError("File path cannot be empty")
            
        # Construct full file path
        full_path = self.csv_directory / file_path
        
        try:
            # Check cache first if enabled
            if self.cache_enabled:
                try:
                    cached_data = self._retrieve_from_cache(str(full_path))
                    if cached_data is not None:
                        self._cache_stats['hits'] += 1
                        self.logger.debug(f"Cache hit for file: {file_path}")
                        return cached_data
                    else:
                        self._cache_stats['misses'] += 1
                        self.logger.debug(f"Cache miss for file: {file_path}")
                except Exception as e:
                    self._cache_stats['errors'] += 1
                    self.logger.warning(f"Cache error for {file_path}: {str(e)}")
                    # Continue without cache if cache fails
            
            # Validate file existence and accessibility
            try:
                if not full_path.exists():
                    raise CsvFileError(f"CSV file not found: {file_path}")
                
                if not full_path.is_file():
                    raise CsvFileError(f"Path is not a file: {file_path}")
                
                if not os.access(full_path, os.R_OK):
                    raise CsvFileError(f"No read permission for file: {file_path}")
                
                # Check if file is empty
                if full_path.stat().st_size == 0:
                    self.logger.warning(f"CSV file is empty: {file_path}")
                    return []
                    
            except OSError as e:
                raise CsvFileError(f"File system error accessing {file_path}: {str(e)}") from e
            
            # Parse CSV file with multiple encoding attempts and error recovery
            parsed_data = []
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            parsing_success = False
            
            for encoding in encodings_to_try:
                try:
                    self.logger.debug(f"Attempting to parse {file_path} with encoding: {encoding}")
                    
                    with open(full_path, 'r', encoding=encoding, newline='') as csvfile:
                        # Detect delimiter
                        sample = csvfile.read(1024)
                        csvfile.seek(0)
                        
                        # Try common delimiters
                        delimiter = self._detect_delimiter(sample)
                        
                        reader = csv.DictReader(csvfile, delimiter=delimiter)
                        
                        row_count = 0
                        error_rows = []
                        
                        for row_num, row in enumerate(reader, start=2):  # Start at 2 because header is row 1
                            try:
                                # Clean empty values and strip whitespace
                                cleaned_row = {}
                                for key, value in row.items():
                                    if key is not None:  # Skip None keys (malformed headers)
                                        cleaned_key = str(key).strip()
                                        cleaned_value = str(value).strip() if value is not None else ""
                                        cleaned_row[cleaned_key] = cleaned_value
                                
                                # Only add rows that have at least some data
                                if any(value for value in cleaned_row.values()):
                                    parsed_data.append(cleaned_row)
                                    row_count += 1
                                    
                            except Exception as row_error:
                                error_rows.append((row_num, str(row_error)))
                                self.logger.warning(f"Skipping malformed row {row_num} in {file_path}: {str(row_error)}")
                                continue
                        
                        # Log parsing results
                        if error_rows:
                            self.logger.warning(f"Parsed {file_path} with {len(error_rows)} error rows skipped")
                        
                        if row_count == 0:
                            self.logger.warning(f"No valid data rows found in {file_path}")
                        else:
                            self.logger.info(f"Successfully parsed {row_count} rows from {file_path} using {encoding}")
                        
                        parsing_success = True
                        break
                        
                except UnicodeDecodeError:
                    self.logger.debug(f"Encoding {encoding} failed for {file_path}, trying next...")
                    continue
                except csv.Error as csv_err:
                    if encoding == encodings_to_try[-1]:  # Last encoding attempt
                        raise CsvParseError(f"CSV parsing failed for {file_path}: {str(csv_err)}") from csv_err
                    else:
                        self.logger.debug(f"CSV error with {encoding} for {file_path}, trying next encoding...")
                        continue
                except Exception as e:
                    raise CsvParseError(f"Unexpected error parsing {file_path} with {encoding}: {str(e)}") from e
            
            if not parsing_success:
                raise CsvParseError(f"Failed to parse {file_path} with any supported encoding")
            
            # Cache the successful result
            if self.cache_enabled:
                try:
                    cache_key = self._generate_cache_key(str(full_path))
                    success = self._store_in_cache(cache_key, str(full_path), parsed_data)
                    if success:
                        self.logger.debug(f"Successfully cached data for {file_path}")
                    else:
                        self.logger.warning(f"Failed to cache data for {file_path}")
                except Exception as cache_error:
                    self._cache_stats['errors'] += 1
                    self.logger.warning(f"Cache storage error for {file_path}: {str(cache_error)}")
                    # Don't fail the whole operation for cache errors
            
            return parsed_data
            
        except CsvFallbackError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Wrap unexpected errors
            error_msg = f"Unexpected error parsing CSV file {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise CsvParseError(error_msg) from e
    
    def _detect_delimiter(self, sample: str) -> str:
        """Detect CSV delimiter from sample text."""
        try:
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample, delimiters=';,\t|').delimiter
            return delimiter
        except csv.Error:
            # Default to semicolon (common in Embrapa data)
            return ';'
    
    def _generate_cache_key(self, file_path: str) -> str:
        """Generate a cache key based on file path and modification time."""
        try:
            mtime = os.path.getmtime(file_path)
            return f"{file_path}_{mtime}"
        except OSError:
            # Fallback to just file path if we can't get mtime
            return file_path
    
    def _get_cached_data_safe(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """Safely retrieve cached data with error handling."""
        try:
            current_key = self._generate_cache_key(file_path)
            
            for cached_key, cached_value in list(self._cache.items()):
                if cached_value.get('file_path') == file_path:
                    # Check if the file has been modified
                    if cached_key == current_key:
                        return cached_value['data']
                    else:
                        # File was modified, remove stale cache
                        del self._cache[cached_key]
                        self.logger.debug(f"Removed stale cache for {file_path}")
                        break
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error accessing cache for {file_path}: {str(e)}")
            return None
    
    def convert_to_api_format(self, csv_data: List[Dict[str, Any]], endpoint: str = None) -> Dict[str, Any]:
        """
        Convert CSV data to API-compatible format with comprehensive error handling.
        
        Args:
            csv_data (List[Dict[str, Any]]): Parsed CSV data as list of dictionaries
            endpoint (str, optional): API endpoint name for specific formatting rules
            
        Returns:
            Dict[str, Any]: Data in API format with header, body, and footer structure
            
        Raises:
            CsvFormatError: If the data cannot be converted to API format
        """
        try:
            # Input validation
            if csv_data is None:
                raise CsvFormatError("CSV data cannot be None")
            
            if not isinstance(csv_data, list):
                raise CsvFormatError(f"Expected list, got {type(csv_data).__name__}")
            
            # Handle empty data gracefully
            if not csv_data:
                self.logger.debug("No CSV data provided for conversion")
                return {"data": {"header": [], "body": [], "footer": []}}
            
            # Validate data structure
            for i, row in enumerate(csv_data):
                if not isinstance(row, dict):
                    raise CsvFormatError(f"Row {i} is not a dictionary: {type(row).__name__}")
            
            try:
                # Extract headers from first row (with validation)
                if not csv_data[0]:
                    self.logger.warning("First row is empty, using empty headers")
                    headers = []
                else:
                    headers = list(csv_data[0].keys())
                    # Filter out None or empty string keys
                    headers = [h for h in headers if h and str(h).strip()]
                
                # Separate data into body and footer
                body_data = []
                footer_data = []
                
                # Keywords that indicate footer/total rows (case-insensitive)
                footer_keywords = {'total', 'soma', 'subtotal', 'geral', 'consolidado', 'média', 'media'}
                
                processed_rows = 0
                error_rows = 0
                
                for row_index, row in enumerate(csv_data):
                    try:
                        # Skip completely empty rows
                        if not any(str(value).strip() for value in row.values() if value is not None):
                            continue
                        
                        # Convert all values to strings and handle None values
                        row_values = []
                        for header in headers:
                            value = row.get(header, "")
                            if value is None:
                                row_values.append("")
                            else:
                                row_values.append(str(value))
                        
                        # Check if this row should be in footer
                        is_footer = False
                        if row_values:  # Ensure there's at least one value
                            first_value = row_values[0].lower().strip()
                            is_footer = any(keyword in first_value for keyword in footer_keywords)
                        
                        # Add to appropriate section
                        if is_footer:
                            footer_data.append(row_values)
                            self.logger.debug(f"Row {row_index + 1} identified as footer: {row_values[0] if row_values else 'empty'}")
                        else:
                            body_item = {
                                "item_data": row_values,
                                "sub_items": []
                            }
                            body_data.append(body_item)
                        
                        processed_rows += 1
                        
                    except Exception as row_error:
                        error_rows += 1
                        self.logger.warning(f"Error processing row {row_index + 1}: {str(row_error)}")
                        # Continue processing other rows instead of failing completely
                        continue
                
                # Create the API response structure
                api_response = {
                    "data": {
                        "header": [headers] if headers else [],
                        "body": body_data,
                        "footer": footer_data
                    }
                }
                
                # Log conversion results
                log_msg = f"Converted {processed_rows} rows to API format"
                if error_rows > 0:
                    log_msg += f" ({error_rows} rows had errors and were skipped)"
                if endpoint:
                    log_msg += f" for endpoint '{endpoint}'"
                
                self.logger.info(log_msg)
                
                return api_response
                
            except Exception as e:
                # Wrap conversion errors
                raise CsvFormatError(f"Failed to convert CSV data to API format: {str(e)}") from e
                
        except CsvFormatError:
            # Re-raise format errors
            raise
        except Exception as e:
            # Wrap unexpected errors
            error_msg = f"Unexpected error during CSV to API conversion: {str(e)}"
            self.logger.error(error_msg)
            raise CsvFormatError(error_msg) from e
    
    def convert_to_api_format_advanced(self, csv_data: List[Dict[str, Any]], 
                                     endpoint: str = None) -> Dict[str, Any]:
        """
        Advanced conversion with endpoint-specific logic and grouping.
        
        This method provides more sophisticated conversion logic that can:
        - Group related data into item_data/sub_items structure
        - Apply endpoint-specific formatting rules
        - Handle hierarchical data structures from CSV
        
        Args:
            csv_data (List[Dict[str, Any]]): Parsed CSV data
            endpoint (str, optional): Endpoint name for specific logic
            
        Returns:
            Dict[str, Any]: Advanced API-compatible data structure
        """
        if not csv_data:
            return {"data": {"header": [], "body": [], "footer": []}}
        
        try:
            # Start with basic conversion
            basic_result = self.convert_to_api_format(csv_data, endpoint)
            
            # Apply endpoint-specific enhancements
            if endpoint and hasattr(self, f'_enhance_for_{endpoint}'):
                enhancement_method = getattr(self, f'_enhance_for_{endpoint}')
                enhanced_result = enhancement_method(basic_result, csv_data)
                self.logger.info(f"Applied {endpoint}-specific enhancements")
                return enhanced_result
            
            return basic_result
            
        except Exception as e:
            self.logger.error(f"Error in advanced CSV conversion: {e}")
            # Fallback to basic conversion
            return self.convert_to_api_format(csv_data, endpoint)
    
    def _enhance_for_producao(self, basic_data: Dict[str, Any], 
                            csv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enhancement logic specific to 'producao' endpoint.
        
        For production data, we might want to group by product type or year.
        """
        # Implementation can be added later based on specific producao data patterns
        self.logger.debug("Applying producao-specific enhancements")
        return basic_data
    
    def _enhance_for_processamento(self, basic_data: Dict[str, Any], 
                                 csv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enhancement logic specific to 'processamento' endpoint.
        
        For processing data, we might want to group by grape variety.
        """
        # Implementation can be added later based on specific processamento data patterns
        self.logger.debug("Applying processamento-specific enhancements")
        return basic_data
    
    def get_cached_data(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached data for a file with error handling.
        
        Args:
            file_path (str): Path to the file to check in cache
            
        Returns:
            Optional[List[Dict[str, Any]]]: Cached data if available, None otherwise
            
        Raises:
            CsvCacheError: If cache access fails critically
        """
        if not self.cache_enabled:
            return None
            
        try:
            with self._cache_lock:
                return self._get_cached_data_safe(file_path)
        except Exception as e:
            self.logger.warning(f"Cache access error for {file_path}: {str(e)}")
            # Don't raise exception for cache errors, just return None
            return None
    
    def clear_cache(self) -> bool:
        """
        Clear all cached data with error handling.
        
        Returns:
            bool: True if cache was cleared successfully, False otherwise
        """
        if not self.cache_enabled:
            self.logger.debug("Cache is disabled, nothing to clear")
            return True
            
        try:
            with self._cache_lock:
                cache_size = len(self._cache)
                self._cache.clear()
                
                # Reset cache stats
                self._cache_stats = {
                    'hits': 0,
                    'misses': 0,
                    'errors': 0,
                    'total_files_cached': 0
                }
                
                self.logger.info(f"Cache cleared successfully. Removed {cache_size} entries.")
                return True
                
        except Exception as e:
            error_msg = f"Failed to clear cache: {str(e)}"
            self.logger.error(error_msg)
            # Don't raise exception, just return False
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics with advanced metrics.
        
        Returns:
            Dict[str, Any]: Detailed cache statistics including performance and health metrics
        """
        if not self.cache_enabled:
            return {
                'cache_enabled': False,
                'message': 'Cache is disabled'
            }
            
        try:
            with self._cache_lock:
                current_time = time.time()
                current_size = len(self._cache)
                total_requests = self._cache_stats['hits'] + self._cache_stats['misses']
                hit_rate = (self._cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
                
                # Calculate cache utilization
                utilization_percent = (current_size / self.max_cache_size * 100) if self.max_cache_size > 0 else 0
                
                # Calculate average access count
                total_access_count = sum(
                    entry.get('access_count', 0) 
                    for entry in self._cache.values()
                )
                avg_access_count = total_access_count / current_size if current_size > 0 else 0
                
                # Calculate total cached data size
                total_data_rows = sum(
                    entry.get('data_size', 0) 
                    for entry in self._cache.values()
                )
                
                # Identify oldest and newest entries
                oldest_entry_age = None
                newest_entry_age = None
                if self._cache_access_times:
                    oldest_access = min(self._cache_access_times.values())
                    newest_access = max(self._cache_access_times.values())
                    oldest_entry_age = round(current_time - oldest_access, 2)
                    newest_entry_age = round(current_time - newest_access, 2)
                
                # Time since last cleanup
                time_since_cleanup = round(current_time - self._cache_config['last_cleanup'], 2)
                
                stats = {
                    # Basic cache status
                    'cache_enabled': True,
                    'cache_healthy': self._cache_stats['errors'] < total_requests * 0.1,  # < 10% error rate
                    
                    # Size and capacity metrics
                    'current_size': current_size,
                    'max_size': self.max_cache_size,
                    'utilization_percent': round(utilization_percent, 2),
                    
                    # Hit/miss statistics
                    'hits': self._cache_stats['hits'],
                    'misses': self._cache_stats['misses'],
                    'hit_rate_percent': round(hit_rate, 2),
                    'total_requests': total_requests,
                    
                    # Error and maintenance stats
                    'errors': self._cache_stats['errors'],
                    'evictions': self._cache_stats['evictions'],
                    'expired_entries': self._cache_stats['expired_entries'],
                    'cache_size_violations': self._cache_stats['cache_size_violations'],
                    
                    # Data metrics
                    'total_files_cached': self._cache_stats['total_files_cached'],
                    'total_data_rows': total_data_rows,
                    'avg_access_count': round(avg_access_count, 2),
                    
                    # Timing metrics
                    'ttl_seconds': self.cache_ttl_seconds,
                    'cleanup_interval_seconds': self._cache_config['cleanup_interval'],
                    'time_since_cleanup_seconds': time_since_cleanup,
                    'oldest_entry_age_seconds': oldest_entry_age,
                    'newest_entry_age_seconds': newest_entry_age,
                    
                    # Performance insights
                    'cache_efficiency': 'excellent' if hit_rate > 80 else 'good' if hit_rate > 60 else 'fair' if hit_rate > 40 else 'poor',
                    'memory_usage': 'high' if utilization_percent > 90 else 'medium' if utilization_percent > 70 else 'low',
                    'needs_cleanup': time_since_cleanup > self._cache_config['cleanup_interval'] * 2
                }
                
                return stats
                
        except Exception as e:
            self.logger.warning(f"Error getting advanced cache stats: {str(e)}")
            return {
                'cache_enabled': True,
                'error': f"Failed to get stats: {str(e)}"
            }
    
    def invalidate_cache_entry(self, file_path: str) -> bool:
        """
        Invalidate a specific cache entry with error handling.
        
        Args:
            file_path (str): Path to the file to invalidate in cache
            
        Returns:
            bool: True if entry was invalidated, False if not found or error occurred
        """
        if not self.cache_enabled:
            return True  # Nothing to invalidate
            
        try:
            with self._cache_lock:
                entries_removed = 0
                
                # Find and remove all cache entries for this file path
                keys_to_remove = []
                for cached_key, cached_value in self._cache.items():
                    if cached_value.get('file_path') == file_path:
                        keys_to_remove.append(cached_key)
                
                for key in keys_to_remove:
                    del self._cache[key]
                    entries_removed += 1
                
                if entries_removed > 0:
                    self.logger.debug(f"Invalidated {entries_removed} cache entries for {file_path}")
                    return True
                else:
                    self.logger.debug(f"No cache entries found for {file_path}")
                    return False
                    
        except Exception as e:
            self.logger.warning(f"Error invalidating cache entry for {file_path}: {str(e)}")
            return False
    
    def _cleanup_expired_cache_entries(self) -> int:
        """
        Clean up expired cache entries based on TTL.
        
        Returns:
            int: Number of entries cleaned up
        """
        if not self.cache_enabled:
            return 0
            
        current_time = time.time()
        expired_keys = []
        
        try:
            for key, cache_data in self._cache.items():
                cache_time = cache_data.get('cache_time', 0)
                if current_time - cache_time > self.cache_ttl_seconds:
                    expired_keys.append(key)
            
            # Remove expired entries
            for key in expired_keys:
                del self._cache[key]
                self._cache_access_times.pop(key, None)
            
            if expired_keys:
                self._cache_stats['expired_entries'] += len(expired_keys)
                self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            # Update last cleanup time
            self._cache_config['last_cleanup'] = current_time
            
            return len(expired_keys)
            
        except Exception as e:
            self.logger.warning(f"Error during cache cleanup: {str(e)}")
            return 0
    
    def _evict_lru_entries(self, slots_needed: int = 1) -> int:
        """
        Evict least recently used cache entries to make space.
        
        Args:
            slots_needed (int): Number of cache slots needed
            
        Returns:
            int: Number of entries evicted
        """
        if not self.cache_enabled or len(self._cache) == 0:
            return 0
            
        try:
            # Sort by access time (oldest first)
            sorted_entries = sorted(
                self._cache_access_times.items(),
                key=lambda x: x[1]
            )
            
            evicted_count = 0
            for key, _ in sorted_entries:
                if evicted_count >= slots_needed:
                    break
                    
                # Remove from cache
                if key in self._cache:
                    del self._cache[key]
                    del self._cache_access_times[key]
                    evicted_count += 1
            
            if evicted_count > 0:
                self._cache_stats['evictions'] += evicted_count
                self.logger.debug(f"Evicted {evicted_count} LRU cache entries")
            
            return evicted_count
            
        except Exception as e:
            self.logger.warning(f"Error during LRU eviction: {str(e)}")
            return 0
    
    def _ensure_cache_capacity(self) -> None:
        """
        Ensure cache doesn't exceed capacity limits by cleaning up expired entries and evicting LRU entries.
        """
        if not self.cache_enabled:
            return
            
        try:
            current_time = time.time()
            
            # Periodic cleanup of expired entries
            if (current_time - self._cache_config['last_cleanup']) > self._cache_config['cleanup_interval']:
                self._cleanup_expired_cache_entries()
            
            # Check if we need to evict entries due to size limit
            current_size = len(self._cache)
            if current_size >= self.max_cache_size:
                # First try cleaning expired entries
                expired_cleaned = self._cleanup_expired_cache_entries()
                
                # If still over capacity, evict LRU entries
                remaining_size = len(self._cache)
                if remaining_size >= self.max_cache_size:
                    slots_to_free = remaining_size - self.max_cache_size + 1
                    self._evict_lru_entries(slots_to_free)
                    self._cache_stats['cache_size_violations'] += 1
                
        except Exception as e:
            self.logger.warning(f"Error ensuring cache capacity: {str(e)}")
    
    def _store_in_cache(self, cache_key: str, file_path: str, data: List[Dict[str, Any]]) -> bool:
        """
        Store data in cache with advanced management.
        
        Args:
            cache_key (str): Cache key for the data
            file_path (str): Original file path
            data (List[Dict[str, Any]]): Data to cache
            
        Returns:
            bool: True if successfully cached, False otherwise
        """
        if not self.cache_enabled:
            return False
            
        try:
            with self._cache_lock:
                # Ensure we have capacity
                self._ensure_cache_capacity()
                
                current_time = time.time()
                
                # Store cache entry with metadata
                self._cache[cache_key] = {
                    'data': data,
                    'timestamp': os.path.getmtime(file_path) if os.path.exists(file_path) else current_time,
                    'file_path': file_path,
                    'cache_time': current_time,
                    'access_count': 1,
                    'data_size': len(data)
                }
                
                # Track access time for LRU
                self._cache_access_times[cache_key] = current_time
                
                self._cache_stats['total_files_cached'] += 1
                self.logger.debug(f"Successfully cached {len(data)} rows for {file_path}")
                
                return True
                
        except Exception as e:
            self._cache_stats['errors'] += 1
            self.logger.warning(f"Failed to store in cache: {str(e)}")
            return False
    
    def _retrieve_from_cache(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve data from cache with TTL and freshness checks.
        
        Args:
            file_path (str): File path to retrieve from cache
            
        Returns:
            Optional[List[Dict[str, Any]]]: Cached data if valid, None otherwise
        """
        if not self.cache_enabled:
            return None
            
        try:
            with self._cache_lock:
                current_time = time.time()
                cache_key = self._generate_cache_key(file_path)
                
                # Check if entry exists
                if cache_key not in self._cache:
                    return None
                
                cache_entry = self._cache[cache_key]
                
                # Check TTL expiration
                cache_time = cache_entry.get('cache_time', 0)
                if current_time - cache_time > self.cache_ttl_seconds:
                    # Remove expired entry
                    del self._cache[cache_key]
                    self._cache_access_times.pop(cache_key, None)
                    self._cache_stats['expired_entries'] += 1
                    self.logger.debug(f"Cache entry expired for {file_path}")
                    return None
                
                # Check file freshness (if file was modified)
                try:
                    current_mtime = os.path.getmtime(file_path)
                    cached_mtime = cache_entry.get('timestamp', 0)
                    
                    if current_mtime > cached_mtime:
                        # File was modified, invalidate cache
                        del self._cache[cache_key]
                        self._cache_access_times.pop(cache_key, None)
                        self.logger.debug(f"Cache invalidated due to file modification: {file_path}")
                        return None
                        
                except OSError:
                    # File doesn't exist, but we have cached data - that's ok
                    pass
                
                # Update access time and count for LRU
                self._cache_access_times[cache_key] = current_time
                cache_entry['access_count'] = cache_entry.get('access_count', 0) + 1
                
                return cache_entry['data']
                
        except Exception as e:
            self.logger.warning(f"Error retrieving from cache: {str(e)}")
            return None
    
    def optimize_cache(self, force_cleanup: bool = False) -> Dict[str, int]:
        """
        Manually optimize cache by cleaning expired entries and optionally forcing LRU eviction.
        
        Args:
            force_cleanup (bool): Force cleanup even if not due for scheduled cleanup
            
        Returns:
            Dict[str, int]: Statistics about the optimization operation
        """
        if not self.cache_enabled:
            return {'message': 'Cache is disabled', 'expired_cleaned': 0, 'lru_evicted': 0}
            
        try:
            with self._cache_lock:
                initial_size = len(self._cache)
                
                # Force cleanup if requested or if due
                if force_cleanup:
                    self._cache_config['last_cleanup'] = 0  # Force cleanup
                
                # Clean expired entries
                expired_cleaned = self._cleanup_expired_cache_entries()
                
                # Optionally evict some LRU entries if cache is still very full
                lru_evicted = 0
                current_size = len(self._cache)
                if current_size > self.max_cache_size * 0.8:  # If > 80% full
                    slots_to_free = int(self.max_cache_size * 0.2)  # Free 20% of capacity
                    lru_evicted = self._evict_lru_entries(slots_to_free)
                
                final_size = len(self._cache)
                
                optimization_stats = {
                    'initial_size': initial_size,
                    'final_size': final_size,
                    'expired_cleaned': expired_cleaned,
                    'lru_evicted': lru_evicted,
                    'total_freed': initial_size - final_size,
                    'optimization_successful': True
                }
                
                self.logger.info(f"Cache optimization completed: freed {initial_size - final_size} entries "
                               f"({expired_cleaned} expired, {lru_evicted} LRU)")
                
                return optimization_stats
                
        except Exception as e:
            self.logger.error(f"Error during cache optimization: {str(e)}")
            return {
                'optimization_successful': False,
                'error': str(e),
                'expired_cleaned': 0,
                'lru_evicted': 0
            }
    
    def get_csv_file_for_endpoint(self, endpoint: str, sub_option: str = None, year: str = None) -> Optional[str]:
        """
        Get the appropriate CSV file for a given endpoint and sub-option.
        
        Args:
            endpoint (str): API endpoint name (e.g., 'producao', 'processamento')
            sub_option (str, optional): Sub-option parameter from the API request
            year (str, optional): Year parameter (for future use/validation)
            
        Returns:
            Optional[str]: CSV filename if mapping exists, None otherwise
            
        Raises:
            CsvFileError: If endpoint is invalid or file doesn't exist
        """
        try:
            # Validate endpoint
            if not endpoint:
                raise CsvFileError("Endpoint cannot be empty")
            
            # Normalize endpoint name
            endpoint = endpoint.lower().strip()
            
            # Check if endpoint exists in mapping
            if endpoint not in self.ENDPOINT_CSV_MAP:
                available_endpoints = list(self.ENDPOINT_CSV_MAP.keys())
                raise CsvFileError(f"Unknown endpoint '{endpoint}'. Available endpoints: {', '.join(available_endpoints)}")
            
            endpoint_config = self.ENDPOINT_CSV_MAP[endpoint]
            csv_filename = None
            
            # Try to get specific file for sub_option first
            if sub_option and 'sub_options' in endpoint_config:
                csv_filename = endpoint_config['sub_options'].get(sub_option)
                if csv_filename:
                    self.logger.debug(f"Found specific CSV for endpoint '{endpoint}' with sub_option '{sub_option}': {csv_filename}")
            
            # Fall back to default file if no specific mapping found
            if not csv_filename:
                csv_filename = endpoint_config.get('default')
                if csv_filename:
                    self.logger.debug(f"Using default CSV for endpoint '{endpoint}': {csv_filename}")
            
            # If still no file found, raise error
            if not csv_filename:
                raise CsvFileError(f"No CSV mapping found for endpoint '{endpoint}' with sub_option '{sub_option}'")
            
            # Validate that the file exists
            full_path = self.csv_directory / csv_filename
            if not full_path.exists():
                raise CsvFileError(f"CSV file '{csv_filename}' not found in directory '{self.csv_directory}'")
            
            # Validate file is readable
            if not full_path.is_file():
                raise CsvFileError(f"Path '{csv_filename}' exists but is not a file")
            
            if not os.access(full_path, os.R_OK):
                raise CsvFileError(f"No read permission for CSV file '{csv_filename}'")
            
            self.logger.info(f"Resolved CSV file for endpoint '{endpoint}' (sub_option: '{sub_option}'): {csv_filename}")
            return csv_filename
            
        except CsvFileError:
            # Re-raise CsvFileError as-is
            raise
        except Exception as e:
            # Wrap unexpected errors
            error_msg = f"Unexpected error resolving CSV file for endpoint '{endpoint}': {str(e)}"
            self.logger.error(error_msg)
            raise CsvFileError(error_msg) from e
    
    def get_available_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available endpoints and their CSV mappings.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary with endpoint information including available sub-options and file status
        """
        try:
            endpoints_info = {}
            
            for endpoint, config in self.ENDPOINT_CSV_MAP.items():
                endpoint_info = {
                    'default_file': config.get('default'),
                    'sub_options': {},
                    'files_status': {}
                }
                
                # Check default file status
                if endpoint_info['default_file']:
                    default_path = self.csv_directory / endpoint_info['default_file']
                    endpoint_info['files_status'][endpoint_info['default_file']] = {
                        'exists': default_path.exists(),
                        'readable': default_path.exists() and os.access(default_path, os.R_OK),
                        'size_bytes': default_path.stat().st_size if default_path.exists() else 0
                    }
                
                # Check sub-option files
                if 'sub_options' in config:
                    for sub_opt, filename in config['sub_options'].items():
                        endpoint_info['sub_options'][sub_opt] = filename
                        
                        if filename not in endpoint_info['files_status']:
                            file_path = self.csv_directory / filename
                            endpoint_info['files_status'][filename] = {
                                'exists': file_path.exists(),
                                'readable': file_path.exists() and os.access(file_path, os.R_OK),
                                'size_bytes': file_path.stat().st_size if file_path.exists() else 0
                            }
                
                endpoints_info[endpoint] = endpoint_info
            
            return endpoints_info
            
        except Exception as e:
            self.logger.error(f"Error getting available endpoints: {str(e)}")
            return {}
    
    def get_data_for_endpoint(self, endpoint: str, sub_option: str = None, year: str = None) -> Optional[Dict[str, Any]]:
        """
        Get parsed and converted data for a specific endpoint and sub-option.
        
        This is a convenience method that combines endpoint resolution, CSV parsing, and API format conversion.
        
        Args:
            endpoint (str): API endpoint name (e.g., 'producao', 'processamento')
            sub_option (str, optional): Sub-option parameter from the API request
            year (str, optional): Year parameter (for future filtering)
            
        Returns:
            Optional[Dict[str, Any]]: Converted data in API format, or None if error
            
        Raises:
            CsvFileError: If endpoint mapping fails
            CsvParseError: If CSV parsing fails
            CsvFormatError: If format conversion fails
        """
        try:
            # Resolve the CSV file for this endpoint
            csv_filename = self.get_csv_file_for_endpoint(endpoint, sub_option, year)
            if not csv_filename:
                raise CsvFileError(f"Could not resolve CSV file for endpoint '{endpoint}'")
            
            # Parse the CSV file
            csv_data = self.parse_csv_file(csv_filename)
            if not csv_data:
                self.logger.warning(f"No data found in CSV file '{csv_filename}' for endpoint '{endpoint}'")
                return None
            
            # Convert to API format
            api_data = self.convert_to_api_format(csv_data, endpoint)
            if not api_data:
                raise CsvFormatError(f"Failed to convert CSV data to API format for endpoint '{endpoint}'")
            
            self.logger.info(f"Successfully retrieved and converted data for endpoint '{endpoint}' from '{csv_filename}'")
            return api_data
            
        except (CsvFileError, CsvParseError, CsvFormatError):
            # Re-raise known CSV errors
            raise
        except Exception as e:
            # Wrap unexpected errors
            error_msg = f"Unexpected error getting data for endpoint '{endpoint}': {str(e)}"
            self.logger.error(error_msg)
            raise CsvFallbackError(error_msg) from e
    
    def validate_endpoint_mapping(self) -> Dict[str, Any]:
        """
        Validate all endpoint mappings and return a comprehensive status report.
        
        Returns:
            Dict[str, Any]: Validation report with status for each endpoint and file
        """
        try:
            validation_report = {
                'overall_status': 'unknown',
                'total_endpoints': len(self.ENDPOINT_CSV_MAP),
                'valid_endpoints': 0,
                'invalid_endpoints': 0,
                'total_files': 0,
                'existing_files': 0,
                'missing_files': 0,
                'endpoints': {},
                'missing_files_list': [],
                'validation_timestamp': time.time()
            }
            
            all_files = set()
            
            for endpoint, config in self.ENDPOINT_CSV_MAP.items():
                endpoint_status = {
                    'valid': True,
                    'default_file': config.get('default'),
                    'default_file_exists': False,
                    'sub_options_count': 0,
                    'valid_sub_options': 0,
                    'files': {},
                    'errors': []
                }
                
                # Check default file
                if endpoint_status['default_file']:
                    default_path = self.csv_directory / endpoint_status['default_file']
                    endpoint_status['default_file_exists'] = default_path.exists()
                    all_files.add(endpoint_status['default_file'])
                    
                    endpoint_status['files'][endpoint_status['default_file']] = {
                        'exists': endpoint_status['default_file_exists'],
                        'readable': endpoint_status['default_file_exists'] and os.access(default_path, os.R_OK),
                        'size': default_path.stat().st_size if endpoint_status['default_file_exists'] else 0
                    }
                    
                    if not endpoint_status['default_file_exists']:
                        endpoint_status['errors'].append(f"Default file '{endpoint_status['default_file']}' not found")
                        validation_report['missing_files_list'].append(endpoint_status['default_file'])
                
                # Check sub-option files
                if 'sub_options' in config:
                    endpoint_status['sub_options_count'] = len(config['sub_options'])
                    
                    for sub_opt, filename in config['sub_options'].items():
                        all_files.add(filename)
                        file_path = self.csv_directory / filename
                        file_exists = file_path.exists()
                        
                        if filename not in endpoint_status['files']:
                            endpoint_status['files'][filename] = {
                                'exists': file_exists,
                                'readable': file_exists and os.access(file_path, os.R_OK),
                                'size': file_path.stat().st_size if file_exists else 0
                            }
                        
                        if file_exists:
                            endpoint_status['valid_sub_options'] += 1
                        else:
                            endpoint_status['errors'].append(f"Sub-option '{sub_opt}' file '{filename}' not found")
                            if filename not in validation_report['missing_files_list']:
                                validation_report['missing_files_list'].append(filename)
                
                # Determine endpoint validity
                if endpoint_status['errors']:
                    endpoint_status['valid'] = False
                    validation_report['invalid_endpoints'] += 1
                else:
                    validation_report['valid_endpoints'] += 1
                
                validation_report['endpoints'][endpoint] = endpoint_status
            
            # Calculate file statistics
            validation_report['total_files'] = len(all_files)
            validation_report['existing_files'] = sum(1 for f in all_files if (self.csv_directory / f).exists())
            validation_report['missing_files'] = validation_report['total_files'] - validation_report['existing_files']
            
            # Determine overall status
            if validation_report['missing_files'] == 0:
                validation_report['overall_status'] = 'valid'
            elif validation_report['existing_files'] > 0:
                validation_report['overall_status'] = 'partial'
            else:
                validation_report['overall_status'] = 'invalid'
            
            self.logger.info(f"Endpoint mapping validation completed: {validation_report['overall_status']} "
                           f"({validation_report['valid_endpoints']}/{validation_report['total_endpoints']} endpoints valid)")
            
            return validation_report
            
        except Exception as e:
            self.logger.error(f"Error during endpoint mapping validation: {str(e)}")
            return {
                'overall_status': 'error',
                'error': str(e),
                'validation_timestamp': time.time()
            } 