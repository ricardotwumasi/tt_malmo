"""
Environment Manager - Connects agents to Malmo/Minecraft.

This bridges the PIANO architecture with the Malmo environment,
enabling agents to observe and act in Minecraft.
"""

import malmoenv
from malmoenv.core import StringActionSpace
import asyncio
import math
import socket
import threading
from typing import Dict, Any, Optional
import numpy as np


class MalmoEnvironmentManager:
    """
    Manages connection between agents and Malmo environment.

    Handles:
    - Connecting to Malmo on specified port
    - Sending observations to agents
    - Receiving actions from agents
    - Executing actions in Minecraft

    Multi-agent protocol (MalmoEnv):
    - All agents share the same base port (role 0's port) for coordination
    - Each agent connects to its own port: base_port + role
    - Each agent needs its own Minecraft client instance
    - Role 0 starts the mission; other roles join via _find_server()
    """

    def __init__(self, mission_xml: str, port: int = 9000, role: int = 0,
                 exp_uid: str = "default_experiment"):
        """
        Initialize Environment Manager.

        Args:
            mission_xml: Mission XML string
            port: Base Malmo port (role 0's coordination port)
            role: Agent role index (0 = mission starter, 1+ = joiners)
            exp_uid: Shared experiment ID so all agents join the same mission
        """
        self.mission_xml = mission_xml
        self.port = port
        self.role = role
        self.exp_uid = exp_uid
        self.env = None
        self.running = False
        self._thread = None
        self._reset_complete = threading.Event()
        self._barrier = None  # Shared barrier for multi-agent sync

    def set_barrier(self, barrier: threading.Barrier):
        """
        Set a shared barrier for multi-agent synchronization.

        All agents wait at this barrier after reset() before stepping.
        This prevents MalmoEnv's done-flag issue where sequential resets
        cause role 0's peek to report done=1 before other roles join.

        Args:
            barrier: threading.Barrier shared across all agents in a mission
        """
        self._barrier = barrier

    @staticmethod
    def cleanup_ports(ports, wait_seconds=10):
        """
        Clean stale sessions on Minecraft ports before starting a mission.

        Sends Close and Quit messages to clear any leftover state.

        Args:
            ports: List of port numbers to clean
            wait_seconds: Seconds to wait after cleanup for Minecraft to stabilize
        """
        from malmoenv import comms
        from malmoenv.version import malmo_version
        import time

        print(f"[CLEANUP] Clearing stale sessions on ports {ports}...")
        for port in ports:
            for msg in ["<Quit/>", "<Close>c:0:0</Close>"]:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(5)
                    s.connect(('127.0.0.1', port))
                    comms.send_message(s, ("<MalmoEnv" + malmo_version + "/>").encode())
                    comms.send_message(s, msg.encode())
                    comms.recv_message(s)
                    s.close()
                except Exception:
                    pass
        print(f"[CLEANUP] Waiting {wait_seconds}s for Minecraft to stabilize...")
        time.sleep(wait_seconds)
        print(f"[CLEANUP] Done.")

    def connect(self):
        """Connect to Malmo environment."""
        agent_port = self.port + self.role
        print(f"Connecting to Malmo on port {agent_port} (role={self.role}, base_port={self.port})...")

        # Create MalmoEnv environment
        self.env = malmoenv.make()

        # Initialize with mission XML, using StringActionSpace for string commands
        # - port: coordination port (role 0's port) used by all agents
        # - server2: address of this agent's Minecraft instance
        # - port2: this agent's actual connection port (base_port + role)
        # - role: this agent's role index (0 starts mission, others join)
        # - exp_uid: shared experiment ID for mission coordination
        self.env.init(
            self.mission_xml,
            self.port,
            server='127.0.0.1',
            server2='127.0.0.1',
            port2=agent_port,
            role=self.role,
            exp_uid=self.exp_uid,
            action_space=StringActionSpace()  # Allows string commands like "move 1"
        )

        print(f"[OK] Initialized Malmo env (role={self.role}, port={agent_port})")
        return True

    def reset(self) -> Dict[str, Any]:
        """
        Reset environment and get initial observation.

        Returns:
            Initial observation dictionary
        """
        if not self.env:
            raise RuntimeError("Environment not connected. Call connect() first.")

        print("Resetting Malmo environment...")
        obs = self.env.reset()

        # Convert observation to dictionary format
        return self._process_observation(obs)

    def step(self, action: str) -> tuple[Dict[str, Any], float, bool]:
        """
        Execute action in Malmo and get result.

        Includes transient error handling: socket timeouts, connection resets,
        and other network errors are retried up to 3 times before raising.

        Args:
            action: Action string (e.g., "move 1", "turn 1", "attack 1")

        Returns:
            (observation, reward, done) tuple
        """
        import time as _time

        if not self.env:
            raise RuntimeError("Environment not connected.")

        # Retry transient network errors (socket timeouts, connection resets)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                obs, reward, done, info = self.env.step(action)
                break  # success
            except (socket.timeout, ConnectionResetError, ConnectionAbortedError,
                    BrokenPipeError, OSError) as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    print(f"  [RETRY] Transient error in step(): {e} — retrying in {wait}s ({attempt+1}/{max_retries})")
                    _time.sleep(wait)
                else:
                    print(f"  [FAIL] step() failed after {max_retries} retries: {e}")
                    raise

        # Coerce done to bool (MalmoEnv may return int 0/1 or string)
        done = bool(int(done)) if done is not None else False

        # Process observation — info is a JSON string from ObservationFromFullStats
        processed_obs = self._process_observation(obs, info)

        # If info was empty (transient gap), use last known good observation
        # instead of returning defaults. This prevents the agent from thinking
        # it's at (0,0,4,0) with no inventory during brief network hiccups.
        if processed_obs.get('_info_empty') and hasattr(self, '_last_good_obs'):
            # Keep pixel data from current step but position/inventory from last good
            good = dict(self._last_good_obs)
            if 'pixels' in processed_obs:
                good['pixels'] = processed_obs['pixels']
                good['shape'] = processed_obs.get('shape')
                good['mean_pixel'] = processed_obs.get('mean_pixel')
            processed_obs = good
        elif not processed_obs.get('_info_empty'):
            # Save as last known good observation (without pixel data to save memory)
            save = {k: v for k, v in processed_obs.items() if k != 'pixels'}
            self._last_good_obs = save

        # Malmo may return None for reward
        if reward is None:
            reward = 0.0

        return processed_obs, reward, done

    def _process_observation(self, obs, info=None) -> Dict[str, Any]:
        """
        Process raw Malmo observation into structured format.

        Args:
            obs: Raw observation from MalmoEnv (pixel array from VideoProducer)
            info: JSON string from ObservationFromFullStats (contains XPos, YPos, etc.)

        Returns:
            Structured observation dictionary
        """
        import json

        observation = {}
        info_parsed = False

        # Parse real observation data from MalmoEnv info string.
        # MalmoEnv returns info as a raw JSON string containing
        # ObservationFromFullStats fields (XPos, YPos, ZPos, Life, etc.)
        if info and isinstance(info, str):
            try:
                parsed = json.loads(info)
                if isinstance(parsed, dict) and len(parsed) > 0:
                    observation.update(parsed)
                    info_parsed = True
            except (json.JSONDecodeError, ValueError):
                pass

        # Add pixel data if available
        if isinstance(obs, np.ndarray):
            observation['type'] = 'video'
            observation['pixels'] = obs
            observation['shape'] = obs.shape
            observation['mean_pixel'] = float(np.mean(obs))

        # Parse inventory from ObservationFromFullInventory format.
        # Malmo provides flat keys like InventorySlot_0_item, InventorySlot_0_size, etc.
        if 'inventory' not in observation or not observation['inventory']:
            inventory = []
            for i in range(41):
                item_key = f'InventorySlot_{i}_item'
                if item_key in observation:
                    inventory.append({
                        'slot': i,
                        'item': observation[item_key],
                        'quantity': observation.get(f'InventorySlot_{i}_size', 1),
                    })
            if inventory:
                observation['inventory'] = inventory

        # Defaults for any fields not provided by Malmo
        observation.setdefault('XPos', 0.0)
        observation.setdefault('YPos', 4.0)
        observation.setdefault('ZPos', 0.0)
        observation.setdefault('Life', 20.0)
        observation.setdefault('Food', 20.0)
        observation.setdefault('inventory', [])
        observation.setdefault('entities', [])

        # Flag whether we got real data from info (used by step() to decide
        # whether to fall back to last known good observation)
        observation['_info_empty'] = not info_parsed

        return observation

    def close(self):
        """Close Malmo connection. Idempotent — safe to call multiple times."""
        if self.env:
            print(f"Closing Malmo environment (role={self.role})...")
            try:
                self.env.close()
            except Exception as e:
                print(f"[WARN] Error during env.close(): {e}")
            self.env = None
            self.running = False
            print(f"[OK] Malmo connection closed (role={self.role})")

    # --- Navigation helpers: keep agents within the building area ---

    BUILDING_RADIUS = 50  # blocks from origin

    def _needs_return_to_center(self, obs) -> bool:
        """Check if agent has wandered too far from the building area."""
        x = obs.get('XPos', 0.0)
        z = obs.get('ZPos', 0.0)
        return math.sqrt(x * x + z * z) > self.BUILDING_RADIUS

    def _is_underground(self, obs) -> bool:
        """Check if agent is below ground level (y < 3 on superflat)."""
        return obs.get('YPos', 4.0) < 3.0

    def _ensure_level_pitch(self, obs) -> Dict[str, Any]:
        """Actively correct pitch angle to level (0 degrees).

        MalmoEnv's 'pitch 0' only stops rotation speed — it does NOT set the
        angle to 0. This method reads the current Pitch from observations and
        applies corrective rotation for a calculated number of ticks, then
        stops rotation.

        Args:
            obs: Current observation dict (must contain 'Pitch')

        Returns:
            Updated observation from the last corrective step
        """
        pitch = obs.get('Pitch', 0.0)

        # Tolerance: don't correct if close enough to level
        if abs(pitch) <= 5.0:
            return obs

        # pitch > 0 means looking down → need negative pitch speed to look up
        # pitch < 0 means looking up → need positive pitch speed to look down
        # At turnSpeedDegs=180, pitch 1.0 = 180 deg/sec.
        # At 2x speed (25ms/tick), each tick rotates ~4.5 degrees.
        # We use pitch speed ±0.5 for gentler correction (~2.25 deg/tick).
        correction_speed = -0.5 if pitch > 0 else 0.5
        deg_per_tick = abs(correction_speed) * 180.0 * 0.025  # at 2x speed
        ticks_needed = int(abs(pitch) / deg_per_tick) + 1
        ticks_needed = min(ticks_needed, 40)  # safety cap

        for _ in range(ticks_needed):
            obs, _, done = self.step(f'pitch {correction_speed}')
            if done or not self.running:
                break
        # Stop pitch rotation
        self.step('pitch 0')
        return obs

    def _execute_return_step(self, obs) -> tuple:
        """Execute a single return-to-center step with proportional turning.

        Instead of using the normal multi-tick path (which overshoots with
        full-speed turns), this method handles turning and moving directly
        with carefully sized commands:
        - Proportional turn amount based on yaw error (no overshoot)
        - Only 3 ticks per turn/move (not 10)
        - Jump if underground

        Returns:
            (obs, reward, done) from the final step command
        """
        NAV_TICKS = 3  # fewer ticks to avoid overshoot

        x = obs.get('XPos', 0.0)
        z = obs.get('ZPos', 0.0)
        yaw = obs.get('Yaw', 0.0)

        # If underground, jump first
        if self._is_underground(obs):
            for _ in range(5):
                obs, reward, done = self.step('jump 1')
                if done or not self.running:
                    return obs, reward, done
            obs, reward, done = self.step('jump 0')
            return obs, reward, done

        # Calculate desired yaw toward origin
        dx = -x
        dz = -z
        desired_yaw = math.degrees(math.atan2(-dx, dz))
        yaw_diff = (desired_yaw - yaw + 180) % 360 - 180

        if abs(yaw_diff) > 15:
            # Proportional turn: scale turn speed by yaw error.
            # At turnSpeedDegs=180, turn 1.0 = 180 deg/sec.
            # Each tick at 2x speed = 25ms, so 3 ticks = 75ms.
            # turn 1.0 for 75ms = ~13.5 degrees.
            # We want to turn by roughly yaw_diff degrees.
            # turn_amount = yaw_diff / (180 * 0.075) but clamped to [-1, 1].
            turn_amount = yaw_diff / 60.0  # tuned: 60° error → full speed
            turn_amount = max(-1.0, min(1.0, turn_amount))
            cmd = f'turn {turn_amount:.2f}'
            for _ in range(NAV_TICKS):
                obs, reward, done = self.step(cmd)
                if done or not self.running:
                    return obs, reward, done
            # Stop turning
            obs, reward, done = self.step('turn 0')
            return obs, reward, done
        else:
            # Roughly aligned — move forward
            for _ in range(NAV_TICKS):
                obs, reward, done = self.step('move 1')
                if done or not self.running:
                    return obs, reward, done
            obs, reward, done = self.step('move 0')
            return obs, reward, done

    def _run_agent_loop_blocking(self, agent_state, agent_manager, agent_id: str,
                                 max_steps: int = 1000):
        """
        Run the agent control loop in a dedicated thread.

        MalmoEnv's reset() and step() are blocking network calls that must
        run in a real thread (not asyncio), since they do socket I/O that
        would block the event loop.

        Args:
            agent_state: Agent's state object
            agent_manager: Agent manager instance
            agent_id: Agent ID
            max_steps: Maximum steps to run
        """
        import time

        print(f"\n{'='*60}")
        print(f"[GAME] Starting agent control loop for {agent_state.name} (role={self.role})")
        print(f"{'='*60}\n")

        self.running = True
        step_count = 0
        exit_reason = "UNKNOWN"

        try:
            # Reset environment and get initial observation
            # This is the blocking call that starts the mission for role 0
            # or joins the mission for roles 1+
            print(f"  [{agent_state.name}] Calling reset() (this may take a while)...")
            obs = self.reset()

            # Signal that reset is complete
            self._reset_complete.set()

            # Multi-agent sync: wait for ALL agents to finish resetting
            # before any agent starts stepping. This prevents MalmoEnv's
            # done-flag issue where peek reports done=1 prematurely.
            if self._barrier:
                print(f"  [{agent_state.name}] Waiting at barrier for other agents...")
                try:
                    self._barrier.wait(timeout=120)
                except threading.BrokenBarrierError:
                    print(f"  [{agent_state.name}] Barrier broken - other agent failed")
                    raise RuntimeError("Multi-agent barrier broken")

            # Force done=False after barrier - the multi-agent peek sometimes
            # sets done=True prematurely during reset negotiation
            if self.env:
                self.env.done = False

            # reset() only returns pixels, no info JSON. Do a no-op step to
            # get the first real observation with position/inventory data.
            obs, _, _ = self.step('move 0')
            agent_state.update_observation(obs)

            print(f"  [{agent_state.name}] Step {step_count}: Initial observation received")
            print(f"    Location: ({obs.get('XPos', 0):.1f}, {obs.get('YPos', 0):.1f}, {obs.get('ZPos', 0):.1f})")
            print(f"    Health: {obs.get('Life', 20):.1f}/20")
            print(f"    Inventory: {len(obs.get('inventory', []))} slots")
            print()

            # Continuous movement commands need multiple game ticks to produce
            # displacement. We execute each command for TICKS_PER_ACTION ticks,
            # then stop movement before reading the final observation.
            MOVEMENT_TICKS = 5    # ~250ms at 50ms/tick, ~125ms at 2x speed
            ACTION_TICKS = 3      # brief pause for place/craft to register

            # Hotbar slots for building materials (mission XML inventory):
            #   hotbar 1 = diamond_pickaxe, 2 = diamond_axe,
            #   3 = cobblestone, 4 = planks, 5 = brick_block,
            #   6 = glass, 7 = torch
            BUILDING_SLOTS = [3, 4, 5, 6]  # cycle through building materials
            PICKAXE_SLOT = 1

            # Stuck detection: track recent positions
            import random
            recent_positions = []   # list of (x, z) tuples
            STUCK_THRESHOLD = 15    # steps with same position → stuck
            consecutive_empty = 0   # consecutive steps with empty info
            EMPTY_THRESHOLD = 100   # only reconnect after many empty steps

            # Track last executed decision to avoid re-executing one-shot
            # actions (hotbar, place, mine) while waiting for the next LLM
            # decision. Movement actions (move, turn, jump) CAN repeat
            # but are capped to prevent overshooting the building area.
            last_executed_ts = None
            movement_repeat_count = 0
            MAX_MOVEMENT_REPEATS = 6  # ~6 steps per decision, ~12 blocks
            _REPEATABLE_CMDS = {'move 1', 'move -1', 'turn -1', 'turn 1', 'jump 1'}

            while self.running and step_count < max_steps:
                # Brief sleep to let PIANO architecture produce a decision
                time.sleep(0.2)

                # Get decision from Cognitive Controller
                decision = agent_state.bottleneck_decision

                if decision:
                    action_type = decision.get('action', 'explore')
                    reasoning = decision.get('reasoning', 'No reasoning')

                    # --- DETECT DEATH (Life <= 0) → auto-respawn ---
                    last_obs = agent_state.current_observation or {}
                    agent_life = last_obs.get('Life', 20.0)

                    if agent_life <= 0 and step_count > 5:
                        print(f"  [{agent_state.name}] Step {step_count + 1}:")
                        print(f"    [DEATH] Agent died! Life={agent_life:.1f}")
                        print(f"    [RESPAWN] Attempting reset()...")

                        try:
                            obs = self.reset()
                            if self.env:
                                self.env.done = False
                            # Get real observation after reset
                            obs, _, _ = self.step('move 0')
                            agent_state.update_observation(obs)
                            recent_positions.clear()
                            consecutive_empty = 0
                            print(f"    [OK] Respawned at ({obs.get('XPos', 0):.1f}, {obs.get('YPos', 0):.1f}, {obs.get('ZPos', 0):.1f})")
                            print(f"    Life: {obs.get('Life', 0):.1f}/20  Inventory: {len(obs.get('inventory', []))} slots")
                        except Exception as e:
                            print(f"    [FAIL] Respawn failed: {e}")
                            time.sleep(5)

                        step_count += 1
                        continue

                    # --- TRACK EMPTY OBSERVATIONS ---
                    # step() preserves last known good obs during transient gaps.
                    # Only track prolonged disconnection.
                    is_default = (
                        abs(last_obs.get('XPos', 0.0)) < 0.01
                        and abs(last_obs.get('ZPos', 0.0)) < 0.01
                        and len(last_obs.get('inventory', [])) == 0
                    )

                    if is_default:
                        consecutive_empty += 1
                        if consecutive_empty == 20:
                            print(f"  [{agent_state.name}] [WARN] {consecutive_empty} consecutive empty observations — riding through")
                        if consecutive_empty >= EMPTY_THRESHOLD:
                            print(f"  [{agent_state.name}] [FAIL] {EMPTY_THRESHOLD} consecutive empty obs — agent likely disconnected. Stopping.")
                            break
                    else:
                        if consecutive_empty > 5:
                            print(f"  [{agent_state.name}] [OK] Observations recovered after {consecutive_empty} empty steps")
                        consecutive_empty = 0

                    # --- STUCK DETECTION: same position for too many steps ---
                    cur_x = last_obs.get('XPos', 0.0)
                    cur_z = last_obs.get('ZPos', 0.0)
                    recent_positions.append((round(cur_x, 1), round(cur_z, 1)))
                    if len(recent_positions) > STUCK_THRESHOLD:
                        recent_positions.pop(0)

                    is_stuck = (
                        len(recent_positions) >= STUCK_THRESHOLD
                        and len(set(recent_positions)) == 1
                    )

                    if is_stuck:
                        print(f"  [{agent_state.name}] Step {step_count + 1}:")
                        print(f"    [STUCK] Position unchanged for {STUCK_THRESHOLD} steps at ({cur_x:.1f}, {cur_z:.1f})")
                        print(f"    [RECOVERY] Jumping + random turn + move")

                        # Recovery: jump, random turn, then move forward
                        try:
                            for _ in range(3):
                                self.step('jump 1')
                            self.step('jump 0')
                            turn_dir = random.choice([-0.7, 0.7])
                            for _ in range(5):
                                self.step(f'turn {turn_dir}')
                            self.step('turn 0')
                            for _ in range(8):
                                obs, reward, done = self.step('move 1')
                                if done or not self.running:
                                    break
                            obs, reward, done = self.step('move 0')
                            agent_state.update_observation(obs)
                            recent_positions.clear()
                            print(f"    [POS] ({obs.get('XPos', 0):.1f}, {obs.get('YPos', 0):.1f}, {obs.get('ZPos', 0):.1f})")
                        except Exception as e:
                            print(f"    [FAIL] Recovery error: {e}")

                        if done:
                            print(f"  [{agent_state.name}] Mission ended during recovery")
                            break

                        step_count += 1
                        continue

                    # --- OVERRIDE: keep agent within building area / rescue from underground ---
                    needs_nav = self._needs_return_to_center(last_obs) or self._is_underground(last_obs)

                    if needs_nav:
                        x = last_obs.get('XPos', 0)
                        z = last_obs.get('ZPos', 0)
                        y = last_obs.get('YPos', 4)
                        dist = math.sqrt(x * x + z * z)
                        underground = self._is_underground(last_obs)
                        print(f"  [{agent_state.name}] Step {step_count + 1}:")
                        if underground:
                            print(f"    [NAV] Underground (y={y:.1f}) — jumping out")
                        else:
                            print(f"    [NAV] Too far from center ({dist:.0f} blocks) — returning")

                        obs, reward, done = self._execute_return_step(last_obs)
                        agent_state.update_observation(obs)

                        print(f"    [POS] ({obs.get('XPos', 0):.1f}, {obs.get('YPos', 0):.1f}, {obs.get('ZPos', 0):.1f})")
                        print()

                        if done:
                            print(f"  [{agent_state.name}] Mission completed!")
                            break

                        step_count += 1
                        continue  # Skip LLM action, do another nav step next iteration

                    # Convert high-level action to Malmo command
                    malmo_action = self._action_to_malmo_command(action_type)

                    # --- SKIP: don't re-execute one-shot actions from the same decision ---
                    # The LLM takes ~10-15s per decision, but this loop runs every 0.2s.
                    # Movement commands can repeat but are capped to prevent overshooting.
                    # One-shot actions (hotbar/place/mine/wait) fire once per decision.
                    decision_ts = decision.get('timestamp')
                    if decision_ts == last_executed_ts:
                        if malmo_action not in _REPEATABLE_CMDS:
                            time.sleep(0.5)
                            continue
                        movement_repeat_count += 1
                        if movement_repeat_count > MAX_MOVEMENT_REPEATS:
                            time.sleep(0.5)
                            continue
                    else:
                        movement_repeat_count = 0
                        last_executed_ts = decision_ts

                    print(f"  [{agent_state.name}] Step {step_count + 1}:")
                    print(f"    [AGENT] Decision: {action_type}")
                    print(f"    [THOUGHT] {reasoning}")
                    print(f"    [CMD] {malmo_action}")

                    # --- PRE-ACTION: ensure pitch is level before every action ---
                    # This prevents the agent from drifting to stare at the
                    # ground or sky across successive actions.
                    last_obs = agent_state.current_observation or {}
                    last_obs = self._ensure_level_pitch(last_obs)

                    # --- PLACE BLOCK: look down briefly, place, then level ---
                    if malmo_action == 'use 1':
                        # Look down ~20° so block is placed on ground
                        for _ in range(3):
                            self.step('pitch 0.5')
                        self.step('pitch 0')  # stop pitch rotation
                        # Place the block
                        obs, reward, done = self.step('use 1')
                        # Look back to level
                        last_obs = agent_state.current_observation or {}
                        self._ensure_level_pitch(last_obs)

                    # --- MINE BLOCK: ensure level pitch so we mine horizontally ---
                    elif malmo_action == 'attack 1':
                        self.step(f'hotbar.{PICKAXE_SLOT} 1')
                        # Pitch is already level from _ensure_level_pitch above
                        obs, reward, done = self.step('attack 1')

                    # --- ALL OTHER ACTIONS: execute normally ---
                    else:
                        obs, reward, done = self.step(malmo_action)
                    total_reward = reward or 0.0

                    # Determine how many extra ticks to sustain this command.
                    # Movement commands set velocity and need multiple ticks.
                    # Action commands fire once, then idle to let the result register.
                    is_movement = malmo_action.split()[0] in (
                        'move', 'strafe', 'turn', 'jump', 'pitch', 'crouch'
                    )
                    extra_ticks = (MOVEMENT_TICKS - 1) if is_movement else (ACTION_TICKS - 1)

                    for _ in range(extra_ticks):
                        if done or not self.running:
                            break
                        tick_cmd = malmo_action if is_movement else 'move 0'
                        obs, reward, done = self.step(tick_cmd)
                        total_reward += (reward or 0.0)

                    # Stop all movement after every action.
                    if not done and self.running:
                        obs, reward, done = self.step('move 0')
                        total_reward += (reward or 0.0)

                    # Update agent observation with the final (most recent) state
                    agent_state.update_observation(obs)

                    # Record last executed action so the LLM prompt can reference it
                    agent_state.last_action = {
                        'action': action_type,
                        'command': malmo_action,
                        'step': step_count
                    }

                    inv_count = len(obs.get('inventory', []))
                    print(f"    [OK] Reward: {total_reward:.1f}  Inventory: {inv_count} slots")
                    print(f"    [POS] ({obs.get('XPos', 0):.1f}, {obs.get('YPos', 0):.1f}, {obs.get('ZPos', 0):.1f})")
                    print()

                    if done:
                        print(f"  [{agent_state.name}] Mission completed!")
                        break

                step_count += 1

        except Exception as e:
            exit_reason = f"EXCEPTION: {type(e).__name__}: {e}"
            print(f"\n  [{agent_state.name}] ERROR in control loop: {e}")
            import traceback
            traceback.print_exc()
        else:
            if step_count >= max_steps:
                exit_reason = f"MAX_STEPS reached ({max_steps})"
            elif not self.running:
                exit_reason = "STOPPED (self.running set to False)"
            else:
                exit_reason = "MISSION_DONE (done=True from Malmo)"
        finally:
            self._reset_complete.set()  # Ensure we unblock waiters even on error
            self.running = False
            print(f"\n  [{agent_state.name}] Control loop finished.")
            print(f"    Exit reason: {exit_reason}")
            print(f"    Total steps: {step_count}")
            print(f"    Max steps: {max_steps}")

    def start_agent_loop(self, agent_state, agent_manager, agent_id: str,
                         max_steps: int = 1000):
        """
        Start the agent control loop in a background thread.

        Returns immediately. Use wait_for_reset() to block until the agent
        has connected and received its first observation.

        Args:
            agent_state: Agent's state object
            agent_manager: Agent manager instance
            agent_id: Agent ID
            max_steps: Maximum steps to run
        """
        self._reset_complete.clear()
        self._thread = threading.Thread(
            target=self._run_agent_loop_blocking,
            args=(agent_state, agent_manager, agent_id, max_steps),
            daemon=True,
            name=f"malmo-agent-{self.role}"
        )
        self._thread.start()

    def wait_for_reset(self, timeout: float = 120.0) -> bool:
        """
        Wait for the agent's reset() to complete.

        Role 0 must complete reset before roles 1+ can start, because
        Malmo needs the mission to be initialized before joiners can
        find the server.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            True if reset completed, False if timed out
        """
        return self._reset_complete.wait(timeout=timeout)

    async def run_agent_loop(self, agent_state, agent_manager, agent_id: str,
                            max_steps: int = 1000):
        """
        Async wrapper that runs the agent loop in a thread.

        Compatible with asyncio.create_task() but delegates actual work
        to a real thread since MalmoEnv uses blocking socket I/O.
        """
        await asyncio.to_thread(
            self._run_agent_loop_blocking,
            agent_state, agent_manager, agent_id, max_steps
        )

    # Direct mapping from cognitive controller action menu names to Malmo commands.
    # This must stay in sync with CognitiveController.ACTION_MENU.
    _ACTION_MAP = {
        'move_forward':   'move 1',
        'turn_left':      'turn -1',
        'turn_right':     'turn 1',
        'place_block':    'use 1',
        'mine_block':     'attack 1',
        'jump_forward':   'jump 1',
        'select_slot_3':  'hotbar.3 1',
        'select_slot_4':  'hotbar.4 1',
        'select_slot_5':  'hotbar.5 1',
        'select_slot_6':  'hotbar.6 1',
        'select_slot_7':  'hotbar.7 1',
        'look_around':    'turn 1',
        'wait':           'move 0',
    }

    def _action_to_malmo_command(self, action: str) -> str:
        """
        Convert action menu name to Malmo command via direct lookup.

        The cognitive controller now outputs exact action names from a
        constrained menu, so we do a direct dict lookup instead of
        keyword matching (which caused everything to default to 'move 1').

        Args:
            action: Exact action name from ACTION_MENU (e.g. 'place_block')

        Returns:
            Malmo action command
        """
        cmd = self._ACTION_MAP.get(action.lower().strip())
        if cmd is None:
            print(f"  [WARN] Unknown action '{action}' in _action_to_malmo_command, defaulting to move 1")
            cmd = 'move 1'
        return cmd

    def execute_action_sequence(self, actions: list) -> list:
        """
        Execute a sequence of actions in order.

        Args:
            actions: List of high-level action strings

        Returns:
            List of (observation, reward, done) tuples for each action
        """
        results = []
        for action in actions:
            malmo_cmd = self._action_to_malmo_command(action)
            obs, reward, done = self.step(malmo_cmd)
            results.append((obs, reward, done))
            if done:
                break
        return results

    def stop(self):
        """Stop the agent control loop."""
        self.running = False
