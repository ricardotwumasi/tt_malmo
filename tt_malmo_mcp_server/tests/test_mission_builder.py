"""
Tests for Mission Builder.

Tests cover:
- Mission XML generation
- Agent section creation
- Resource placement
- Multi-agent support
"""

import pytest
import xml.etree.ElementTree as ET
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMissionBuilderInit:
    """Test MissionBuilder initialization."""

    def test_init(self, mission_builder):
        """Test MissionBuilder initialization."""
        assert mission_builder.mission_name == "PIANO_Benchmark_Mission"


class TestBenchmarkMissionGeneration:
    """Test benchmark mission XML generation."""

    def test_create_benchmark_mission_valid_xml(self, mission_builder):
        """Test that generated XML is valid."""
        xml_str = mission_builder.create_benchmark_mission(num_agents=3)

        # Should be parseable XML
        root = ET.fromstring(xml_str)
        # Handle namespace in tag
        assert 'Mission' in root.tag

    def test_create_benchmark_mission_agent_count(self, mission_builder):
        """Test that correct number of agents are created."""
        for num_agents in [1, 5, 10]:
            xml_str = mission_builder.create_benchmark_mission(num_agents=num_agents)

            # Count AgentSection occurrences in raw XML (namespace-agnostic)
            agent_count = xml_str.count('<AgentSection')
            assert agent_count == num_agents

    def test_create_benchmark_mission_server_section(self, mission_builder):
        """Test server section is present."""
        xml_str = mission_builder.create_benchmark_mission(num_agents=2)

        # Check for ServerSection in raw XML
        assert '<ServerSection>' in xml_str
        assert '<ServerHandlers>' in xml_str

    def test_create_benchmark_mission_has_resources(self, mission_builder):
        """Test that resources are placed in the mission."""
        xml_str = mission_builder.create_benchmark_mission(num_agents=2)

        # Check for resource-related elements
        assert 'DrawTree' in xml_str or 'DrawCuboid' in xml_str
        assert 'stone' in xml_str or 'iron_ore' in xml_str


class TestAgentSectionGeneration:
    """Test agent section generation."""

    def test_agent_section_has_name(self, mission_builder):
        """Test that each agent has a unique name."""
        xml_str = mission_builder.create_benchmark_mission(num_agents=5)
        root = ET.fromstring(xml_str)

        agent_sections = root.findall('.//AgentSection')
        names = [section.find('.//Name').text for section in agent_sections]

        # All names should be unique
        assert len(names) == len(set(names))
        # Names should follow pattern
        for i, name in enumerate(names):
            assert name == f'Agent{i}'

    def test_agent_section_has_placement(self, mission_builder):
        """Test that each agent has a spawn placement."""
        xml_str = mission_builder.create_benchmark_mission(num_agents=3)
        root = ET.fromstring(xml_str)

        agent_sections = root.findall('.//AgentSection')

        for section in agent_sections:
            placement = section.find('.//Placement')
            assert placement is not None
            assert 'x' in placement.attrib
            assert 'y' in placement.attrib
            assert 'z' in placement.attrib

    def test_agent_section_has_handlers(self, mission_builder):
        """Test that agents have observation and action handlers."""
        xml_str = mission_builder.create_benchmark_mission(num_agents=2)

        # Check for handlers in raw XML (namespace-agnostic)
        assert '<AgentHandlers>' in xml_str
        assert '<ObservationFromFullStats/>' in xml_str
        assert '<ContinuousMovementCommands' in xml_str


class TestSpawnLocationCalculation:
    """Test spawn location calculation."""

    def test_spawn_locations_different(self, mission_builder):
        """Test that spawn locations are different for each agent."""
        locations = []
        for i in range(5):
            x, y, z = mission_builder._get_spawn_location(i, 5)
            locations.append((x, y, z))

        # All locations should be unique
        assert len(locations) == len(set(locations))

    def test_spawn_locations_in_circle(self, mission_builder):
        """Test that spawn locations form a circle pattern."""
        import math

        locations = []
        for i in range(8):
            x, y, z = mission_builder._get_spawn_location(i, 8)
            locations.append((x, z))

        # All should be roughly same distance from center
        distances = [math.sqrt(x**2 + z**2) for x, z in locations]
        avg_distance = sum(distances) / len(distances)

        for dist in distances:
            assert abs(dist - avg_distance) < 1.0  # Within 1 block tolerance


class TestSimpleTestMission:
    """Test simple test mission generation."""

    def test_create_simple_mission_valid_xml(self, mission_builder):
        """Test that simple mission XML is valid."""
        xml_str = mission_builder.create_simple_test_mission(num_agents=2)

        root = ET.fromstring(xml_str)
        # Handle namespace in tag
        assert 'Mission' in root.tag

    def test_create_simple_mission_agent_count(self, mission_builder):
        """Test simple mission has correct agent count."""
        xml_str = mission_builder.create_simple_test_mission(num_agents=3)

        # Count AgentSection occurrences in raw XML
        agent_count = xml_str.count('<AgentSection')
        assert agent_count == 3

    def test_create_simple_mission_minimal(self, mission_builder):
        """Test simple mission is minimal (no complex handlers)."""
        xml_str = mission_builder.create_simple_test_mission(num_agents=1)

        # Should have basic handlers only
        assert 'ObservationFromFullStats' in xml_str
        assert 'ContinuousMovementCommands' in xml_str

        # Should not have complex elements
        assert 'VideoProducer' not in xml_str
        assert 'ChatCommands' not in xml_str


class TestResourceGeneration:
    """Test resource generation."""

    def test_generate_resources(self, mission_builder):
        """Test resource generation XML."""
        resources = mission_builder._generate_resources(100)

        assert 'DrawTree' in resources
        assert 'stone' in resources
        assert 'iron_ore' in resources or 'coal_ore' in resources


class TestEdgeCases:
    """Test edge cases."""

    def test_single_agent(self, mission_builder):
        """Test mission with single agent."""
        xml_str = mission_builder.create_benchmark_mission(num_agents=1)

        # Count AgentSection occurrences
        agent_count = xml_str.count('<AgentSection')
        assert agent_count == 1

    def test_many_agents(self, mission_builder):
        """Test mission with many agents."""
        xml_str = mission_builder.create_benchmark_mission(num_agents=50)

        # Count AgentSection occurrences
        agent_count = xml_str.count('<AgentSection')
        assert agent_count == 50
