class ziplist:
    """A ziplist is a list that maintains a current position"""
    def __init__(self, a_list: list):
        if len(a_list) < 1:
            raise ValueError("initialize with non-empty list")
        self._list = a_list
        self._current = 0

    def current(self):
        return self._list[self._current]

    def forward(self):
        self._current = (self._current + 1) % len(self._list)

    def backward(self):
        self._current = (self._current - 1) % len(self._list)
