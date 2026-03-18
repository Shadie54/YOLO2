# tools_helpers.py
class TempPoint:
    """Dočasný bod pre dynamický preview (len POLYCURVE/POLYLINE)"""
    def __init__(self, pos):
        self._pos = pos
        self._is_temp = True

    def pos(self):
        return self._pos