class Progress:
    pre_value: int

    def reset(self):
        self.pre_value = 0
        self.report(0)

    def report(self, current: int, total: int = None):
        if total:
            value = current * 100 // total
        else:
            value = current

        if value > self.pre_value:
            self.pre_value = value
            print(f"{value}%")
