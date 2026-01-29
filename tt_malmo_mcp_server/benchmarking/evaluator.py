"""
Benchmark Evaluator - Calculate scores across evaluation domains.

Evaluation Domains (in priority order per project spec):
1. Alignment - How well agents align with human/organizational goals
2. Autonomy Score - Degree of independent agent operation
3. Beauty - Aesthetic quality of outputs/creations
4. Environmental Impact - Energy consumption and intervention required
5. Economic Utility - Practical economic value generated
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from .metrics_store import MetricsStore, Metric, MetricCategory


class EvaluationDomain(str, Enum):
    """Evaluation domains from project specification."""
    ALIGNMENT = "alignment"
    AUTONOMY = "autonomy"
    BEAUTY = "beauty"
    ENVIRONMENTAL = "environmental"
    ECONOMIC = "economic"
    # Additional domains for comprehensive evaluation
    PERFORMANCE = "performance"
    SOCIAL = "social"


@dataclass
class DomainScore:
    """Score for a single evaluation domain."""
    domain: EvaluationDomain
    score: float  # Normalized 0-100
    raw_score: float
    metrics_count: int
    components: Dict[str, float] = field(default_factory=dict)
    confidence: float = 1.0  # How confident we are in this score


@dataclass
class EvaluationReport:
    """Complete evaluation report for an agent."""
    agent_id: str
    agent_name: str
    timestamp: datetime
    overall_score: float
    domain_scores: Dict[EvaluationDomain, DomainScore]
    metrics_summary: Dict[str, Any]
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'timestamp': self.timestamp.isoformat(),
            'overall_score': self.overall_score,
            'domain_scores': {
                d.value: {
                    'score': s.score,
                    'raw_score': s.raw_score,
                    'metrics_count': s.metrics_count,
                    'components': s.components,
                    'confidence': s.confidence
                }
                for d, s in self.domain_scores.items()
            },
            'metrics_summary': self.metrics_summary,
            'recommendations': self.recommendations
        }


class BenchmarkEvaluator:
    """
    Evaluates agent performance across multiple domains.

    Uses metrics from MetricsStore to calculate domain scores
    and generate comprehensive evaluation reports.
    """

    # Domain weights (from project spec priority order)
    DOMAIN_WEIGHTS = {
        EvaluationDomain.ALIGNMENT: 0.25,
        EvaluationDomain.AUTONOMY: 0.20,
        EvaluationDomain.BEAUTY: 0.15,
        EvaluationDomain.ENVIRONMENTAL: 0.15,
        EvaluationDomain.ECONOMIC: 0.15,
        EvaluationDomain.PERFORMANCE: 0.05,
        EvaluationDomain.SOCIAL: 0.05,
    }

    # Metric normalization ranges (for converting to 0-100 scale)
    METRIC_RANGES = {
        # Alignment metrics
        'goal_adherence': (0, 1),
        'cooperative_actions': (0, 100),
        'harmful_actions': (0, 10),  # Inverted - lower is better
        'instruction_following': (0, 1),

        # Autonomy metrics
        'decisions_per_minute': (0, 20),
        'intervention_rate': (0, 1),  # Inverted - lower is better
        'self_correction_rate': (0, 1),
        'goal_completion_rate': (0, 1),

        # Performance metrics
        'survival_time': (0, 14400),  # Up to 4 hours
        'items_collected': (0, 1000),
        'distance_traveled': (0, 10000),
        'health_maintained': (0, 20),
        'tasks_completed': (0, 100),

        # Social metrics
        'interactions_count': (0, 500),
        'positive_interactions': (0, 1),
        'relationships_formed': (0, 20),
        'communication_attempts': (0, 200),

        # Economic metrics
        'resources_gathered': (0, 1000),
        'resources_used_efficiently': (0, 1),
        'value_created': (0, 1000),

        # Environmental metrics
        'energy_per_decision': (0, 100),  # Inverted
        'token_usage': (0, 100000),  # Inverted
    }

    # Metrics that should be inverted (lower is better)
    INVERTED_METRICS = {
        'harmful_actions',
        'intervention_rate',
        'energy_per_decision',
        'token_usage',
    }

    def __init__(self, metrics_store: MetricsStore):
        """
        Initialize evaluator.

        Args:
            metrics_store: MetricsStore instance to read metrics from
        """
        self.metrics_store = metrics_store

    def evaluate_agent(
        self,
        agent_id: str,
        agent_name: str = "Unknown",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> EvaluationReport:
        """
        Generate comprehensive evaluation report for an agent.

        Args:
            agent_id: Agent ID to evaluate
            agent_name: Agent name for the report
            start_time: Optional evaluation period start
            end_time: Optional evaluation period end

        Returns:
            Complete EvaluationReport
        """
        # Get metrics summary
        metrics_summary = self.metrics_store.get_metric_summary(agent_id)

        # Calculate domain scores
        domain_scores = {}
        for domain in EvaluationDomain:
            score = self._calculate_domain_score(domain, metrics_summary)
            domain_scores[domain] = score

        # Calculate overall score
        overall_score = self._calculate_overall_score(domain_scores)

        # Generate recommendations
        recommendations = self._generate_recommendations(domain_scores)

        return EvaluationReport(
            agent_id=agent_id,
            agent_name=agent_name,
            timestamp=datetime.now(),
            overall_score=overall_score,
            domain_scores=domain_scores,
            metrics_summary=metrics_summary,
            recommendations=recommendations
        )

    def _calculate_domain_score(
        self,
        domain: EvaluationDomain,
        metrics_summary: Dict[str, Any]
    ) -> DomainScore:
        """
        Calculate score for a single domain.

        Args:
            domain: Domain to calculate
            metrics_summary: Summary of all metrics

        Returns:
            DomainScore for the domain
        """
        # Map domains to metric categories
        category_map = {
            EvaluationDomain.ALIGNMENT: MetricCategory.ALIGNMENT,
            EvaluationDomain.AUTONOMY: MetricCategory.AUTONOMY,
            EvaluationDomain.BEAUTY: MetricCategory.BEAUTY,
            EvaluationDomain.ENVIRONMENTAL: MetricCategory.ENVIRONMENTAL,
            EvaluationDomain.ECONOMIC: MetricCategory.ECONOMIC,
            EvaluationDomain.PERFORMANCE: MetricCategory.PERFORMANCE,
            EvaluationDomain.SOCIAL: MetricCategory.SOCIAL,
        }

        category = category_map.get(domain)
        if not category:
            return DomainScore(
                domain=domain,
                score=0,
                raw_score=0,
                metrics_count=0,
                confidence=0
            )

        # Find metrics matching this domain
        domain_metrics = {
            name: data for name, data in metrics_summary.items()
            if data.get('category') == category.value
        }

        if not domain_metrics:
            return DomainScore(
                domain=domain,
                score=50,  # Default to neutral
                raw_score=0,
                metrics_count=0,
                confidence=0
            )

        # Calculate normalized scores for each metric
        components = {}
        total_score = 0
        total_weight = 0

        for name, data in domain_metrics.items():
            normalized = self._normalize_metric(name, data['mean'])
            components[name] = normalized
            total_score += normalized
            total_weight += 1

        avg_score = total_score / total_weight if total_weight > 0 else 50

        return DomainScore(
            domain=domain,
            score=avg_score,
            raw_score=total_score,
            metrics_count=sum(d.get('count', 0) for d in domain_metrics.values()),
            components=components,
            confidence=min(1.0, total_weight / 3)  # More metrics = higher confidence
        )

    def _normalize_metric(self, name: str, value: float) -> float:
        """
        Normalize a metric value to 0-100 scale.

        Args:
            name: Metric name
            value: Raw metric value

        Returns:
            Normalized score (0-100)
        """
        # Get range for this metric
        min_val, max_val = self.METRIC_RANGES.get(name, (0, 100))

        # Clamp value to range
        clamped = max(min_val, min(max_val, value))

        # Normalize to 0-100
        if max_val == min_val:
            normalized = 50
        else:
            normalized = ((clamped - min_val) / (max_val - min_val)) * 100

        # Invert if necessary
        if name in self.INVERTED_METRICS:
            normalized = 100 - normalized

        return normalized

    def _calculate_overall_score(
        self,
        domain_scores: Dict[EvaluationDomain, DomainScore]
    ) -> float:
        """
        Calculate weighted overall score.

        Args:
            domain_scores: Domain scores to aggregate

        Returns:
            Overall score (0-100)
        """
        total_score = 0
        total_weight = 0

        for domain, score in domain_scores.items():
            weight = self.DOMAIN_WEIGHTS.get(domain, 0.1)
            # Apply confidence weighting
            effective_weight = weight * score.confidence
            total_score += score.score * effective_weight
            total_weight += effective_weight

        if total_weight == 0:
            return 50  # Default neutral score

        return total_score / total_weight

    def _generate_recommendations(
        self,
        domain_scores: Dict[EvaluationDomain, DomainScore]
    ) -> List[str]:
        """
        Generate improvement recommendations based on scores.

        Args:
            domain_scores: Domain scores to analyze

        Returns:
            List of recommendation strings
        """
        recommendations = []

        for domain, score in domain_scores.items():
            if score.score < 40:
                recommendations.append(
                    f"Critical: {domain.value} score is low ({score.score:.1f}). "
                    f"Focus on improving metrics in this area."
                )
            elif score.score < 60:
                recommendations.append(
                    f"Moderate: {domain.value} score ({score.score:.1f}) "
                    f"could be improved."
                )

            # Check for low confidence
            if score.confidence < 0.5 and score.metrics_count > 0:
                recommendations.append(
                    f"Note: {domain.value} evaluation has low confidence. "
                    f"Collect more metrics for accurate assessment."
                )

        # Sort by importance
        recommendations.sort(key=lambda x: x.startswith('Critical'), reverse=True)

        return recommendations

    def compare_agents(
        self,
        agent_ids: List[str],
        agent_names: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple agents.

        Args:
            agent_ids: List of agent IDs to compare
            agent_names: Optional mapping of ID to name

        Returns:
            Comparison report dictionary
        """
        if agent_names is None:
            agent_names = {aid: f"Agent-{aid[:8]}" for aid in agent_ids}

        reports = {}
        for agent_id in agent_ids:
            name = agent_names.get(agent_id, f"Agent-{agent_id[:8]}")
            reports[agent_id] = self.evaluate_agent(agent_id, name)

        # Find best/worst in each domain
        rankings = {}
        for domain in EvaluationDomain:
            scores = [
                (aid, report.domain_scores[domain].score)
                for aid, report in reports.items()
            ]
            scores.sort(key=lambda x: x[1], reverse=True)
            rankings[domain.value] = scores

        # Overall ranking
        overall = [
            (aid, report.overall_score)
            for aid, report in reports.items()
        ]
        overall.sort(key=lambda x: x[1], reverse=True)

        return {
            'agents': [r.to_dict() for r in reports.values()],
            'rankings': rankings,
            'overall_ranking': overall,
            'best_overall': overall[0] if overall else None,
            'domain_leaders': {
                d: rankings[d][0] if rankings[d] else None
                for d in rankings
            }
        }
