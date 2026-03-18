from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from duui_py.logging.core import get_event_logger, MetricEvent

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None  # type: ignore


class MetricCollector:
    """Collects system and process metrics."""
    
    def __init__(
        self,
        collection_interval_seconds: int = 5,
        include_process_metrics: bool = True,
        include_system_metrics: bool = True,
        include_disk_metrics: bool = True,
        include_network_metrics: bool = True,
    ):
        self.collection_interval = collection_interval_seconds
        self.include_process_metrics = include_process_metrics
        self.include_system_metrics = include_system_metrics
        self.include_disk_metrics = include_disk_metrics
        self.include_network_metrics = include_network_metrics
        
        self._process = psutil.Process() if PSUTIL_AVAILABLE else None
        self._collection_task: Optional[asyncio.Task] = None
        self._running = False
        
        # For calculating deltas
        self._last_network_io = self._get_network_io() if PSUTIL_AVAILABLE else None
        self._last_disk_io = self._get_disk_io() if PSUTIL_AVAILABLE else None
        self._last_collection_time = time.time()
    
    def start(self) -> None:
        """Start the background metrics collection."""
        if not PSUTIL_AVAILABLE:
            print("Warning: psutil not available, metrics collection disabled")
            return
        
        if self._collection_task is None:
            self._running = True
            self._collection_task = asyncio.create_task(self._collection_loop())
    
    async def stop(self) -> None:
        """Stop the background metrics collection."""
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
            self._collection_task = None
    
    async def _collection_loop(self) -> None:
        """Background task to collect and log metrics periodically."""
        while self._running:
            try:
                await asyncio.sleep(self.collection_interval)
                await self.collect_and_log_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log but don't crash
                print(f"Error in metrics collection: {e}")
    
    async def collect_and_log_metrics(self) -> None:
        """Collect all metrics and log them via the event logger."""
        if not PSUTIL_AVAILABLE:
            return
        
        current_time = time.time()
        interval_ms = int((current_time - self._last_collection_time) * 1000)
        self._last_collection_time = current_time
        
        logger = get_event_logger()
        
        # Collect process metrics
        if self.include_process_metrics:
            process_metrics = self._collect_process_metrics(interval_ms)
            for metric in process_metrics:
                await logger.metric(**metric)
        
        # Collect system metrics
        if self.include_system_metrics:
            system_metrics = self._collect_system_metrics(interval_ms)
            for metric in system_metrics:
                await logger.metric(**metric)
        
        # Collect disk metrics
        if self.include_disk_metrics:
            disk_metrics = self._collect_disk_metrics(interval_ms)
            for metric in disk_metrics:
                await logger.metric(**metric)
        
        # Collect network metrics
        if self.include_network_metrics:
            network_metrics = self._collect_network_metrics(interval_ms)
            for metric in network_metrics:
                await logger.metric(**metric)
    
    def _collect_process_metrics(self, interval_ms: int) -> List[Dict[str, Any]]:
        """Collect metrics for the current process."""
        metrics = []
        
        try:
            # CPU
            cpu_percent = self._process.cpu_percent(interval=None)  # Non-blocking
            metrics.append({
                "category": "cpu",
                "name": "cpu_percent",
                "value": cpu_percent,
                "unit": "percent",
                "interval_ms": interval_ms,
                "tags": {"scope": "process"}
            })
            
            # Memory
            memory_info = self._process.memory_info()
            metrics.extend([
                {
                    "category": "memory",
                    "name": "memory_rss_bytes",
                    "value": float(memory_info.rss),
                    "unit": "bytes",
                    "interval_ms": interval_ms,
                    "tags": {"scope": "process"}
                },
                {
                    "category": "memory",
                    "name": "memory_vms_bytes",
                    "value": float(memory_info.vms),
                    "unit": "bytes",
                    "interval_ms": interval_ms,
                    "tags": {"scope": "process"}
                }
            ])
            
            # Threads
            num_threads = self._process.num_threads()
            metrics.append({
                "category": "process",
                "name": "thread_count",
                "value": float(num_threads),
                "unit": "count",
                "interval_ms": interval_ms,
                "tags": {"scope": "process"}
            })
            
            # File descriptors (Unix) or handles (Windows)
            try:
                num_fds = self._process.num_fds() if hasattr(self._process, 'num_fds') else 0
                metrics.append({
                    "category": "process",
                    "name": "file_descriptors",
                    "value": float(num_fds),
                    "unit": "count",
                    "interval_ms": interval_ms,
                    "tags": {"scope": "process"}
                })
            except (AttributeError, psutil.AccessDenied):
                pass
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process may have terminated or we don't have access
            pass
        
        return metrics
    
    def _collect_system_metrics(self, interval_ms: int) -> List[Dict[str, Any]]:
        """Collect system-wide metrics."""
        metrics = []
        
        try:
            # System CPU
            system_cpu_percent = psutil.cpu_percent(interval=None, percpu=False)
            metrics.append({
                "category": "cpu",
                "name": "system_cpu_percent",
                "value": system_cpu_percent,
                "unit": "percent",
                "interval_ms": interval_ms,
                "tags": {"scope": "system"}
            })
            
            # System memory
            system_memory = psutil.virtual_memory()
            metrics.extend([
                {
                    "category": "memory",
                    "name": "system_memory_total_bytes",
                    "value": float(system_memory.total),
                    "unit": "bytes",
                    "interval_ms": interval_ms,
                    "tags": {"scope": "system"}
                },
                {
                    "category": "memory",
                    "name": "system_memory_available_bytes",
                    "value": float(system_memory.available),
                    "unit": "bytes",
                    "interval_ms": interval_ms,
                    "tags": {"scope": "system"}
                },
                {
                    "category": "memory",
                    "name": "system_memory_used_percent",
                    "value": system_memory.percent,
                    "unit": "percent",
                    "interval_ms": interval_ms,
                    "tags": {"scope": "system"}
                }
            ])
            
            # System load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()
                metrics.extend([
                    {
                        "category": "system",
                        "name": "load_average_1min",
                        "value": load_avg[0],
                        "unit": "load",
                        "interval_ms": interval_ms,
                        "tags": {"scope": "system"}
                    },
                    {
                        "category": "system",
                        "name": "load_average_5min",
                        "value": load_avg[1],
                        "unit": "load",
                        "interval_ms": interval_ms,
                        "tags": {"scope": "system"}
                    },
                    {
                        "category": "system",
                        "name": "load_average_15min",
                        "value": load_avg[2],
                        "unit": "load",
                        "interval_ms": interval_ms,
                        "tags": {"scope": "system"}
                    }
                ])
            except AttributeError:
                pass
            
        except Exception as e:
            # Log but continue with other metrics
            print(f"Error collecting system metrics: {e}")
        
        return metrics
    
    def _collect_disk_metrics(self, interval_ms: int) -> List[Dict[str, Any]]:
        """Collect disk I/O metrics."""
        metrics = []
        
        try:
            current_disk_io = self._get_disk_io()
            
            if self._last_disk_io and current_disk_io:
                read_diff = current_disk_io["read_bytes"] - self._last_disk_io["read_bytes"]
                write_diff = current_disk_io["write_bytes"] - self._last_disk_io["write_bytes"]
                
                # Calculate rates in bytes per second
                interval_seconds = interval_ms / 1000
                if interval_seconds > 0:
                    read_rate = read_diff / interval_seconds
                    write_rate = write_diff / interval_seconds
                    
                    metrics.extend([
                        {
                            "category": "disk",
                            "name": "disk_read_bytes_per_second",
                            "value": read_rate,
                            "unit": "bytes_per_second",
                            "interval_ms": interval_ms,
                            "tags": {"scope": "system"}
                        },
                        {
                            "category": "disk",
                            "name": "disk_write_bytes_per_second",
                            "value": write_rate,
                            "unit": "bytes_per_second",
                            "interval_ms": interval_ms,
                            "tags": {"scope": "system"}
                        }
                    ])
            
            self._last_disk_io = current_disk_io
            
            # Disk usage for root filesystem
            try:
                disk_usage = psutil.disk_usage('/')
                metrics.append({
                    "category": "disk",
                    "name": "disk_usage_percent",
                    "value": disk_usage.percent,
                    "unit": "percent",
                    "interval_ms": interval_ms,
                    "tags": {"scope": "system", "mount": "/"}
                })
            except Exception:
                pass
            
        except Exception as e:
            print(f"Error collecting disk metrics: {e}")
        
        return metrics
    
    def _collect_network_metrics(self, interval_ms: int) -> List[Dict[str, Any]]:
        """Collect network I/O metrics."""
        metrics = []
        
        try:
            current_network_io = self._get_network_io()
            
            if self._last_network_io and current_network_io:
                bytes_sent_diff = current_network_io["bytes_sent"] - self._last_network_io["bytes_sent"]
                bytes_recv_diff = current_network_io["bytes_recv"] - self._last_network_io["bytes_recv"]
                
                # Calculate rates in bytes per second
                interval_seconds = interval_ms / 1000
                if interval_seconds > 0:
                    sent_rate = bytes_sent_diff / interval_seconds
                    recv_rate = bytes_recv_diff / interval_seconds
                    
                    metrics.extend([
                        {
                            "category": "network",
                            "name": "network_sent_bytes_per_second",
                            "value": sent_rate,
                            "unit": "bytes_per_second",
                            "interval_ms": interval_ms,
                            "tags": {"scope": "system"}
                        },
                        {
                            "category": "network",
                            "name": "network_received_bytes_per_second",
                            "value": recv_rate,
                            "unit": "bytes_per_second",
                            "interval_ms": interval_ms,
                            "tags": {"scope": "system"}
                        }
                    ])
            
            self._last_network_io = current_network_io
            
        except Exception as e:
            print(f"Error collecting network metrics: {e}")
        
        return metrics
    
    def _get_disk_io(self) -> Optional[Dict[str, float]]:
        """Get current disk I/O statistics."""
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                return {
                    "read_bytes": float(disk_io.read_bytes),
                    "write_bytes": float(disk_io.write_bytes),
                }
        except Exception:
            pass
        return None
    
    def _get_network_io(self) -> Optional[Dict[str, float]]:
        """Get current network I/O statistics."""
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                return {
                    "bytes_sent": float(net_io.bytes_sent),
                    "bytes_recv": float(net_io.bytes_recv),
                }
        except Exception:
            pass
        return None


# Global metric collector instance
_metric_collector_instance: Optional[MetricCollector] = None


def get_metric_collector() -> MetricCollector:
    """Get the global metric collector instance."""
    global _metric_collector_instance
    if _metric_collector_instance is None:
        _metric_collector_instance = MetricCollector()
    return _metric_collector_instance


def configure_metric_collector(
    collection_interval_seconds: int = 5,
    include_process_metrics: bool = True,
    include_system_metrics: bool = True,
    include_disk_metrics: bool = True,
    include_network_metrics: bool = True,
    start_immediately: bool = True,
) -> MetricCollector:
    """Configure the global metric collector."""
    global _metric_collector_instance
    
    if _metric_collector_instance is not None:
        raise RuntimeError("Metric collector already configured")
    
    _metric_collector_instance = MetricCollector(
        collection_interval_seconds=collection_interval_seconds,
        include_process_metrics=include_process_metrics,
        include_system_metrics=include_system_metrics,
        include_disk_metrics=include_disk_metrics,
        include_network_metrics=include_network_metrics,
    )
    
    if start_immediately:
        _metric_collector_instance.start()
    
    return _metric_collector_instance