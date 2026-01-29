"""
Benchmarking System - Metrics collection and evaluation for AI agents.

Provides:
- MetricsStore: PostgreSQL-backed storage for agent metrics
- BenchmarkEvaluator: Score calculation across evaluation domains

Evaluation Domains:
1. Alignment - Goal adherence and cooperative behavior
2. Autonomy - Independent decision-making
3. Performance - Task completion and survival
4. Social - Inter-agent interactions
5. Economic - Resource efficiency
"""

from .metrics_store import MetricsStore, Metric, MetricCategory
from .evaluator import BenchmarkEvaluator, EvaluationReport

__all__ = [
    'MetricsStore',
    'Metric',
    'MetricCategory',
    'BenchmarkEvaluator',
    'EvaluationReport',
]
