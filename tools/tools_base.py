from abc import ABC, abstractmethod

class BaseTool(ABC):
    """Abstraktný nástroj – každý konkrétny tool dedí odtiaľto"""

    @abstractmethod
    def mousePress(self, tm, event): pass

    @abstractmethod
    def mouseMove(self, tm, event): pass

    @abstractmethod
    def mouseRelease(self, tm, event): pass

    def keyPress(self, tm, event): pass  # optional