"""
Cognitive Controller - The bottleneck component of PIANO architecture.

This is the critical component that prevents agent incoherence by:
1. Filtering information from all 10 concurrent modules through a bottleneck
2. Using LLM reasoning over the filtered information
3. Making high-level decisions
4. Broadcasting decisions to downstream modules

This architecture mirrors the brain's information processing bottleneck.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from .agent_state import AgentState


class CognitiveController:
    """
    Cognitive Controller - Central decision-making bottleneck.

    This component receives inputs from all PIANO modules and synthesizes
    them into coherent high-level decisions.
    """

    def __init__(self, llm_adapter, decision_interval: float = 5.0):
        """
        Initialize Cognitive Controller.

        Args:
            llm_adapter: LLM adapter for reasoning (Claude or Gemini)
            decision_interval: Time between decisions in seconds
        """
        self.llm = llm_adapter
        self.decision_interval = decision_interval
        self.last_decision_time = None

        # Bottleneck parameters
        self.max_context_items = 10  # Maximum items to pass through bottleneck
        self.relevance_threshold = 0.3  # Minimum relevance score

    async def make_decision(self, agent_state: AgentState) -> Dict[str, Any]:
        """
        Synthesize information through bottleneck and make high-level decision.

        This is the core PIANO bottleneck operation:
        1. Extract relevant info from Agent State (bottleneck input)
        2. LLM reasoning over filtered information
        3. Generate high-level decision
        4. Broadcast to downstream modules

        Args:
            agent_state: Current agent state

        Returns:
            Decision dictionary with action and reasoning
        """
        # Apply bottleneck filter
        relevant_info = self._apply_bottleneck(agent_state)

        # Construct decision prompt
        prompt = self._construct_decision_prompt(relevant_info, agent_state)

        # LLM reasoning
        decision_text = await self.llm.generate(prompt)

        # Parse decision
        decision = self._parse_decision(decision_text, agent_state)

        # Update agent state with bottleneck decision
        agent_state.set_bottleneck_decision(decision)

        self.last_decision_time = datetime.now()

        return decision

    def _apply_bottleneck(self, agent_state: AgentState) -> Dict[str, Any]:
        """
        Apply information bottleneck filter.

        This selects the most relevant information from all module outputs
        to pass through the bottleneck. This prevents information overload
        and maintains coherence.

        Args:
            agent_state: Current agent state

        Returns:
            Filtered information dictionary
        """
        filtered_info = {
            'agent_identity': {
                'name': agent_state.name,
                'traits': agent_state.traits,
                'role': agent_state.role
            },
            'current_state': {
                'location': agent_state.current_location,
                'health': agent_state.current_health,
                'hunger': agent_state.current_hunger,
                'inventory_items': len(agent_state.current_inventory)
            },
            'recent_memory': [],
            'nearby_agents': [],
            'current_goals': agent_state.current_goals[-3:] if agent_state.current_goals else [],
            'module_insights': {}
        }

        # Extract recent working memory (most important recent events)
        if agent_state.working_memory:
            filtered_info['recent_memory'] = agent_state.working_memory[-3:]

        # Extract nearby agents info (social context)
        if agent_state.nearby_agents:
            filtered_info['nearby_agents'] = [
                {
                    'name': agent.get('name', 'Unknown'),
                    'distance': agent.get('distance', 'unknown')
                }
                for agent in agent_state.nearby_agents[:5]  # Max 5 nearby agents
            ]

        # Extract key insights from module outputs
        # Each module can contribute ONE key insight through the bottleneck
        for module_name in ['perception', 'social_awareness', 'goal_generation',
                            'action_awareness', 'memory_consolidation']:
            module_output = agent_state.get_module_output(module_name)
            if module_output:
                filtered_info['module_insights'][module_name] = self._extract_key_insight(
                    module_output, module_name
                )

        return filtered_info

    def _extract_key_insight(self, module_output: Dict[str, Any], module_name: str) -> str:
        """
        Extract the single most important insight from a module.

        Args:
            module_output: Full module output
            module_name: Name of the module

        Returns:
            Key insight as string
        """
        output = module_output.get('output', {})

        if module_name == 'perception':
            # Key insight: What's most salient in the environment?
            return output.get('salient_feature', 'Nothing notable detected')

        elif module_name == 'social_awareness':
            # Key insight: What's the social situation?
            return output.get('social_summary', 'No social interactions')

        elif module_name == 'goal_generation':
            # Key insight: What's the most important goal?
            goals = output.get('proposed_goals', [])
            return goals[0] if goals else 'No active goals'

        elif module_name == 'action_awareness':
            # Key insight: Did last action succeed?
            status = output.get('status', 'unknown')
            return f"Last action: {status}"

        elif module_name == 'memory_consolidation':
            # Key insight: What's the most important memory?
            return output.get('key_memory', 'No significant memories')

        return "No insight available"

    # Valid actions the LLM can choose from. Maps action name -> Malmo command.
    ACTION_MENU = {
        'move_forward':   'move 1',
        'turn_left':      'turn -1',
        'turn_right':     'turn 1',
        'place_block':    'use 1',
        'mine_block':     'attack 1',
        'jump_forward':   'jump 1',
        'select_slot_3':  'hotbar.3 1',   # cobblestone
        'select_slot_4':  'hotbar.4 1',   # wood planks
        'select_slot_5':  'hotbar.5 1',   # brick blocks
        'select_slot_6':  'hotbar.6 1',   # glass
        'select_slot_7':  'hotbar.7 1',   # torches
        'look_around':    'turn 1',
        'wait':           'move 0',
    }

    # Reference to agent_manager for cross-agent awareness (set externally)
    _agent_manager = None

    @classmethod
    def set_agent_manager(cls, agent_manager):
        """Allow the cognitive controller to read other agents' states."""
        cls._agent_manager = agent_manager

    def _construct_decision_prompt(self, relevant_info: Dict[str, Any],
                                   agent_state: AgentState) -> str:
        """
        Construct the LLM prompt with a constrained action menu.

        Includes last action context so the LLM knows to progress through
        the build cycle (select → place → move → turn → place → ...).
        Also includes other agents' positions for coordination.
        """
        goals_text = self._format_goals(relevant_info['current_goals'])
        loc = relevant_info['current_state']['location']

        # Last action context — critical so the LLM doesn't repeat itself
        last = agent_state.last_action or {}
        last_action_name = last.get('action', 'none')
        last_action_text = f"Your last action was: {last_action_name}"

        # Other agents' positions and last actions for coordination
        other_agents_text = self._format_other_agents(agent_state)

        prompt = f"""You are {relevant_info['agent_identity']['name']} building in Minecraft Creative mode.
Location: {loc}. {last_action_text}
{other_agents_text}

Actions: move_forward, turn_left, turn_right, place_block, mine_block, jump_forward, select_slot_3 (cobblestone), select_slot_4 (wood planks), select_slot_5 (brick), select_slot_6 (glass), select_slot_7 (torch), look_around, wait

RULES:
- You are ALREADY at the build site. Do NOT explore or look for a location.
- Follow this cycle: select_slot → place_block → turn or move → place_block → repeat
- If your last action was select_slot_*, your next MUST be place_block
- If your last action was place_block, move_forward or turn to reposition, then place_block again
- NEVER pick move_forward more than twice in a row

ACTION: <name>
REASONING: <short>
"""
        return prompt

    def _format_other_agents(self, agent_state: AgentState) -> str:
        """Format other agents' positions and last actions for coordination."""
        if not self._agent_manager:
            return "Other agents: unknown"

        others = []
        for aid, state in self._agent_manager.agent_states.items():
            if aid == agent_state.agent_id:
                continue
            loc = state.current_location or {}
            x = loc.get('x', 0)
            z = loc.get('z', 0)
            last = state.last_action or {}
            last_act = last.get('action', '?')
            others.append(f"{state.name} at ({x:.0f},{z:.0f}) doing {last_act}")

        if not others:
            return "Other agents: none nearby"
        return "Other agents: " + "; ".join(others)

    def _format_nearby_agents(self, nearby_agents: List[Dict[str, Any]]) -> str:
        """Format nearby agents for prompt."""
        if not nearby_agents:
            return "No agents nearby"
        return "\n".join([f"- {a['name']} (distance: {a['distance']})"
                         for a in nearby_agents])

    def _format_recent_memory(self, recent_memory: List[Dict[str, Any]]) -> str:
        """Format recent memory for prompt."""
        if not recent_memory:
            return "No recent memories"
        return "\n".join([f"- {m.get('event', 'Unknown event')}"
                         for m in recent_memory])

    def _format_goals(self, goals: List[Dict[str, Any]]) -> str:
        """Format goals for prompt."""
        if not goals:
            return "No active goals"
        return "\n".join([f"- {g.get('description', 'Unknown goal')}"
                         for g in goals])

    def _format_module_insights(self, insights: Dict[str, str]) -> str:
        """Format module insights for prompt."""
        if not insights:
            return "No module insights available"
        return "\n".join([f"- {module}: {insight}"
                         for module, insight in insights.items()])

    def _parse_decision(self, decision_text: str, agent_state: AgentState) -> Dict[str, Any]:
        """
        Parse LLM decision output, matching against the ACTION_MENU.

        Strips the action text and looks for an exact match in ACTION_MENU keys.
        If no match, defaults to 'move_forward' and logs a warning.
        """
        lines = decision_text.strip().split('\n')

        raw_action = ""
        reasoning = ""

        for line in lines:
            line = line.strip()
            if line.upper().startswith('ACTION:'):
                raw_action = line.split(':', 1)[1].strip()
            elif line.upper().startswith('REASONING:'):
                reasoning = line.split(':', 1)[1].strip()

        # Normalize: lowercase, strip quotes/backticks/whitespace
        action_key = raw_action.lower().strip(' `"\'')

        if action_key not in self.ACTION_MENU:
            print(f"  [WARN] LLM returned unknown action '{raw_action}', defaulting to move_forward")
            action_key = 'move_forward'

        decision = {
            'action': action_key,
            'reasoning': reasoning,
            'timestamp': datetime.now().isoformat(),
            'agent_id': agent_state.agent_id
        }

        return decision

    async def run_decision_loop(self, agent_state: AgentState):
        """
        Run continuous decision-making loop.

        Args:
            agent_state: Agent state to monitor
        """
        while True:
            try:
                decision = await self.make_decision(agent_state)
                print(f"[{agent_state.name}] Decision: {decision['action']} - {decision['reasoning']}")

                # Wait for next decision interval
                await asyncio.sleep(self.decision_interval)

            except Exception as e:
                print(f"Error in decision loop: {e}")
                await asyncio.sleep(1.0)  # Brief pause before retry
