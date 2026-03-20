class TempPoint:
    """Dočasný bod pre dynamický preview (len POLYCURVE/POLYLINE)"""
    def __init__(self, pos):
        self._pos = pos

    def pos(self):
        return self._pos