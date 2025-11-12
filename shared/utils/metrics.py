#!/usr/bin/env python3
"""
Metrics collection utilities for DGX Spark Playbooks
"""

import time
import psutil
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


@dataclass
class MetricPoint:
    """Single metric data point"""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Metrics collector for monitoring"""

    def __init__(self, prefix: str = "dgx_spark"):
        """
        Initialize metrics collector

        Args:
            prefix: Metric name prefix
        """
        self.prefix = prefix
        self.metrics = {}
        self.prometheus_enabled = PROMETHEUS_AVAILABLE

        if self.prometheus_enabled:
            self._init_prometheus_metrics()

    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        if not self.prometheus_enabled:
            return

        # System metrics
        self.cpu_usage = Gauge(
            f'{self.prefix}_cpu_usage_percent',
            'CPU usage percentage'
        )

        self.memory_usage = Gauge(
            f'{self.prefix}_memory_usage_percent',
            'Memory usage percentage'
        )

        self.disk_usage = Gauge(
            f'{self.prefix}_disk_usage_percent',
            'Disk usage percentage'
        )

        # Request metrics
        self.request_count = Counter(
            f'{self.prefix}_requests_total',
            'Total request count',
            ['method', 'endpoint', 'status']
        )

        self.request_duration = Histogram(
            f'{self.prefix}_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint']
        )

        self.request_size = Summary(
            f'{self.prefix}_request_size_bytes',
            'Request size in bytes',
            ['method', 'endpoint']
        )

    def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> MetricPoint:
        """
        Record a metric

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels

        Returns:
            MetricPoint object
        """
        metric = MetricPoint(
            name=f"{self.prefix}_{name}",
            value=value,
            labels=labels or {}
        )

        # Store in internal metrics
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(metric)

        return metric

    def update_system_metrics(self):
        """Update system metrics"""
        if self.prometheus_enabled:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_usage.set(cpu_percent)

            # Memory
            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.percent)

            # Disk
            disk = psutil.disk_usage('/')
            self.disk_usage.set(disk.percent)

        # Record internally
        self.record_metric('cpu_usage', psutil.cpu_percent(interval=0.1))
        self.record_metric('memory_usage', psutil.virtual_memory().percent)
        self.record_metric('disk_usage', psutil.disk_usage('/').percent)

    def record_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float,
        size: Optional[int] = None
    ):
        """
        Record HTTP request metrics

        Args:
            method: HTTP method
            endpoint: Request endpoint
            status: HTTP status code
            duration: Request duration in seconds
            size: Request size in bytes
        """
        if self.prometheus_enabled:
            self.request_count.labels(
                method=method,
                endpoint=endpoint,
                status=str(status)
            ).inc()

            self.request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            if size:
                self.request_size.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(size)

    def get_metrics(self, name: Optional[str] = None) -> Dict:
        """
        Get recorded metrics

        Args:
            name: Specific metric name (optional)

        Returns:
            Dictionary of metrics
        """
        if name:
            return {
                name: [
                    {
                        'value': m.value,
                        'timestamp': m.timestamp,
                        'labels': m.labels
                    }
                    for m in self.metrics.get(name, [])
                ]
            }

        return {
            name: [
                {
                    'value': m.value,
                    'timestamp': m.timestamp,
                    'labels': m.labels
                }
                for m in metrics
            ]
            for name, metrics in self.metrics.items()
        }

    def clear_metrics(self, name: Optional[str] = None):
        """
        Clear recorded metrics

        Args:
            name: Specific metric name to clear (clears all if not specified)
        """
        if name:
            self.metrics.pop(name, None)
        else:
            self.metrics.clear()
