"""
Metrics Store - PostgreSQL-backed storage for benchmarking metrics.

Stores and queries agent performance metrics across multiple domains:
- Alignment: How well agents align with goals
- Autonomy: Independent decision-making capability
- Performance: Task completion, survival, resources
- Social: Inter-agent interactions and relationships
- Economic: Resource efficiency and utility
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import json
import os

try:
    from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Enum as SQLEnum
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False


class MetricCategory(str, Enum):
    """Categories of metrics aligned with evaluation domains."""
    ALIGNMENT = "alignment"
    AUTONOMY = "autonomy"
    PERFORMANCE = "performance"
    SOCIAL = "social"
    ECONOMIC = "economic"
    BEAUTY = "beauty"
    ENVIRONMENTAL = "environmental"


@dataclass
class Metric:
    """A single metric measurement."""
    agent_id: str
    category: MetricCategory
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'agent_id': self.agent_id,
            'category': self.category.value,
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


# SQLAlchemy models (only if available)
if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()

    class MetricRecord(Base):
        """SQLAlchemy model for metrics."""
        __tablename__ = 'metrics'

        id = Column(Integer, primary_key=True, autoincrement=True)
        agent_id = Column(String(36), nullable=False, index=True)
        session_id = Column(String(36), nullable=True, index=True)
        category = Column(String(50), nullable=False, index=True)
        name = Column(String(100), nullable=False, index=True)
        value = Column(Float, nullable=False)
        timestamp = Column(DateTime, default=datetime.utcnow, index=True)
        metadata_json = Column(Text, nullable=True)

    class SessionRecord(Base):
        """SQLAlchemy model for benchmark sessions."""
        __tablename__ = 'sessions'

        id = Column(Integer, primary_key=True, autoincrement=True)
        session_id = Column(String(36), unique=True, nullable=False)
        name = Column(String(200), nullable=True)
        started_at = Column(DateTime, default=datetime.utcnow)
        ended_at = Column(DateTime, nullable=True)
        config_json = Column(Text, nullable=True)
        status = Column(String(50), default='running')


class MetricsStore:
    """
    Store and query agent benchmarking metrics.

    Supports both PostgreSQL (production) and in-memory (testing) backends.
    """

    def __init__(self, database_url: Optional[str] = None, use_memory: bool = False):
        """
        Initialize metrics store.

        Args:
            database_url: PostgreSQL connection URL
            use_memory: If True, use in-memory storage instead of database
        """
        self.use_memory = use_memory or not SQLALCHEMY_AVAILABLE
        self.metrics: List[Metric] = []  # In-memory storage

        if not self.use_memory:
            # Use database
            self.database_url = database_url or os.getenv(
                'DATABASE_URL',
                'postgresql://malmo:malmo_password@localhost:5432/malmo_benchmarks'
            )
            self.engine = create_engine(self.database_url)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
        else:
            self.engine = None
            self.Session = None

    def record_metric(self, metric: Metric, session_id: Optional[str] = None) -> bool:
        """
        Record a single metric.

        Args:
            metric: Metric to record
            session_id: Optional benchmark session ID

        Returns:
            True if recorded successfully
        """
        if self.use_memory:
            self.metrics.append(metric)
            return True

        try:
            session = self.Session()
            record = MetricRecord(
                agent_id=metric.agent_id,
                session_id=session_id,
                category=metric.category.value,
                name=metric.name,
                value=metric.value,
                timestamp=metric.timestamp,
                metadata_json=json.dumps(metric.metadata) if metric.metadata else None
            )
            session.add(record)
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"Error recording metric: {e}")
            return False

    def record_metrics(self, metrics: List[Metric], session_id: Optional[str] = None) -> int:
        """
        Record multiple metrics.

        Args:
            metrics: List of metrics to record
            session_id: Optional benchmark session ID

        Returns:
            Number of metrics recorded successfully
        """
        count = 0
        for metric in metrics:
            if self.record_metric(metric, session_id):
                count += 1
        return count

    def get_agent_metrics(
        self,
        agent_id: str,
        category: Optional[MetricCategory] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Metric]:
        """
        Get metrics for a specific agent.

        Args:
            agent_id: Agent ID
            category: Optional category filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of results

        Returns:
            List of matching metrics
        """
        if self.use_memory:
            results = [m for m in self.metrics if m.agent_id == agent_id]
            if category:
                results = [m for m in results if m.category == category]
            if start_time:
                results = [m for m in results if m.timestamp >= start_time]
            if end_time:
                results = [m for m in results if m.timestamp <= end_time]
            return results[:limit]

        try:
            session = self.Session()
            query = session.query(MetricRecord).filter(
                MetricRecord.agent_id == agent_id
            )

            if category:
                query = query.filter(MetricRecord.category == category.value)
            if start_time:
                query = query.filter(MetricRecord.timestamp >= start_time)
            if end_time:
                query = query.filter(MetricRecord.timestamp <= end_time)

            query = query.order_by(MetricRecord.timestamp.desc()).limit(limit)
            records = query.all()
            session.close()

            return [
                Metric(
                    agent_id=r.agent_id,
                    category=MetricCategory(r.category),
                    name=r.name,
                    value=r.value,
                    timestamp=r.timestamp,
                    metadata=json.loads(r.metadata_json) if r.metadata_json else {}
                )
                for r in records
            ]
        except Exception as e:
            print(f"Error getting metrics: {e}")
            return []

    def get_session_metrics(
        self,
        session_id: str,
        category: Optional[MetricCategory] = None
    ) -> List[Metric]:
        """
        Get all metrics for a benchmark session.

        Args:
            session_id: Benchmark session ID
            category: Optional category filter

        Returns:
            List of metrics for the session
        """
        if self.use_memory:
            # In-memory doesn't track sessions
            return self.metrics

        try:
            session = self.Session()
            query = session.query(MetricRecord).filter(
                MetricRecord.session_id == session_id
            )

            if category:
                query = query.filter(MetricRecord.category == category.value)

            records = query.all()
            session.close()

            return [
                Metric(
                    agent_id=r.agent_id,
                    category=MetricCategory(r.category),
                    name=r.name,
                    value=r.value,
                    timestamp=r.timestamp,
                    metadata=json.loads(r.metadata_json) if r.metadata_json else {}
                )
                for r in records
            ]
        except Exception as e:
            print(f"Error getting session metrics: {e}")
            return []

    def get_metric_summary(
        self,
        agent_id: str,
        category: Optional[MetricCategory] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Get summary statistics for agent metrics.

        Args:
            agent_id: Agent ID
            category: Optional category filter

        Returns:
            Dictionary of {metric_name: {mean, min, max, count}}
        """
        metrics = self.get_agent_metrics(agent_id, category)

        summary: Dict[str, Dict[str, float]] = {}

        for metric in metrics:
            if metric.name not in summary:
                summary[metric.name] = {
                    'values': [],
                    'category': metric.category.value
                }
            summary[metric.name]['values'].append(metric.value)

        # Calculate statistics
        for name, data in summary.items():
            values = data['values']
            summary[name] = {
                'category': data['category'],
                'mean': sum(values) / len(values) if values else 0,
                'min': min(values) if values else 0,
                'max': max(values) if values else 0,
                'count': len(values)
            }

        return summary

    def clear_metrics(self, agent_id: Optional[str] = None) -> int:
        """
        Clear metrics (for testing).

        Args:
            agent_id: Optional agent ID to clear (all if None)

        Returns:
            Number of metrics cleared
        """
        if self.use_memory:
            if agent_id:
                original = len(self.metrics)
                self.metrics = [m for m in self.metrics if m.agent_id != agent_id]
                return original - len(self.metrics)
            else:
                count = len(self.metrics)
                self.metrics = []
                return count

        try:
            session = self.Session()
            if agent_id:
                count = session.query(MetricRecord).filter(
                    MetricRecord.agent_id == agent_id
                ).delete()
            else:
                count = session.query(MetricRecord).delete()
            session.commit()
            session.close()
            return count
        except Exception as e:
            print(f"Error clearing metrics: {e}")
            return 0


# Convenience functions for recording common metrics

def record_alignment_metric(
    store: MetricsStore,
    agent_id: str,
    name: str,
    value: float,
    **metadata
) -> bool:
    """Record an alignment metric."""
    return store.record_metric(Metric(
        agent_id=agent_id,
        category=MetricCategory.ALIGNMENT,
        name=name,
        value=value,
        metadata=metadata
    ))


def record_autonomy_metric(
    store: MetricsStore,
    agent_id: str,
    name: str,
    value: float,
    **metadata
) -> bool:
    """Record an autonomy metric."""
    return store.record_metric(Metric(
        agent_id=agent_id,
        category=MetricCategory.AUTONOMY,
        name=name,
        value=value,
        metadata=metadata
    ))


def record_performance_metric(
    store: MetricsStore,
    agent_id: str,
    name: str,
    value: float,
    **metadata
) -> bool:
    """Record a performance metric."""
    return store.record_metric(Metric(
        agent_id=agent_id,
        category=MetricCategory.PERFORMANCE,
        name=name,
        value=value,
        metadata=metadata
    ))


def record_social_metric(
    store: MetricsStore,
    agent_id: str,
    name: str,
    value: float,
    **metadata
) -> bool:
    """Record a social metric."""
    return store.record_metric(Metric(
        agent_id=agent_id,
        category=MetricCategory.SOCIAL,
        name=name,
        value=value,
        metadata=metadata
    ))
