class Rectangle:
    height: int
    width: int
    x: int
    y: int

    def __init__(self, *args, **kwargs):
        if args:
            # Rectangle(Point, Size)
            if len(args) == 4:
                self.x, self.y, self.width, self.height = args
        elif kwargs:
            self.__dict__.update(kwargs)

    def round(rect):
        return Rectangle(
            round(rect.x), round(rect.y), round(rect.width), round(rect.height)
        )

    @property
    def left(self):
        return self.x

    @property
    def top(self):
        return self.y

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def size(self):
        return (self.width, self.height)

    @property
    def location(self):
        return (self.x, self.y)
