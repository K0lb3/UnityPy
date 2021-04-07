from .Component import Component
from .PPtr import PPtr


class StaticBatchInfo:
    def __init__(self, reader):
        self.firstSubMesh = reader.read_u_short()
        self.subMeshCount = reader.read_u_short()


class Renderer(Component):
    def __init__(self, reader):
        super().__init__(reader=reader)
        version = self.version
        if version < (5,):  # 5.0 down
            self.m_Enabled = reader.read_boolean()
            self.m_CastShadows = reader.read_boolean()
            self.m_ReceiveShadows = reader.read_boolean()
            self.m_LightmapIndex = reader.read_byte()
        else:  # 5.0 and up
            if version >= (5, 4):  # 5.4 and up
                self.m_Enabled = reader.read_boolean()
                self.m_CastShadows = reader.read_byte()
                self.m_ReceiveShadows = reader.read_byte()
                if version[:2] > (2017, 2):  # 2017.2 and up
                    self.m_DynamicOccludee = reader.read_byte()
                self.m_MotionVectors = reader.read_byte()
                self.m_LightProbeUsage = reader.read_byte()
                self.m_ReflectionProbeUsage = reader.read_byte()
                if version >= (2019, 3):  # 2019.3 and up
                    self.m_RayTracingMode = reader.read_byte()
                if version >= (2020,):  # 2020.1 and up
                    self.m_RayTraceProcedural = reader.read_byte()
                reader.align_stream()
            else:
                self.m_Enabled = reader.read_boolean()
                reader.align_stream()
                self.m_CastShadows = reader.read_byte()
                self.m_ReceiveShadows = reader.read_boolean()
                reader.align_stream()

            if version >= (2018,):  # 2018 and up
                self.m_RenderingLayerMask = reader.read_u_int()

            if version >= (2018, 3):  # 2018.3 and up
                self.m_RendererPriority = reader.read_int()

            self.m_LightmapIndex = reader.read_u_short()
            self.m_LightmapIndexDynamic = reader.read_u_short()

        if version >= (3,):  # 3.0 and up
            self.m_LightmapTilingOffset = reader.read_vector4()

        if version >= (5,):  # 5.0 and up
            self.m_LightmapTilingOffsetDynamic = reader.read_vector4()

        m_MaterialsSize = reader.read_int()
        self.m_Materials = [PPtr(reader)
                            for _ in range(m_MaterialsSize)]  # Material

        if version < (3,):  # 3.0 down
            self.m_LightmapTilingOffset = reader.read_vector4()
        else:  # 3.0 and up
            if version >= (5, 5):  # 5.5 and up
                self.m_StaticBatchInfo = StaticBatchInfo(reader)
            else:
                self.m_SubsetIndices = reader.read_u_int_array()

            self.m_StaticBatchRoot = PPtr(reader)  # Transform

        if version >= (5, 4):  # 5.4 and up
            self.m_ProbeAnchor = PPtr(reader)  # Transform
            self.m_LightProbeVolumeOverride = PPtr(reader)  # GameObject
        elif version >= (3, 5):  # 3.5 - 5.3
            self.m_UseLightProbes = reader.read_boolean()
            reader.align_stream()

            if version >= (5,):  # 5.0 and up
                self.m_ReflectionProbeUsage = reader.read_int()

            # Transform #5.0 and up m_ProbeAnchor
            self.m_LightProbeAnchor = PPtr(reader)

        if version >= (4, 3):  # 4.3 and up
            if version[:2] == (4, 3):  # 4.3
                self.m_SortingLayer = reader.read_short()
            else:
                self.m_SortingLayerID = reader.read_u_int()

            # SInt16 m_SortingLayer 5.6 and up
            self.m_SortingOrder = reader.read_short()
            reader.align_stream()
