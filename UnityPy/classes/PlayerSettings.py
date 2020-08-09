from .Object import Object


class PlayerSettings(Object):
    def __init__(self, reader):
        super().__init__(reader=reader)
        version = self.version
        if version >= (5, 4):  # 5.4.0 nad up
            self.productGUID = reader.read_bytes(16)

        self.AndroidProfiler = reader.read_boolean()
        # bool AndroidFilterTouchesWhenObscured 2017.2 and up
        # bool AndroidEnableSustainedPerformanceMode 2018 and up
        reader.align_stream()
        self.defaultScreenOrientation = reader.read_int()
        self.targetDevice = reader.read_int()
        if version < (5, 3):  # 5.3 down
            if version < (5,):  # 5.0 down
                self.targetPlatform = reader.read_int()  # 4.0 and up targetGlesGraphics
                if version >= (4, 6):  # 4.6 and up
                    self.targetIOSGraphics = reader.read_int()
            self.targetResolution = reader.read_int()
        else:
            self.useOnDemandResources = reader.read_boolean()
            reader.align_stream()
        if version >= (3, 5):  # 3.5 and up
            self.accelerometerFrequency = reader.read_int()
        self.companyName = reader.read_aligned_string()
        self.productName = reader.read_aligned_string()
