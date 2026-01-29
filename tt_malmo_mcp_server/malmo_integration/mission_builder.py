"""
Mission Builder - Creates Malmo mission XML for multi-agent benchmarking.

Generates missions with:
- Survival mode gameplay
- Resource-rich environment
- Multiple agent spawn points
- Observation and action handlers
"""

from typing import List, Tuple
import math


class MissionBuilder:
    """
    Builds Malmo mission XML for benchmarking agents.
    """

    def __init__(self):
        """Initialize Mission Builder."""
        self.mission_name = "PIANO_Benchmark_Mission"

    def create_benchmark_mission(self, num_agents: int = 10,
                                world_size: int = 100,
                                difficulty: str = "normal") -> str:
        """
        Generate complete mission XML for benchmarking.

        Args:
            num_agents: Number of agents to spawn
            world_size: Size of world in blocks
            difficulty: Minecraft difficulty (peaceful/easy/normal/hard)

        Returns:
            Complete mission XML string
        """
        xml = self._create_mission_header()
        xml += self._create_server_section(world_size, difficulty)

        # Create agent sections
        for i in range(num_agents):
            xml += self._create_agent_section(i, num_agents, world_size)

        xml += self._create_mission_footer()

        return xml

    def _create_mission_header(self) -> str:
        """Create mission XML header."""
        return f'''<?xml version="1.0" encoding="UTF-8" ?>
<Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <About>
        <Summary>{self.mission_name} - Multi-agent civilizational benchmarking</Summary>
    </About>

    <ModSettings>
        <MsPerTick>50</MsPerTick>
    </ModSettings>

'''

    def _create_server_section(self, world_size: int, difficulty: str) -> str:
        """
        Create server section with world generation.

        Args:
            world_size: Size of world
            difficulty: Minecraft difficulty

        Returns:
            Server section XML
        """
        xml = f'''    <ServerSection>
        <ServerInitialConditions>
            <Time>
                <StartTime>6000</StartTime>
                <AllowPassageOfTime>true</AllowPassageOfTime>
            </Time>
            <Weather>clear</Weather>
            <AllowSpawning>true</AllowSpawning>
        </ServerInitialConditions>

        <ServerHandlers>
            <!-- Flat world with resources -->
            <FlatWorldGenerator
                generatorString="3;minecraft:bedrock,2*minecraft:dirt,minecraft:grass;1;village"
                forceReset="false"/>

            <DrawingDecorator>
                {self._generate_resources(world_size)}
            </DrawingDecorator>

            <ServerQuitFromTimeUp timeLimitMs="14400000" description="4 hour time limit"/>
            <ServerQuitWhenAnyAgentFinishes/>
        </ServerHandlers>
    </ServerSection>

'''
        return xml

    def _generate_resources(self, world_size: int) -> str:
        """
        Generate resource placement XML (trees, ores, animals).

        Args:
            world_size: Size of world

        Returns:
            Resource placement XML
        """
        resources = ""

        # Place trees (wood resource)
        for i in range(20):
            x = (i % 5) * 20 - 40
            z = (i // 5) * 20 - 40
            resources += f'''
                <DrawTree x="{x}" y="4" z="{z}" type="oak"/>'''

        # Place stone and ore deposits
        resources += '''
                <DrawCuboid x1="-50" y1="1" z1="-50" x2="50" y2="2" z2="50" type="stone"/>
                <DrawCuboid x1="-30" y1="1" z1="-30" x2="-25" y2="1" z2="-25" type="iron_ore"/>
                <DrawCuboid x1="25" y1="1" z1="25" x2="30" y2="1" z2="30" type="coal_ore"/>
'''

        # Place animals (food source)
        animals = ["cow", "pig", "sheep", "chicken"]
        for i, animal in enumerate(animals):
            x = (i - 2) * 15
            z = 30
            resources += f'''
                <DrawEntity x="{x}" y="4" z="{z}" type="{animal}"/>'''

        return resources

    def _create_agent_section(self, agent_idx: int, total_agents: int,
                             world_size: int) -> str:
        """
        Create agent section with spawn point and handlers.

        Args:
            agent_idx: Agent index (0, 1, 2, ...)
            total_agents: Total number of agents
            world_size: Size of world

        Returns:
            Agent section XML
        """
        # Calculate spawn position (circle layout)
        spawn_x, spawn_y, spawn_z = self._get_spawn_location(agent_idx, total_agents)

        xml = f'''    <AgentSection mode="Survival">
        <Name>Agent{agent_idx}</Name>

        <AgentStart>
            <Placement x="{spawn_x}" y="{spawn_y}" z="{spawn_z}" pitch="0" yaw="{agent_idx * 30}"/>
            <Inventory>
                <!-- Start with basic tools -->
                <InventoryItem slot="0" type="wooden_pickaxe"/>
                <InventoryItem slot="1" type="wooden_axe"/>
            </Inventory>
        </AgentStart>

        <AgentHandlers>
            <!-- Observations -->
            <ObservationFromFullStats/>

            <ObservationFromNearbyEntities>
                <Range name="entities" xrange="20" yrange="10" zrange="20"/>
            </ObservationFromNearbyEntities>

            <ObservationFromGrid>
                <Grid name="floor">
                    <min x="-1" y="-1" z="-1"/>
                    <max x="1" y="-1" z="1"/>
                </Grid>
            </ObservationFromGrid>

            <ObservationFromRay/>

            <!-- Actions -->
            <ContinuousMovementCommands turnSpeedDegs="180"/>
            <DiscreteMovementCommands/>
            <InventoryCommands/>
            <ChatCommands/>
            <SimpleCraftCommands/>
            <MissionQuitCommands/>

            <!-- Video (optional, for debugging) -->
            <VideoProducer>
                <Width>320</Width>
                <Height>240</Height>
            </VideoProducer>
        </AgentHandlers>
    </AgentSection>

'''
        return xml

    def _get_spawn_location(self, agent_idx: int, total_agents: int) -> Tuple[float, float, float]:
        """
        Calculate spawn location for agent.

        Agents spawn in a circle pattern.

        Args:
            agent_idx: Agent index
            total_agents: Total number of agents

        Returns:
            (x, y, z) spawn coordinates
        """
        # Spawn in circle with radius 20 blocks
        radius = 20.0
        angle = (2 * math.pi * agent_idx) / total_agents

        x = radius * math.cos(angle)
        y = 4.0  # Slightly above ground
        z = radius * math.sin(angle)

        return (round(x, 1), y, round(z, 1))

    def _create_mission_footer(self) -> str:
        """Create mission XML footer."""
        return '''</Mission>
'''

    def create_simple_test_mission(self, num_agents: int = 2) -> str:
        """
        Create simple test mission for debugging.

        Args:
            num_agents: Number of agents

        Returns:
            Simple test mission XML
        """
        xml = self._create_mission_header()
        xml += '''    <ServerSection>
        <ServerInitialConditions>
            <Time>
                <StartTime>6000</StartTime>
                <AllowPassageOfTime>false</AllowPassageOfTime>
            </Time>
            <Weather>clear</Weather>
        </ServerInitialConditions>

        <ServerHandlers>
            <FlatWorldGenerator generatorString="3;7,2*3,2;1;"/>
        </ServerHandlers>
    </ServerSection>

'''

        # Simple agent sections
        for i in range(num_agents):
            x = i * 5
            xml += f'''    <AgentSection mode="Survival">
        <Name>Agent{i}</Name>
        <AgentStart>
            <Placement x="{x}" y="4" z="0"/>
        </AgentStart>
        <AgentHandlers>
            <ObservationFromFullStats/>
            <ContinuousMovementCommands/>
            <VideoProducer want_depth="false">
                <Width>320</Width>
                <Height>240</Height>
            </VideoProducer>
        </AgentHandlers>
    </AgentSection>

'''

        xml += self._create_mission_footer()

        return xml


# Example usage
if __name__ == "__main__":
    builder = MissionBuilder()

    # Create mission for 10 agents
    mission_xml = builder.create_benchmark_mission(num_agents=10)

    print("Mission XML generated:")
    print(mission_xml[:500])  # Print first 500 chars
    print(f"... (total length: {len(mission_xml)} characters)")
