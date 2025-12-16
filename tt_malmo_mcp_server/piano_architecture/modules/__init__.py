"""
PIANO Modules - The 10 concurrent information processing modules.

These modules run in parallel and feed information through the
Cognitive Controller bottleneck.
"""

from .base_module import Module
from .action_awareness import ActionAwarenessModule
from .perception import PerceptionModule
from .social_awareness import SocialAwarenessModule
from .goal_generation import GoalGenerationModule
from .memory_consolidation import MemoryConsolidationModule

__all__ = [
    'Module',
    'ActionAwarenessModule',
    'PerceptionModule',
    'SocialAwarenessModule',
    'GoalGenerationModule',
    'MemoryConsolidationModule'
]
