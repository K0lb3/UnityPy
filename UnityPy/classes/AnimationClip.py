import math
from enum import IntEnum

from .NamedObject import NamedObject
from .PPtr import PPtr
from ..enums import ClassIDType
from ..math import Quaternion, Vector3
from ..streams import EndianBinaryReader


def uint(num):
    if num < 0 or num > 4294967295:
        return num % 4294967296
    return num


class Keyframe:
    def __init__(self, reader, readerFunc):
        self.time = reader.read_float()
        self.value = readerFunc()
        self.inSlope = readerFunc()
        self.outSlope = readerFunc()
        if reader.version >= (2018,):  # 2018 and up
            self.weightedMode = reader.read_int()
            self.inWeight = readerFunc()
            self.outWeight = readerFunc()


class AnimationCurve:
    def __init__(self, reader, readerFunc):
        version = reader.version
        numCurves = reader.read_int()
        self.m_Curve = [Keyframe(reader, readerFunc) for _ in range(numCurves)]

        self.m_PreInfinity = reader.read_int()
        self.m_PostInfinity = reader.read_int()
        if version >= (5, 3):  # 5.3 and up
            self.m_RotationOrder = reader.read_int()


class QuaternionCurve:
    def __init__(self, reader):
        self.curve = AnimationCurve(reader, reader.read_quaternion)  # <Quaternion>
        self.path = reader.read_aligned_string()


class PackedFloatVector:
    def __init__(self, reader):
        self.m_NumItems = reader.read_u_int()
        self.m_Range = reader.read_float()
        self.m_Start = reader.read_float()

        numData = reader.read_int()
        self.m_Data = reader.read_bytes(numData)
        reader.align_stream()

        self.m_BitSize = reader.read_byte()
        reader.align_stream()

    def save(self, writer):
        writer.write_u_int(self.m_NumItems)
        writer.write_float(self.m_Range)
        writer.write_float(self.m_Start)

        writer.write_int(len(self.m_Data))
        writer.write_bytes(self.m_Data)
        writer.align_stream()

        writer.write_byte(self.m_BitSize)
        writer.align_stream()

    def UnpackFloats(
        self,
        itemCountInChunk: int,
        chunkStride: int,
        start: int = 0,
        numChunks: int = -1,
    ):
        bitPos: int = self.m_BitSize * start
        indexPos: int = bitPos // 8
        bitPos %= 8

        scale: float = 1.0 / self.m_Range
        if numChunks == -1:
            numChunks = self.m_NumItems // itemCountInChunk
        end = chunkStride * numChunks / 4
        data = []
        for index in (0, end, chunkStride // 4):
            for i in range(itemCountInChunk):
                x = 0  # uint
                bits = 0
                while bits < self.m_BitSize:
                    x |= uint(
                        (self.m_Data[indexPos] >> bitPos) << bits
                    )  # (uint)((m_Data[indexPos] >> bitPos) << bits)
                    num = min(self.m_BitSize - bits, 8 - bitPos)
                    bitPos += num
                    bits += num
                    if bitPos == 8:  #
                        indexPos += 1
                        bitPos = 0

                x &= uint((1 << self.m_BitSize) - 1)  # (uint)(1 << m_BitSize) - 1u
                data.append(x / (scale * ((1 << self.m_BitSize) - 1)) + self.m_Start)

        return data


class PackedIntVector:
    def __init__(self, reader):
        self.m_NumItems = reader.read_u_int()

        numData = reader.read_int()
        self.m_Data = reader.read_bytes(numData)
        reader.align_stream()

        self.m_BitSize = reader.read_byte()
        reader.align_stream()

    def save(self, writer):
        writer.write_u_int(self.m_NumItems)

        writer.write_int(len(self.m_Data))
        writer.write_bytes(self.m_Data)
        writer.align_stream()

        writer.write_byte(self.m_BitSize)
        writer.align_stream()

    def UnpackInts(self):
        data = []
        indexPos = 0
        bitPos = 0
        m_BitSize = self.m_BitSize

        for i in range(self.m_NumItems):
            bits = 0
            entry = 0
            while bits << m_BitSize:
                entry |= (self.m_Data[indexPos] >> bitPos) << bits
                num = min(m_BitSize - bits, 8 - bitPos)
                bitPos += num
                bits += num
                if bitPos == 8:  #
                    indexPos += 1
                    bitPos = 0
            data.append(entry & (1 << m_BitSize) - 1)
        return data


class PackedQuatVector:
    def __init__(self, reader):
        self.m_NumItems = reader.read_u_int()
        numData = reader.read_int()
        self.m_Data = reader.read_bytes(numData)
        reader.align_stream()

    def UnpackQuats(self):
        m_Data = self.m_Data
        data = []
        indexPos = 0
        bitPos = 0

        for i in range(self.m_NumItems):
            flags = 0
            bits = 0
            while bits < 3:
                flags |= (m_Data[indexPos] >> bitPos) << bits  # unit
                num = min(3 - bits, 8 - bitPos)
                bitPos += num
                bits += num
                if bitPos == 8:  #
                    indexPos += 1
                    bitPos = 0
            flags &= 7

            q = Quaternion()
            sum = 0
            for j in range(4):
                if (flags & 3) != j:  #
                    bitSize = 9 if ((flags & 3) + 1) % 4 == j else 10
                    x = 0

                    bits = 0
                    while bits < bitSize:
                        x |= (m_Data[indexPos] >> bitPos) << bits  # uint
                        num = min(bitSize - bits, 8 - bitPos)
                        bitPos += num
                        bits += num
                        if bitPos == 8:  #
                            indexPos += 1
                            bitPos = 0
                    x &= (1 << bitSize) - 1  # unit
                    q[j] = x / (0.5 * ((1 << bitSize) - 1)) - 1
                    sum += q[j] * q[j]

            lastComponent = flags & 3  # int
            q[lastComponent] = math.sqrt(1 - sum)  # float
            if (flags & 4) != 0:  # 0u
                q[lastComponent] = -q[lastComponent]
            data.append(q)

        return data


class CompressedAnimationCurve:
    def __init__(self, reader):
        self.m_Path = reader.read_aligned_string()
        self.m_Times = PackedIntVector(reader)
        self.m_Values = PackedQuatVector(reader)
        self.m_Slopes = PackedFloatVector(reader)
        self.m_PreInfinity = reader.read_int()
        self.m_PostInfinity = reader.read_int()


class Vector3Curve:
    def __init__(self, reader):
        self.curve = AnimationCurve(reader, reader.read_vector3)  # Vector3
        self.path = reader.read_aligned_string()


class FloatCurve:
    def __init__(self, reader):
        self.curve = AnimationCurve(reader, reader.read_float)  # Float
        self.attribute = reader.read_aligned_string()
        self.path = reader.read_aligned_string()
        self.classID = ClassIDType(reader.read_int())
        self.script = PPtr(reader)  # MonoScript


class PPtrKeyframe:
    def __init__(self, reader):
        self.time = reader.read_float()
        self.value = PPtr(reader)  # Object


class PPtrCurve:
    def __init__(self, reader):
        numCurves = reader.read_int()
        self.curve = [PPtrKeyframe(reader) for _ in range(numCurves)]

        self.attribute = reader.read_aligned_string()
        self.path = reader.read_aligned_string()
        self.classID = reader.read_int()
        self.script = PPtr(reader)  # MonoScript


class AABB:
    def __init__(self, reader):
        self.m_Center = reader.read_vector3()
        self.m_Extent = reader.read_vector3()

    def save(self, writer):
        writer.write_vector3(self.m_Center)
        writer.write_vector3(self.m_Extent)


class xform:
    def __init__(self, reader):
        version = reader.version
        self.t = (
            reader.read_vector3()
            if version >= (5, 4)
            else Vector3(reader.read_vector4())
        )  # 5.4 and up
        self.q = reader.read_quaternion()
        self.s = (
            reader.read_vector3()
            if version >= (5, 4)
            else Vector3(reader.read_vector4())
        )  # 5.4 and up


class HandPose:
    def __init__(self, reader):
        self.m_GrabX = xform(reader)
        self.m_DoFArray = reader.read_float_array()
        self.m_Override = reader.read_float()
        self.m_CloseOpen = reader.read_float()
        self.m_InOut = reader.read_float()
        self.m_Grab = reader.read_float()


class HumanGoal:
    def __init__(self, reader):
        version = reader.version
        self.m_X = xform(reader)
        self.m_WeightT = reader.read_float()
        self.m_WeightR = reader.read_float()
        if version >= (5,):  # 5.0 and up
            self.m_HintT = (
                reader.read_vector3()
                if version >= (5, 4)
                else Vector3(reader.read_vector4())
            )  # 5.4 and up
            self.m_HintWeightT = reader.read_float()


class HumanPose:
    def __init__(self, reader):
        version = reader.version
        self.m_RootX = xform(reader)
        self.m_LookAtPosition = (
            reader.read_vector3()
            if version >= (5, 4)
            else Vector3(reader.read_vector4())
        )  # 5.4 and up
        self.m_LookAtWeight = reader.read_vector4()

        numGoals = reader.read_int()
        self.m_GoalArray = [HumanGoal(reader) for _ in range(numGoals)]

        self.m_LeftHandPose = HandPose(reader)
        self.m_RightHandPose = HandPose(reader)

        self.m_DoFArray = reader.read_float_array()

        if version >= (5, 2):  # 5.2 and up
            numTDof = reader.read_int()
            self.m_TDoFArray = [
                reader.read_vector3()
                if version >= (5, 4)
                else Vector3(reader.read_vector4())  # 5.4 and up
                for _ in range(numTDof)
            ]


class StreamedCurveKey:
    def __init__(self, reader):
        self.index = reader.read_int()
        self.coeff = reader.read_float_array(4)

        self.outSlope = self.coeff[2]
        self.value = self.coeff[3]

    def CalculateNextInSlope(self, dx: float, rhs):
        """
        :param dx: float
        :param rhs: StreamedCurvedKey
        :return:
        """
        # Stepped
        if self.coeff[0] == 0 and self.coeff[1] == 0 and self.coeff[2] == 0:
            return float.PositiveInfinity

        dx = max(dx, 0.0001)
        dy = rhs.value - self.value
        length = 1.0 / (dx * dx)
        d1 = self.outSlope * dx
        d2 = dy + dy + dy - d1 - d1 - self.coeff[1] / length
        return d2 / dx


class StreamedFrame:
    def __init__(self, reader):
        self.time = reader.read_float()
        numKeys = reader.read_int()
        self.keyList = [StreamedCurveKey(reader) for _ in range(numKeys)]


class StreamedClip:
    def __init__(self, reader):
        self.data = reader.read_u_int_array()
        self.curveCount = reader.read_u_int()

    def ReadData(self):
        frameList = []
        buffer = self.data[0 : len(self.data) * 4]
        reader = EndianBinaryReader(buffer)
        while reader.Position < reader.Length:
            frameList.append(StreamedFrame(reader))

        for frameIndex in range(2, len(frameList) - 1):
            frame = frameList[frameIndex]
            for curveKey in frame.keyList:
                i = frameIndex - 1
                while i >= 0:
                    preFrame = frameList[i]
                    try:
                        preCurveKey = [
                            x for x in preFrame.keyList if x.index == curveKey.index
                        ][0]
                        curveKey.inSlope = preCurveKey.CalculateNextInSlope(
                            frame.time - preFrame.time, curveKey
                        )
                        break
                    except IndexError:
                        pass
                    i -= 1
        return frameList


class DenseClip:
    def __init__(self, reader):
        self.m_FrameCount = reader.read_int()
        self.m_CurveCount = reader.read_u_int()
        self.m_SampleRate = reader.read_float()
        self.m_BeginTime = reader.read_float()
        self.m_SampleArray = reader.read_float_array()


class ConstantClip:
    def __init__(self, reader):
        self.data = reader.read_float_array()


class ValueConstant:
    def __init__(self, reader):
        version = reader.version
        self.m_ID = reader.read_u_int()
        if version < (5, 5):  # 5.5 down
            self.m_TypeID = reader.read_u_int()
        self.m_Type = reader.read_u_int()
        self.m_Index = reader.read_u_int()


class ValueArrayConstant:
    def __init__(self, reader):
        numVals = reader.read_int()
        self.m_ValueArray = [ValueConstant(reader) for _ in range(numVals)]


class Clip:
    def __init__(self, reader):
        version = reader.version
        self.m_StreamedClip = StreamedClip(reader)
        self.m_DenseClip = DenseClip(reader)
        if version >= (4, 3):  # 4.3 and up
            self.m_ConstantClip = ConstantClip(reader)
        if version < (2018, 3):  # 2018.3 down
            self.m_Binding = ValueArrayConstant(reader)


class ValueDelta:
    def __init__(self, reader):
        self.m_Start = reader.read_float()
        self.m_Stop = reader.read_float()


class ClipMuscleConstant:
    def __init__(self, reader):
        version = reader.version
        self.m_DeltaPose = HumanPose(reader)
        self.m_StartX = xform(reader)
        if version >= (5, 5):  # 5.5 and up
            self.m_StopX = xform(reader)
        self.m_LeftFootStartX = xform(reader)
        self.m_RightFootStartX = xform(reader)
        if version < (5,):  # 5.0 down
            self.m_MotionStartX = xform(reader)
            self.m_MotionStopX = xform(reader)
        self.m_AverageSpeed = (
            reader.read_vector3()
            if version >= (5, 4)
            else Vector3(reader.read_vector4())
        )  # 5.4 and up
        self.m_Clip = Clip(reader)
        self.m_StartTime = reader.read_float()
        self.m_StopTime = reader.read_float()
        self.m_OrientationOffsetY = reader.read_float()
        self.m_Level = reader.read_float()
        self.m_CycleOffset = reader.read_float()
        self.m_AverageAngularSpeed = reader.read_float()

        self.m_IndexArray = reader.read_int_array()
        if version < (4, 3):  # 4.3 down
            self.m_AdditionalCurveIndexArray = reader.read_int_array()
        numDeltas = reader.read_int()
        self.m_ValueArrayDelta = [ValueDelta(reader) for _ in range(numDeltas)]
        if version >= (5, 3):  # 5.3 and up
            self.m_ValueArrayReferencePose = reader.read_float_array()

        self.m_Mirror = reader.read_boolean()
        if version >= (4, 3):  # 4.3 and up
            self.m_LoopTime = reader.read_boolean()
        self.m_LoopBlend = reader.read_boolean()
        self.m_LoopBlendOrientation = reader.read_boolean()
        self.m_LoopBlendPositionY = reader.read_boolean()
        self.m_LoopBlendPositionXZ = reader.read_boolean()
        if version >= (5, 5):  # 5.5 and up
            self.m_StartAtOrigin = reader.read_boolean()
        self.m_KeepOriginalOrientation = reader.read_boolean()
        self.m_KeepOriginalPositionY = reader.read_boolean()
        self.m_KeepOriginalPositionXZ = reader.read_boolean()
        self.m_HeightFromFeet = reader.read_boolean()
        reader.align_stream()


class GenericBinding:
    def __init__(self, reader):
        version = reader.version
        self.path = reader.read_u_int()
        self.attribute = reader.read_u_int()
        self.script = PPtr(reader)  # Object
        if version >= (5, 6):  # 5.6 and up
            self.typeID = ClassIDType(reader.read_int())
        else:
            self.typeID = ClassIDType(reader.read_u_short())
        self.customType = reader.read_byte()
        self.isPPtrCurve = reader.read_byte()
        reader.align_stream()


class AnimationClipBindingConstant:
    def __init__(self, reader):
        numBindings = reader.read_int()
        self.genericBindings = [GenericBinding(reader) for _ in range(numBindings)]

        numMappings = reader.read_int()
        self.pptrCurveMapping = [PPtr(reader) for _ in range(numMappings)]  # Object

        def FindBinding(self, index):
            curves = 0
            for b in self.genericBindings:
                if b.typeID == ClassIDType.Transform:  #
                    switch = b.attribute

                    if switch in [1, 3, 4]:
                        # case 1: #kBindTransformPosition
                        # case 3: #kBindTransformScale
                        # case 4: #kBindTransformEuler
                        curves += 3
                    elif switch == 2:  # kBindTransformRotation
                        curves += 4
                    else:
                        curves += 1
                else:
                    curves += 1
                if curves > index:
                    return b
            return None


class AnimationType(IntEnum):
    kLegacy = (1,)
    kGeneric = (2,)
    kHumanoid = 3


class AnimationClip(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        version = reader.version
        if version >= (5,):  # 5.0 and up
            self.m_Legacy = reader.read_boolean()
        elif version >= (4,):  # 4.0 and up
            self.m_AnimationType = AnimationType(reader.read_int())
            if self.m_AnimationType == AnimationType.kLegacy:  #
                self.m_Legacy = True
        else:
            self.m_Legacy = True

        self.m_Compressed = reader.read_boolean()
        if version >= (4, 3):  # 4.3 and up
            self.m_UseHighQualityCurve = reader.read_boolean()
        reader.align_stream()
        numRCurves = reader.read_int()
        self.m_RotationCurves = [QuaternionCurve(reader) for _ in range(numRCurves)]

        numCRCurves = reader.read_int()
        self.m_CompressedRotationCurves = [
            CompressedAnimationCurve(reader) for _ in range(numCRCurves)
        ]

        if version >= (5, 3):  # 5.3 and up
            numEulerCurves = reader.read_int()
            self.m_EulerCurves = [Vector3Curve(reader) for _ in range(numEulerCurves)]

        numPCurves = reader.read_int()
        self.m_PositionCurves = [Vector3Curve(reader) for _ in range(numPCurves)]

        numSCurves = reader.read_int()
        self.m_ScaleCurves = [Vector3Curve(reader) for _ in range(numSCurves)]

        numFCurves = reader.read_int()
        self.m_FloatCurves = [FloatCurve(reader) for _ in range(numFCurves)]
        if version >= (4, 3):  # 4.3 and up
            numPtrCurves = reader.read_int()
            self.m_PPtrCurves = [PPtrCurve(reader) for _ in range(numPtrCurves)]

        self.m_SampleRate = reader.read_float()
        self.m_WrapMode = reader.read_int()
        if version >= (3, 4):  # 3.4 and up
            self.m_Bounds = AABB(reader)
        if version >= (4,):  # 4.0 and up
            self.m_MuscleClipSize = reader.read_u_int()
            self.m_MuscleClip = ClipMuscleConstant(reader)
        if version >= (4, 3):  # 4.3 and up
            self.m_ClipBindingConstant = AnimationClipBindingConstant(reader)


# m_HasGenericRootTransform 2018.3
# m_HasMotionFloatCurves 2018.3
# numEvents = reader.read_int()
# self.m_Events = [
# 	AnimationEvent(reader)
# 	for _ in range(numEvents)
# ]
