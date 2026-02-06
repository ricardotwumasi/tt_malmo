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

    def create_city_building_mission(self, num_agents: int = 3,
                                     ms_per_tick: int = 50,
                                     include_spectator: bool = True,
                                     prioritise_offscreen: bool = False,
                                     world_size: int = 200,
                                     time_limit_hours: float = 4.0) -> str:
        """
        Generate mission XML optimized for city building benchmark.

        Args:
            num_agents: Number of builder agents (default 3)
            ms_per_tick: Milliseconds per game tick (lower = faster)
                        - 50 = normal speed (default)
                        - 25 = 2x speed
                        - 10 = 5x speed
                        - 5 = 10x speed
            include_spectator: Add a spectator agent for watching (default True)
            prioritise_offscreen: Reduce window updates for faster simulation
            world_size: Size of flat building area
            time_limit_hours: Mission time limit

        Returns:
            Complete mission XML string
        """
        xml = self._create_city_mission_header(ms_per_tick, prioritise_offscreen)
        xml += self._create_city_server_section(world_size, time_limit_hours)

        # Create builder agents
        for i in range(num_agents):
            xml += self._create_builder_agent_section(i, num_agents, world_size)

        # Add spectator agent if requested
        if include_spectator:
            xml += self._create_spectator_section(world_size)

        xml += self._create_mission_footer()

        return xml

    def _create_city_mission_header(self, ms_per_tick: int,
                                    prioritise_offscreen: bool) -> str:
        """Create mission header with speed settings."""
        offscreen_xml = ""
        if prioritise_offscreen:
            offscreen_xml = "\n        <PrioritiseOffscreenRendering>true</PrioritiseOffscreenRendering>"

        return f'''<?xml version="1.0" encoding="UTF-8" ?>
<Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <About>
        <Summary>City Building Benchmark - AI Agents Building a City</Summary>
    </About>

    <ModSettings>
        <MsPerTick>{ms_per_tick}</MsPerTick>{offscreen_xml}
    </ModSettings>

'''

    def _create_city_server_section(self, world_size: int,
                                    time_limit_hours: float) -> str:
        """Create server section for city building."""
        time_limit_ms = int(time_limit_hours * 3600 * 1000)

        resources_xml = self._generate_city_resources()

        return f'''    <ServerSection>
        <ServerInitialConditions>
            <Time>
                <StartTime>6000</StartTime>
                <AllowPassageOfTime>true</AllowPassageOfTime>
            </Time>
            <Weather>clear</Weather>
            <AllowSpawning>false</AllowSpawning>
        </ServerInitialConditions>

        <ServerHandlers>
            <!-- Flat superflat world for building.
                 Bottom layer is barrier (unbreakable even in Creative)
                 to prevent agents falling into void. -->
            <FlatWorldGenerator
                generatorString="3;minecraft:barrier,minecraft:bedrock,2*minecraft:dirt,minecraft:grass;1;"
                forceReset="true"/>

            <DrawingDecorator>
{resources_xml}
            </DrawingDecorator>

            <ServerQuitFromTimeUp timeLimitMs="{time_limit_ms}" description="{time_limit_hours} hour time limit"/>
        </ServerHandlers>
    </ServerSection>

'''

    def _generate_city_resources(self) -> str:
        """Generate a rich, resource-filled building area using only DrawBlock.

        Creates:
        - Stone plaza floor around center (11x11)
        - Gold center marker + glowstone boundary markers
        - Four material stockpiles at compass points (cobblestone, planks, brick, sandstone)
        - Ore deposits (iron, coal, diamond)
        - Wood supply (stacked logs)
        - Water feature (small pond)
        - Building plot corner markers
        - Torches for lighting
        """
        blocks = []

        # --- Central stone plaza (11x11, replaces grass at y=3) ---
        for x in range(-5, 6):
            for z in range(-5, 6):
                blocks.append(f'<DrawBlock x="{x}" y="3" z="{z}" type="stone"/>')

        # Gold center marker on top of plaza
        blocks.append('<DrawBlock x="0" y="4" z="0" type="gold_block"/>')

        # --- Boundary markers (glowstone at 40-block radius) ---
        for x, z in [(-40, -40), (40, -40), (-40, 40), (40, 40),
                      (-40, 0), (40, 0), (0, -40), (0, 40)]:
            blocks.append(f'<DrawBlock x="{x}" y="4" z="{z}" type="glowstone"/>')

        # --- Material stockpile: COBBLESTONE (north, z=-20) ---
        for x in range(-2, 3):
            for z in range(-22, -18):
                for y in [4, 5]:
                    blocks.append(f'<DrawBlock x="{x}" y="{y}" z="{z}" type="cobblestone"/>')

        # --- Material stockpile: PLANKS (east, x=20) ---
        for x in range(18, 22):
            for z in range(-2, 3):
                for y in [4, 5]:
                    blocks.append(f'<DrawBlock x="{x}" y="{y}" z="{z}" type="planks"/>')

        # --- Material stockpile: BRICK (south, z=20) ---
        for x in range(-2, 3):
            for z in range(18, 22):
                for y in [4, 5]:
                    blocks.append(f'<DrawBlock x="{x}" y="{y}" z="{z}" type="brick_block"/>')

        # --- Material stockpile: SANDSTONE (west, x=-20) ---
        for x in range(-22, -18):
            for z in range(-2, 3):
                for y in [4, 5]:
                    blocks.append(f'<DrawBlock x="{x}" y="{y}" z="{z}" type="sandstone"/>')

        # --- Iron ore deposit (NW corner) ---
        for x in range(-32, -28):
            for z in range(-32, -28):
                blocks.append(f'<DrawBlock x="{x}" y="3" z="{z}" type="iron_ore"/>')

        # --- Coal ore deposit (NE corner) ---
        for x in range(28, 32):
            for z in range(-32, -28):
                blocks.append(f'<DrawBlock x="{x}" y="3" z="{z}" type="coal_ore"/>')

        # --- Diamond ore (rare, SE corner) ---
        for x in range(28, 30):
            for z in range(28, 30):
                blocks.append(f'<DrawBlock x="{x}" y="3" z="{z}" type="diamond_ore"/>')

        # --- Wood supply: stacked logs (NW, near iron) ---
        for x in range(-15, -10):
            for y in [4, 5, 6]:
                blocks.append(f'<DrawBlock x="{x}" y="{y}" z="-15" type="log"/>')

        # --- Wood supply: second stack (NE) ---
        for x in range(10, 15):
            for y in [4, 5, 6]:
                blocks.append(f'<DrawBlock x="{x}" y="{y}" z="-15" type="log"/>')

        # --- Water feature: small pond (SE quadrant) ---
        for x in range(10, 15):
            for z in range(10, 15):
                blocks.append(f'<DrawBlock x="{x}" y="3" z="{z}" type="water"/>')

        # --- Building plot markers (sandstone corners showing 8x8 plots) ---
        plots = [(-15, -10), (8, -10), (-15, 8), (-35, -10), (25, -10)]
        for px, pz in plots:
            for dx, dz in [(0, 0), (7, 0), (0, 7), (7, 7)]:
                blocks.append(f'<DrawBlock x="{px+dx}" y="4" z="{pz+dz}" type="sandstone"/>')

        # --- Torch lighting around the plaza and stockpiles ---
        torch_positions = [
            (-6, -6), (6, -6), (-6, 6), (6, 6),          # plaza corners
            (0, -23), (0, 23), (-23, 0), (23, 0),         # stockpile markers
            (-20, -20), (20, -20), (-20, 20), (20, 20),   # midpoints
        ]
        for tx, tz in torch_positions:
            blocks.append(f'<DrawBlock x="{tx}" y="4" z="{tz}" type="torch"/>')

        # --- Extra glass and wool for decoration ---
        for x in range(-2, 3):
            blocks.append(f'<DrawBlock x="{x}" y="4" z="25" type="glass"/>')
        for z in range(-2, 3):
            blocks.append(f'<DrawBlock x="-25" y="4" z="{z}" type="wool"/>')

        indent = '                '
        return '\n'.join(f'{indent}{b}' for b in blocks)

    def _create_builder_agent_section(self, agent_idx: int, total_agents: int,
                                      world_size: int) -> str:
        """Create agent section with building inventory and capabilities."""
        spawn_x, spawn_y, spawn_z = self._get_spawn_location(agent_idx, total_agents)

        # Give agents different colored wool to build with
        wool_colors = ["white", "orange", "light_blue", "lime", "pink", "gray"]
        wool_color = wool_colors[agent_idx % len(wool_colors)]

        return f'''    <AgentSection mode="Creative">
        <Name>Builder{agent_idx}</Name>

        <AgentStart>
            <Placement x="{spawn_x}" y="{spawn_y}" z="{spawn_z}" pitch="0" yaw="{agent_idx * 120}"/>
            <Inventory>
                <InventoryBlock quantity="1" slot="0" type="diamond_pickaxe"/>
                <InventoryBlock quantity="1" slot="1" type="diamond_axe"/>
                <InventoryBlock quantity="64" slot="2" type="cobblestone"/>
                <InventoryBlock quantity="64" slot="3" type="planks"/>
                <InventoryBlock quantity="64" slot="4" type="brick_block"/>
                <InventoryBlock quantity="64" slot="5" type="glass"/>
                <InventoryBlock quantity="64" slot="6" type="torch"/>
            </Inventory>
        </AgentStart>

        <AgentHandlers>
            <ObservationFromFullStats/>
            <ObservationFromFullInventory/>
            <ObservationFromGrid>
                <Grid name="surroundings">
                    <min x="-3" y="-1" z="-3"/>
                    <max x="3" y="3" z="3"/>
                </Grid>
            </ObservationFromGrid>
            <ContinuousMovementCommands turnSpeedDegs="180"/>
            <InventoryCommands/>
            <MissionQuitCommands/>
            <VideoProducer want_depth="false">
                <Width>320</Width>
                <Height>240</Height>
            </VideoProducer>
        </AgentHandlers>
    </AgentSection>

'''

    def _create_spectator_section(self, world_size: int) -> str:
        """Create spectator agent section for watching the builders."""
        return f'''    <AgentSection mode="Spectator">
        <Name>Spectator</Name>

        <AgentStart>
            <!-- Start above the building area with good view -->
            <Placement x="0" y="50" z="-80" pitch="30" yaw="0"/>
        </AgentStart>

        <AgentHandlers>
            <!-- Observations -->
            <ObservationFromFullStats/>

            <ObservationFromNearbyEntities>
                <Range name="entities" xrange="100" yrange="50" zrange="100"/>
            </ObservationFromNearbyEntities>

            <ObservationFromChat/>

            <!-- Spectator movement -->
            <ContinuousMovementCommands turnSpeedDegs="180"/>

            <!-- High-res video for watching -->
            <VideoProducer want_depth="false">
                <Width>640</Width>
                <Height>480</Height>
            </VideoProducer>
        </AgentHandlers>
    </AgentSection>

'''

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
                forceReset="true"/>

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

        # Place marker blocks for resource areas (DrawBlock only)
        # DrawCuboid/DrawTree cause Minecraft state issues after multiple mission cycles
        resources += '''
                <DrawBlock x="-40" y="4" z="-40" type="oak_log"/>
                <DrawBlock x="-20" y="4" z="-40" type="oak_log"/>
                <DrawBlock x="0" y="4" z="-40" type="oak_log"/>
                <DrawBlock x="20" y="4" z="-40" type="oak_log"/>
                <DrawBlock x="-30" y="4" z="-30" type="iron_ore"/>
                <DrawBlock x="25" y="4" z="25" type="coal_ore"/>'''

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
                <InventoryBlock quantity="1" slot="0" type="wooden_pickaxe"/>
                <InventoryBlock quantity="1" slot="1" type="wooden_axe"/>
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
        # Spawn in circle with radius 10 blocks
        radius = 10.0
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
