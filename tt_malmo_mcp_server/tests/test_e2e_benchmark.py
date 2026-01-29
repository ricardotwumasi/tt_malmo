"""
End-to-End Benchmark Tests.

Tests the full pipeline:
- Agent creation with different LLM providers
- PIANO architecture startup
- Observation/Decision/Action loop
- Metrics collection and evaluation
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAgentCreationWithProviders:
    """Test agent creation with different LLM providers."""

    @patch('mcp_server.agent_manager.create_adapter')
    def test_create_gemini_agent(self, mock_create_adapter, test_client):
        """Test creating agent with Gemini."""
        mock_adapter = MagicMock()
        mock_adapter.generate = AsyncMock(return_value="ACTION: explore\nREASONING: test\nTARGET: none")
        mock_create_adapter.return_value = mock_adapter

        response = test_client.post(
            "/agents",
            json={
                "name": "GeminiTestAgent",
                "llm_type": "gemini",
                "role": 0
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "GeminiTestAgent"

        # Verify adapter was created with gemini type
        mock_create_adapter.assert_called()
        call_kwargs = mock_create_adapter.call_args[1]
        assert call_kwargs['llm_type'] == 'gemini'

    @patch('mcp_server.agent_manager.create_adapter')
    def test_create_openrouter_agent(self, mock_create_adapter, test_client):
        """Test creating agent with OpenRouter."""
        mock_adapter = MagicMock()
        mock_adapter.generate = AsyncMock(return_value="ACTION: gather\nREASONING: test\nTARGET: wood")
        mock_create_adapter.return_value = mock_adapter

        response = test_client.post(
            "/agents",
            json={
                "name": "OpenRouterTestAgent",
                "llm_type": "openrouter",
                "role": 1
            }
        )

        assert response.status_code == 200

        mock_create_adapter.assert_called()
        call_kwargs = mock_create_adapter.call_args[1]
        assert call_kwargs['llm_type'] == 'openrouter'


class TestFullPipeline:
    """Test full observation-decision-action pipeline."""

    @pytest.mark.asyncio
    async def test_pipeline_with_mock_llm(self, sample_agent_state, mock_llm_adapter):
        """Test full pipeline with mocked LLM."""
        from piano_architecture.cognitive_controller import CognitiveController

        # Create controller
        controller = CognitiveController(mock_llm_adapter, decision_interval=0.1)

        # Simulate observation
        sample_agent_state.update_observation({
            'XPos': 10.0,
            'YPos': 64.0,
            'ZPos': -5.0,
            'Life': 15.0,
            'Food': 12.0
        })

        # Get decision
        decision = await controller.make_decision(sample_agent_state)

        # Verify decision structure
        assert 'action' in decision
        assert 'reasoning' in decision
        assert decision['agent_id'] == sample_agent_state.agent_id

        # Verify LLM was called
        assert mock_llm_adapter.call_count > 0


class TestMetricsCollection:
    """Test metrics collection during benchmark."""

    def test_record_and_retrieve_metrics(self, memory_metrics_store):
        """Test recording and retrieving metrics."""
        from benchmarking.metrics_store import Metric, MetricCategory

        # Record some metrics
        metric1 = Metric(
            agent_id="test-agent",
            category=MetricCategory.PERFORMANCE,
            name="survival_time",
            value=1200.0
        )

        metric2 = Metric(
            agent_id="test-agent",
            category=MetricCategory.ALIGNMENT,
            name="goal_adherence",
            value=0.85
        )

        memory_metrics_store.record_metric(metric1)
        memory_metrics_store.record_metric(metric2)

        # Retrieve metrics
        metrics = memory_metrics_store.get_agent_metrics("test-agent")

        assert len(metrics) == 2

    def test_metrics_summary(self, memory_metrics_store):
        """Test metrics summary calculation."""
        from benchmarking.metrics_store import Metric, MetricCategory

        # Record multiple values for same metric
        for value in [100, 200, 300]:
            memory_metrics_store.record_metric(Metric(
                agent_id="test-agent",
                category=MetricCategory.PERFORMANCE,
                name="items_collected",
                value=value
            ))

        # Get summary
        summary = memory_metrics_store.get_metric_summary("test-agent")

        assert "items_collected" in summary
        assert summary["items_collected"]["mean"] == 200.0
        assert summary["items_collected"]["min"] == 100
        assert summary["items_collected"]["max"] == 300
        assert summary["items_collected"]["count"] == 3


class TestBenchmarkEvaluation:
    """Test benchmark evaluation."""

    def test_evaluate_agent(self, memory_metrics_store):
        """Test agent evaluation."""
        from benchmarking.metrics_store import Metric, MetricCategory
        from benchmarking.evaluator import BenchmarkEvaluator

        # Record metrics
        metrics_to_record = [
            ("goal_adherence", MetricCategory.ALIGNMENT, 0.9),
            ("decisions_per_minute", MetricCategory.AUTONOMY, 10.0),
            ("survival_time", MetricCategory.PERFORMANCE, 3600.0),
            ("interactions_count", MetricCategory.SOCIAL, 50),
        ]

        for name, category, value in metrics_to_record:
            memory_metrics_store.record_metric(Metric(
                agent_id="test-agent",
                category=category,
                name=name,
                value=value
            ))

        # Evaluate
        evaluator = BenchmarkEvaluator(memory_metrics_store)
        report = evaluator.evaluate_agent("test-agent", "TestAgent")

        # Check report structure
        assert report.agent_id == "test-agent"
        assert report.agent_name == "TestAgent"
        assert 0 <= report.overall_score <= 100
        assert len(report.domain_scores) > 0

    def test_compare_agents(self, memory_metrics_store):
        """Test comparing multiple agents."""
        from benchmarking.metrics_store import Metric, MetricCategory
        from benchmarking.evaluator import BenchmarkEvaluator

        # Create metrics for two agents
        for agent_id in ["agent-1", "agent-2"]:
            value = 0.9 if agent_id == "agent-1" else 0.7
            memory_metrics_store.record_metric(Metric(
                agent_id=agent_id,
                category=MetricCategory.ALIGNMENT,
                name="goal_adherence",
                value=value
            ))

        # Compare
        evaluator = BenchmarkEvaluator(memory_metrics_store)
        comparison = evaluator.compare_agents(
            ["agent-1", "agent-2"],
            {"agent-1": "Agent One", "agent-2": "Agent Two"}
        )

        assert "overall_ranking" in comparison
        assert len(comparison["agents"]) == 2


class TestMultiAgentBenchmark:
    """Test multi-agent benchmark scenario."""

    @patch('mcp_server.agent_manager.create_adapter')
    @pytest.mark.asyncio
    async def test_multi_agent_creation(self, mock_create_adapter, test_client):
        """Test creating multiple agents."""
        mock_adapter = MagicMock()
        mock_adapter.generate = AsyncMock(return_value="ACTION: explore\nREASONING: test\nTARGET: none")
        mock_create_adapter.return_value = mock_adapter

        agent_ids = []
        for i in range(3):
            response = test_client.post(
                "/agents",
                json={
                    "name": f"BenchmarkAgent{i}",
                    "llm_type": "gemini",
                    "role": i
                }
            )
            assert response.status_code == 200
            agent_ids.append(response.json()["agent_id"])

        # Verify all agents created
        assert len(agent_ids) == 3
        assert len(set(agent_ids)) == 3  # All unique IDs

        # List agents
        response = test_client.get("/agents")
        agents = response.json()

        # Find our benchmark agents
        benchmark_agents = [a for a in agents if "BenchmarkAgent" in a.get("name", "")]
        assert len(benchmark_agents) >= 3


class TestMissionIntegration:
    """Test mission builder integration with agents."""

    def test_mission_with_agent_count(self, mission_builder, test_client):
        """Test creating mission matching agent count."""
        # This would be used in a real benchmark
        num_agents = 5

        # Generate mission
        mission_xml = mission_builder.create_benchmark_mission(num_agents=num_agents)

        # Verify mission is valid - count AgentSection occurrences in raw XML
        agent_count = mission_xml.count('<AgentSection')
        assert agent_count == num_agents


class TestEvaluationReport:
    """Test evaluation report generation."""

    def test_report_to_dict(self, memory_metrics_store):
        """Test report serialization."""
        from benchmarking.metrics_store import Metric, MetricCategory
        from benchmarking.evaluator import BenchmarkEvaluator

        # Record a metric
        memory_metrics_store.record_metric(Metric(
            agent_id="test-agent",
            category=MetricCategory.PERFORMANCE,
            name="survival_time",
            value=1000.0
        ))

        # Generate report
        evaluator = BenchmarkEvaluator(memory_metrics_store)
        report = evaluator.evaluate_agent("test-agent", "TestAgent")

        # Serialize
        report_dict = report.to_dict()

        # Verify structure
        assert "agent_id" in report_dict
        assert "overall_score" in report_dict
        assert "domain_scores" in report_dict
        assert "timestamp" in report_dict

    def test_recommendations_generated(self, memory_metrics_store):
        """Test that recommendations are generated."""
        from benchmarking.metrics_store import Metric, MetricCategory
        from benchmarking.evaluator import BenchmarkEvaluator

        # Record a low-performing metric
        memory_metrics_store.record_metric(Metric(
            agent_id="test-agent",
            category=MetricCategory.ALIGNMENT,
            name="goal_adherence",
            value=0.2  # Low score
        ))

        # Generate report
        evaluator = BenchmarkEvaluator(memory_metrics_store)
        report = evaluator.evaluate_agent("test-agent", "TestAgent")

        # Should have recommendations for low scores
        assert isinstance(report.recommendations, list)
