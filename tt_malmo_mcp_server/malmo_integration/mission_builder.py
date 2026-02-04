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
        half_size = world_size // 2

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
            <!-- Flat superflat world for building -->
            <FlatWorldGenerator
                generatorString="3;minecraft:bedrock,2*minecraft:dirt,minecraft:grass;1;"
                forceReset="false"/>

            <DrawingDecorator>
                <!-- Clear flat building area -->
                <DrawCuboid x1="-{half_size}" y1="4" z1="-{half_size}" x2="{half_size}" y2="4" z2="{half_size}" type="grass"/>

                <!-- Stone foundation area in center -->
                <DrawCuboid x1="-50" y1="3" z1="-50" x2="50" y2="3" z2="50" type="stone"/>

                <!-- Resource stockpiles around the edges -->
                <!-- Wood stockpile -->
                <DrawCuboid x1="-60" y1="4" z1="-60" x2="-55" y2="10" z2="-55" type="oak_log"/>
                <!-- Stone stockpile -->
                <DrawCuboid x1="55" y1="4" z1="-60" x2="60" y2="10" z2="-55" type="cobblestone"/>
                <!-- Brick stockpile -->
                <DrawCuboid x1="-60" y1="4" z1="55" x2="-55" y2="10" z2="60" type="brick_block"/>
                <!-- Glass stockpile -->
                <DrawCuboid x1="55" y1="4" z1="55" x2="60" y2="8" z2="60" type="glass"/>

                <!-- Trees for wood -->
                <DrawTree x="-70" y="4" z="0" type="oak"/>
                <DrawTree x="70" y="4" z="0" type="oak"/>
                <DrawTree x="0" y="4" z="-70" type="oak"/>
                <DrawTree x="0" y="4" z="70" type="oak"/>

                <!-- Central marker (town square) -->
                <DrawBlock x="0" y="4" z="0" type="gold_block"/>
            </DrawingDecorator>

            <ServerQuitFromTimeUp timeLimitMs="{time_limit_ms}" description="{time_limit_hours} hour time limit"/>
        </ServerHandlers>
    </ServerSection>

'''

    def _create_builder_agent_section(self, agent_idx: int, total_agents: int,
                                      world_size: int) -> str:
        """Create agent section with building inventory and capabilities."""
        spawn_x, spawn_y, spawn_z = self._get_spawn_location(agent_idx, total_agents)

        # Give agents different colored wool to build with
        wool_colors = ["white", "orange", "light_blue", "lime", "pink", "gray"]
        wool_color = wool_colors[agent_idx % len(wool_colors)]

        return f'''    <AgentSection mode="Survival">
        <Name>Builder{agent_idx}</Name>

        <AgentStart>
            <Placement x="{spawn_x}" y="{spawn_y}" z="{spawn_z}" pitch="0" yaw="{agent_idx * 120}"/>
            <Inventory>
                <!-- Building tools -->
                <InventoryItem slot="0" type="diamond_pickaxe"/>
                <InventoryItem slot="1" type="diamond_axe"/>
                <InventoryItem slot="2" type="diamond_shovel"/>

                <!-- Primary building materials -->
                <InventoryItem slot="3" type="cobblestone" quantity="64"/>
                <InventoryItem slot="4" type="oak_planks" quantity="64"/>
                <InventoryItem slot="5" type="brick_block" quantity="64"/>
                <InventoryItem slot="6" type="glass" quantity="64"/>
                <InventoryItem slot="7" type="wool" variant="{wool_color}" quantity="64"/>
                <InventoryItem slot="8" type="torch" quantity="64"/>

                <!-- Additional materials in backpack -->
                <InventoryItem slot="9" type="oak_stairs" quantity="64"/>
                <InventoryItem slot="10" type="stone_slab" quantity="64"/>
                <InventoryItem slot="11" type="oak_door" quantity="16"/>
                <InventoryItem slot="12" type="ladder" quantity="64"/>
                <InventoryItem slot="13" type="fence" quantity="64"/>
                <InventoryItem slot="14" type="crafting_table" quantity="1"/>
            </Inventory>
        </AgentStart>

        <AgentHandlers>
            <!-- Observations -->
            <ObservationFromFullStats/>

            <ObservationFromNearbyEntities>
                <Range name="entities" xrange="30" yrange="15" zrange="30"/>
            </ObservationFromNearbyEntities>

            <ObservationFromGrid>
                <Grid name="surroundings">
                    <min x="-3" y="-1" z="-3"/>
                    <max x="3" y="3" z="3"/>
                </Grid>
            </ObservationFromGrid>

            <ObservationFromRay/>
            <ObservationFromChat/>

            <!-- Actions -->
            <ContinuousMovementCommands turnSpeedDegs="180"/>
            <DiscreteMovementCommands/>
            <InventoryCommands/>
            <ChatCommands/>
            <SimpleCraftCommands/>
            <PlaceCommands/>
            <MissionQuitCommands/>

            <!-- Video for agent vision -->
            <VideoProducer want_depth="true">
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
