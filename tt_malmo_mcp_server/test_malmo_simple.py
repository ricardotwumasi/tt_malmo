#!/usr/bin/env python3
"""
Simple Malmo Connection Test - Minimal test to verify Malmo communication.

This uses the exact example from MalmoEnv documentation to test basic connectivity.
"""

import malmoenv
import sys

# Minimal mission XML from Malmo documentation
SIMPLE_MISSION = """<?xml version="1.0" encoding="UTF-8" ?>
<Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <About>
    <Summary>Simple Test Mission</Summary>
  </About>

  <ServerSection>
    <ServerInitialConditions>
      <Time>
        <StartTime>6000</StartTime>
        <AllowPassageOfTime>false</AllowPassageOfTime>
      </Time>
      <Weather>clear</Weather>
    </ServerInitialConditions>

    <ServerHandlers>
      <FlatWorldGenerator generatorString="3;7,2*3,2;1;"/>
      <ServerQuitFromTimeUp timeLimitMs="30000"/>
      <ServerQuitWhenAnyAgentFinishes/>
    </ServerHandlers>
  </ServerSection>

  <AgentSection mode="Survival">
    <Name>TestAgent</Name>
    <AgentStart>
      <Placement x="0" y="4" z="0"/>
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
</Mission>
"""


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000

    print("=" * 60)
    print("  Simple Malmo Connection Test")
    print("=" * 60)
    print(f"  Port: {port}")
    print()

    print("Step 1: Creating MalmoEnv...")
    env = malmoenv.make()
    print("  Done")

    print("\nStep 2: Initializing with mission XML...")
    try:
        env.init(
            SIMPLE_MISSION,
            port,
            server='127.0.0.1',
            role=0,
            exp_uid="test-exp-001",
            episode=0
        )
        print("  Done")
    except Exception as e:
        print(f"  FAILED: {e}")
        return

    print("\nStep 3: Resetting environment (starts mission)...")
    try:
        obs = env.reset()
        print(f"  Done - got observation with shape: {obs.shape if hasattr(obs, 'shape') else type(obs)}")
    except Exception as e:
        print(f"  FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\nStep 4: Taking actions...")
    try:
        for i in range(5):
            # Move forward
            action = env.action_space.sample()  # Random action
            obs, reward, done, info = env.step(action)
            print(f"  Step {i+1}: action={action}, reward={reward}, done={done}")
            if done:
                print("  Mission ended")
                break
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\nStep 5: Closing environment...")
    env.close()
    print("  Done")

    print("\n" + "=" * 60)
    print("  Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
