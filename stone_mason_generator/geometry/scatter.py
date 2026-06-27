"""Scatter Engine -- delegates to LayoutStrategy for point generation.

Refactored in Step 9: ScatterEngine is no longer a pipeline stage.
It becomes a thin wrapper that delegates to a LayoutStrategy.

The Composer pipeline now calls LayoutStrategy.build() directly.
This module remains for backward compatibility and re-exports.

Historical: ScatterEngine previously contained Distribute Points on
Faces logic. That logic is now in RandomScatter (a LayoutStrategy).
"""

from .layout import LayoutStrategy, CourseLayout, RandomScatter

# Re-export for external imports
__all__ = ['LayoutStrategy', 'CourseLayout', 'RandomScatter']

