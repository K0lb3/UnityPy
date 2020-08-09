from .AnimationClip import xform
from .NamedObject import NamedObject


class Avatar(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.m_AvatarSize = reader.read_u_int()
        self.m_Avatar = AvatarConstant(reader)

        numTOS = reader.read_int()
        self.m_TOS = {}
        for _ in range(numTOS):
            key = reader.read_u_int()
            self.m_TOS[key] = reader.read_aligned_string()

    # HumanDescription m_HumanDescription 2019 and up

    def FindBonePath(self, hash):
        return self.m_TOS[hash]


class Node:
    def __init__(self, reader):
        self.m_ParentId = reader.read_int()
        self.m_AxesId = reader.read_int()


class Limit:
    def __init__(self, reader):
        version = reader.version
        if version >= (5, 4):  # 5.4 and up
            self.m_Min = reader.read_vector3()
            self.m_Max = reader.read_vector3()
        else:
            self.m_Min = reader.read_vector4()
            self.m_Max = reader.read_vector4()


class Axes:
    def __init__(self, reader):
        version = reader.version
        self.m_PreQ = reader.read_vector4()
        self.m_PostQ = reader.read_vector4()
        if version >= (5, 4):  # 5.4 and up
            self.m_Sgn = reader.read_vector3()
        else:
            self.m_Sgn = reader.read_vector4()
        self.m_Limit = Limit(reader)
        self.m_Length = reader.read_float()
        self.m_Type = reader.read_u_int()


class Skeleton:
    def __init__(self, reader):
        numNodes = reader.read_int()
        self.m_Node = [Node(reader) for _ in range(numNodes)]

        self.m_ID = reader.read_u_int_array()

        numAxes = reader.read_int()
        self.m_AxesArray = [Axes(reader) for _ in range(numAxes)]


class SkeletonPose:
    def __init__(self, reader):
        numXforms = reader.read_int()
        self.m_X = [xform(reader) for _ in range(numXforms)]


class Hand:
    def __init__(self, reader):
        self.m_HandBoneIndex = reader.read_int_array()


class Handle:
    def __init__(self, reader):
        self.m_X = xform(reader)
        self.m_ParentHumanIndex = reader.read_u_int()
        self.m_ID = reader.read_u_int()


class Collider:
    def __init__(self, reader):
        self.m_X = xform(reader)
        self.m_Type = reader.read_u_int()
        self.m_XMotionType = reader.read_u_int()
        self.m_YMotionType = reader.read_u_int()
        self.m_ZMotionType = reader.read_u_int()
        self.m_MinLimitX = reader.read_float()
        self.m_MaxLimitX = reader.read_float()
        self.m_MaxLimitY = reader.read_float()
        self.m_MaxLimitZ = reader.read_float()


class Human:
    def __init__(self, reader):
        version = reader.version
        self.m_RootX = xform(reader)
        self.m_Skeleton = Skeleton(reader)
        self.m_SkeletonPose = SkeletonPose(reader)
        self.m_LeftHand = Hand(reader)
        self.m_RightHand = Hand(reader)

        if version < (2018, 2):  # 2018.2 down
            numHandles = reader.read_int()
            self.m_Handles = [Handle(reader) for _ in range(numHandles)]
            numColliders = reader.read_int()
            self.m_ColliderArray = [Collider(reader) for _ in range(numColliders)]
        self.m_HumanBoneIndex = reader.read_int_array()
        self.m_HumanBoneMass = reader.read_float_array()

        if version < (2018, 2):  # 2018.2 down
            self.m_ColliderIndex = reader.read_int_array()

        self.m_Scale = reader.read_float()
        self.m_ArmTwist = reader.read_float()
        self.m_ForeArmTwist = reader.read_float()
        self.m_UpperLegTwist = reader.read_float()
        self.m_LegTwist = reader.read_float()
        self.m_ArmStretch = reader.read_float()
        self.m_LegStretch = reader.read_float()
        self.m_FeetSpacing = reader.read_float()
        self.m_HasLeftHand = reader.read_boolean()
        self.m_HasRightHand = reader.read_boolean()
        if version >= (5, 2):  # 5.2 and up
            self.m_HasTDoF = reader.read_boolean()
        reader.align_stream()


class AvatarConstant:
    def __init__(self, reader):
        version = reader.version
        self.m_AvatarSkeleton = Skeleton(reader)
        self.m_AvatarSkeletonPose = SkeletonPose(reader)

        if version >= (4, 3):  # 4.3 and up
            self.m_DefaultPose = SkeletonPose(reader)
            self.m_SkeletonNameIDArray = reader.read_u_int_array()

        self.m_Human = Human(reader)

        self.m_HumanSkeletonIndexArray = reader.read_int_array()

        if version >= (4, 3):  # 4.3 and up
            self.m_HumanSkeletonReverseIndexArray = reader.read_int_array()

        self.m_RootMotionBoneIndex = reader.read_int()
        self.m_RootMotionBoneX = xform(reader)

        if version >= (4, 3):  # 4.3 and up
            self.m_RootMotionSkeleton = Skeleton(reader)
            self.m_RootMotionSkeletonPose = SkeletonPose(reader)

            self.m_RootMotionSkeletonIndexArray = reader.read_int_array()
