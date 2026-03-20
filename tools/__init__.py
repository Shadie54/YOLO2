# tools/__init__.py

# hlavný ToolManager
from .tool_manager import ToolManager

# jednotlivé tools
from .pencil import PencilTool
from .eraser import EraserTool
from .line import LineTool
from .polyline import PolylineTool
from .polycurve import PolycurveTool
from .text import TextTool  # pridaný text tool

# voliteľne: zoznam všetkých nástrojov
__all__ = [
    "ToolManager",
    "PencilTool",
    "EraserTool",
    "LineTool",
    "PolylineTool",
    "PolycurveTool",
    "TextTool",  # doplnený do __all__
]