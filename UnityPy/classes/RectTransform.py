from .Transform import Transform


class RectTransform(Transform):
    def __init__(self, reader):
        super().__init__(reader=reader)
