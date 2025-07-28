"""Performance optimization utilities for the AI Coding Agent.

This module provides comprehensive performance features including:
- Intelligent caching strategies
- Request optimization
- Memory management
- Profiling and monitoring
- Async operation optimization
"""

import asyncio
import functools
import hashlib
import time
import weakref
from typing import Any, Dict, List, Optional, Callable, TypeVar, Union
import logging
from datetime import datetime, timedelta
import gc
from dataclasses import dataclass
from pathlib import Path
import json

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    data: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    size_bytes: int
    expires_at: Optional[datetime] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    operation_name: str
    duration: float
    memory_used: int
    cache_hit: bool
    timestamp: datetime
    metadata: Dict[str, Any]


class LRUCache:
    """Thread-safe LRU cache with size limits and TTL support."""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100, default_ttl: int = 3600):
        """Initialize LRU cache.
        
        Args:
            max_size: Maximum number of entries
            max_memory_mb: Maximum memory usage in MB
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl
        
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
        self._current_memory = 0
        self._lock = asyncio.Lock()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        async with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.expires_at and datetime.now() > entry.expires_at:
                await self._remove_entry(key)
                self.misses += 1
                return None
            
            # Update access info
            entry.last_accessed = datetime.now()
            entry.access_count += 1
            
            # Move to end of access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            self.hits += 1
            return entry.data
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        async with self._lock:
            # Calculate size
            size_bytes = self._estimate_size(value)
            
            # Remove existing entry if present
            if key in self._cache:
                await self._remove_entry(key)
            
            # Check if we need to make space
            while (len(self._cache) >= self.max_size or 
                   self._current_memory + size_bytes > self.max_memory_bytes):
                if not self._access_order:
                    break
                oldest_key = self._access_order.pop(0)
                await self._remove_entry(oldest_key)
                self.evictions += 1
            
            # Create entry
            expires_at = None
            if ttl is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl)
            elif self.default_ttl > 0:
                expires_at = datetime.now() + timedelta(seconds=self.default_ttl)
            
            entry = CacheEntry(
                data=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=0,
                size_bytes=size_bytes,
                expires_at=expires_at
            )
            
            self._cache[key] = entry
            self._access_order.append(key)
            self._current_memory += size_bytes
    
    async def delete(self, key: str) -> bool:
        """Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was deleted
        """
        async with self._lock:
            if key in self._cache:
                await self._remove_entry(key)
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._current_memory = 0
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        async with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.expires_at and now > entry.expires_at
            ]
            
            for key in expired_keys:
                await self._remove_entry(key)
            
            return len(expired_keys)
    
    async def _remove_entry(self, key: str) -> None:
        """Remove entry from cache."""
        if key in self._cache:
            entry = self._cache[key]
            self._current_memory -= entry.size_bytes
            del self._cache[key]
        
        if key in self._access_order:
            self._access_order.remove(key)
    
    def _estimate_size(self, obj: Any) -> int:
        """Estimate object size in bytes."""
        try:
            if isinstance(obj, str):
                return len(obj.encode('utf-8'))
            elif isinstance(obj, (int, float)):
                return 8
            elif isinstance(obj, (list, tuple)):
                return sum(self._estimate_size(item) for item in obj) + 64
            elif isinstance(obj, dict):
                return sum(
                    self._estimate_size(k) + self._estimate_size(v) 
                    for k, v in obj.items()
                ) + 64
            else:
                # Rough estimate for other objects
                return len(str(obj).encode('utf-8')) + 100
        except Exception:
            return 1024  # Default estimate
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "memory_used_mb": self._current_memory / (1024 * 1024),
            "max_memory_mb": self.max_memory_bytes / (1024 * 1024),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "evictions": self.evictions
        }


class PerformanceMonitor:
    """Performance monitoring and profiling."""
    
    def __init__(self, max_metrics: int = 10000):
        """Initialize performance monitor.
        
        Args:
            max_metrics: Maximum number of metrics to store
        """
        self.max_metrics = max_metrics
        self.metrics: List[PerformanceMetrics] = []
        self._lock = asyncio.Lock()
    
    async def record_operation(
        self,
        operation_name: str,
        duration: float,
        memory_used: int = 0,
        cache_hit: bool = False,
        **metadata: Any
    ) -> None:
        """Record performance metrics for an operation.
        
        Args:
            operation_name: Name of the operation
            duration: Duration in seconds
            memory_used: Memory used in bytes
            cache_hit: Whether operation used cache
            **metadata: Additional metadata
        """
        async with self._lock:
            metric = PerformanceMetrics(
                operation_name=operation_name,
                duration=duration,
                memory_used=memory_used,
                cache_hit=cache_hit,
                timestamp=datetime.now(),
                metadata=metadata
            )
            
            self.metrics.append(metric)
            
            # Trim if necessary
            if len(self.metrics) > self.max_metrics:
                self.metrics = self.metrics[-self.max_metrics:]
    
    async def get_operation_stats(self, operation_name: str) -> Dict[str, Any]:
        """Get statistics for a specific operation.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Statistics dictionary
        """
        async with self._lock:
            operation_metrics = [
                m for m in self.metrics 
                if m.operation_name == operation_name
            ]
            
            if not operation_metrics:
                return {"operation": operation_name, "count": 0}
            
            durations = [m.duration for m in operation_metrics]
            memory_usage = [m.memory_used for m in operation_metrics]
            cache_hits = sum(1 for m in operation_metrics if m.cache_hit)
            
            return {
                "operation": operation_name,
                "count": len(operation_metrics),
                "avg_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "avg_memory": sum(memory_usage) / len(memory_usage),
                "cache_hit_rate": cache_hits / len(operation_metrics),
                "last_run": max(m.timestamp for m in operation_metrics).isoformat()
            }
    
    async def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall performance statistics."""
        async with self._lock:
            if not self.metrics:
                return {"total_operations": 0}
            
            operations = {}
            for metric in self.metrics:
                if metric.operation_name not in operations:
                    operations[metric.operation_name] = []
                operations[metric.operation_name].append(metric)
            
            total_duration = sum(m.duration for m in self.metrics)
            total_memory = sum(m.memory_used for m in self.metrics)
            total_cache_hits = sum(1 for m in self.metrics if m.cache_hit)
            
            return {
                "total_operations": len(self.metrics),
                "unique_operations": len(operations),
                "total_duration": total_duration,
                "avg_duration": total_duration / len(self.metrics),
                "total_memory": total_memory,
                "avg_memory": total_memory / len(self.metrics),
                "cache_hit_rate": total_cache_hits / len(self.metrics),
                "operations": list(operations.keys())
            }


def timed_cache(ttl: int = 3600, max_size: int = 100):
    """Decorator for caching function results with TTL.
    
    Args:
        ttl: Time to live in seconds
        max_size: Maximum cache size
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache = LRUCache(max_size=max_size, default_ttl=ttl)
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Create cache key
            key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            key = hashlib.md5(str(key_data).encode()).hexdigest()
            
            # Try cache first
            result = await cache.get(key)
            if result is not None:
                return result
            
            # Call function and cache result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await cache.set(key, result)
            return result
        
        wrapper.cache = cache
        return wrapper
    
    return decorator


def performance_monitor(monitor: PerformanceMonitor):
    """Decorator for monitoring function performance.
    
    Args:
        monitor: PerformanceMonitor instance
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            start_time = time.perf_counter()
            start_memory = get_memory_usage()
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Record successful operation
                duration = time.perf_counter() - start_time
                memory_used = get_memory_usage() - start_memory
                
                await monitor.record_operation(
                    operation_name=func.__name__,
                    duration=duration,
                    memory_used=memory_used,
                    success=True
                )
                
                return result
                
            except Exception as e:
                # Record failed operation
                duration = time.perf_counter() - start_time
                memory_used = get_memory_usage() - start_memory
                
                await monitor.record_operation(
                    operation_name=func.__name__,
                    duration=duration,
                    memory_used=memory_used,
                    success=False,
                    error=str(e)
                )
                
                raise
        
        return wrapper
    
    return decorator


class BatchProcessor:
    """Batch processing for efficient API calls."""
    
    def __init__(self, batch_size: int = 10, max_wait_time: float = 1.0):
        """Initialize batch processor.
        
        Args:
            batch_size: Maximum batch size
            max_wait_time: Maximum wait time in seconds
        """
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_requests: List[Dict[str, Any]] = []
        self.batch_lock = asyncio.Lock()
        self._processing = False
    
    async def add_request(self, request_data: Dict[str, Any], callback: Callable) -> Any:
        """Add request to batch.
        
        Args:
            request_data: Request data
            callback: Callback function for processing
            
        Returns:
            Result future
        """
        future = asyncio.Future()
        
        async with self.batch_lock:
            self.pending_requests.append({
                'data': request_data,
                'callback': callback,
                'future': future
            })
            
            # Start processing if batch is full or this is the first request
            if len(self.pending_requests) >= self.batch_size or not self._processing:
                asyncio.create_task(self._process_batch())
        
        return await future
    
    async def _process_batch(self) -> None:
        """Process pending batch requests."""
        if self._processing:
            return
        
        self._processing = True
        
        try:
            # Wait for either batch to fill or timeout
            start_time = time.time()
            while (len(self.pending_requests) < self.batch_size and 
                   time.time() - start_time < self.max_wait_time):
                await asyncio.sleep(0.1)
            
            async with self.batch_lock:
                if not self.pending_requests:
                    return
                
                batch = self.pending_requests.copy()
                self.pending_requests.clear()
            
            # Process batch
            tasks = []
            for request in batch:
                task = asyncio.create_task(
                    self._process_single_request(request)
                )
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
        finally:
            self._processing = False
    
    async def _process_single_request(self, request: Dict[str, Any]) -> None:
        """Process a single request."""
        try:
            result = await request['callback'](request['data'])
            request['future'].set_result(result)
        except Exception as e:
            request['future'].set_exception(e)


class AsyncPoolExecutor:
    """Async pool executor for parallel operations."""
    
    def __init__(self, max_workers: int = 10):
        """Initialize executor.
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
        self.active_tasks: weakref.WeakSet = weakref.WeakSet()
    
    async def submit(self, coro: Callable[..., T], *args, **kwargs) -> T:
        """Submit coroutine for execution.
        
        Args:
            coro: Coroutine function
            *args: Arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result of coroutine
        """
        async with self.semaphore:
            task = asyncio.create_task(coro(*args, **kwargs))
            self.active_tasks.add(task)
            
            try:
                return await task
            finally:
                self.active_tasks.discard(task)
    
    async def submit_all(self, tasks: List[tuple]) -> List[Any]:
        """Submit multiple tasks for parallel execution.
        
        Args:
            tasks: List of (coro, args, kwargs) tuples
            
        Returns:
            List of results
        """
        coroutines = [
            self.submit(coro, *args, **kwargs)
            for coro, args, kwargs in tasks
        ]
        
        return await asyncio.gather(*coroutines)
    
    async def shutdown(self, wait: bool = True) -> None:
        """Shutdown executor.
        
        Args:
            wait: Whether to wait for active tasks
        """
        if wait:
            # Wait for all active tasks to complete
            while self.active_tasks:
                await asyncio.sleep(0.1)


def get_memory_usage() -> int:
    """Get current memory usage in bytes."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss
    except ImportError:
        # Fallback to gc stats
        return len(gc.get_objects()) * 100  # Rough estimate


async def optimize_for_large_datasets(data: List[Any], chunk_size: int = 1000) -> List[Any]:
    """Optimize processing for large datasets.
    
    Args:
        data: Dataset to process
        chunk_size: Size of processing chunks
        
    Returns:
        Processed data
    """
    results = []
    
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        
        # Process chunk
        chunk_results = await asyncio.gather(*[
            process_item(item) for item in chunk
        ])
        
        results.extend(chunk_results)
        
        # Yield control to allow other operations
        await asyncio.sleep(0)
        
        # Trigger garbage collection periodically
        if i % (chunk_size * 10) == 0:
            gc.collect()
    
    return results


async def process_item(item: Any) -> Any:
    """Process a single item (placeholder)."""
    # This would be replaced with actual processing logic
    await asyncio.sleep(0.001)  # Simulate processing time
    return item


class ResourceManager:
    """Manage system resources and limits."""
    
    def __init__(self, max_memory_mb: int = 1000, max_cpu_percent: float = 80.0):
        """Initialize resource manager.
        
        Args:
            max_memory_mb: Maximum memory usage in MB
            max_cpu_percent: Maximum CPU usage percentage
        """
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.max_cpu_percent = max_cpu_percent
        self.monitoring = False
    
    async def start_monitoring(self) -> None:
        """Start resource monitoring."""
        self.monitoring = True
        asyncio.create_task(self._monitor_resources())
    
    def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        self.monitoring = False
    
    async def _monitor_resources(self) -> None:
        """Monitor system resources."""
        while self.monitoring:
            try:
                memory_usage = get_memory_usage()
                
                if memory_usage > self.max_memory_bytes:
                    logger.warning(f"High memory usage: {memory_usage / (1024*1024):.1f}MB")
                    gc.collect()  # Force garbage collection
                
                # Monitor CPU if psutil is available
                try:
                    import psutil
                    cpu_percent = psutil.cpu_percent(interval=1)
                    if cpu_percent > self.max_cpu_percent:
                        logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
                        await asyncio.sleep(0.5)  # Brief pause to reduce load
                except ImportError:
                    pass
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring resources: {e}")
                await asyncio.sleep(10)