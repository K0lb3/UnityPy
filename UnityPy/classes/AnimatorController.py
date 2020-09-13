from .AnimationClip import ValueArrayConstant
from .PPtr import PPtr
from .RuntimeAnimatorController import RuntimeAnimatorController
from ..math import Vector3


class AnimatorController(RuntimeAnimatorController):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.m_ControllerSize = reader.read_u_int()
        self.m_Controller = ControllerConstant(reader)
        tosSize = reader.read_int()
        self.m_TOS = {}
        for _ in range(tosSize):
            key = reader.read_u_int()
            self.m_TOS[key] = reader.read_aligned_string()

        numClips = reader.read_int()
        self.m_AnimationClips = [PPtr(reader) for _ in range(numClips)]


class HumanPoseMask:
    def __init__(self, reader):
        version = reader.version
        self.word0 = reader.read_u_int()
        self.word1 = reader.read_u_int()
        if version >= (5, 2):  # 5.2 and up
            self.word2 = reader.read_u_int()


class SkeletonMaskElement:
    def __init__(self, reader):
        self.m_PathHash = reader.read_u_int()
        self.m_Weight = reader.read_float()


class SkeletonMask:
    def __init__(self, reader):
        numElements = reader.read_int()
        self.m_Data = [SkeletonMaskElement(reader) for _ in range(numElements)]


class LayerConstant:
    def __init__(self, reader):
        version = reader.version
        self.m_StateMachineIndex = reader.read_u_int()
        self.m_StateMachineMotionSetIndex = reader.read_u_int()
        self.m_BodyMask = HumanPoseMask(reader)
        self.m_SkeletonMask = SkeletonMask(reader)
        self.m_Binding = reader.read_u_int()
        self.m_LayerBlendingMode = reader.read_int()
        if version >= (4, 2):  # 4.2 and up
            self.m_DefaultWeight = reader.read_float()
        self.m_IKPass = reader.read_boolean()
        if version >= (4, 2):  # 4.2 and up
            self.m_SyncedLayerAffectsTiming = reader.read_boolean()
        reader.align_stream()


class ConditionConstant:
    def __init__(self, reader):
        self.m_ConditionMode = reader.read_u_int()
        self.m_EventID = reader.read_u_int()
        self.m_EventThreshold = reader.read_float()
        self.m_ExitTime = reader.read_float()


class TransitionConstant:
    def __init__(self, reader):
        version = reader.version

        numConditions = reader.read_int()
        self.m_ConditionConstantArray = [
            ConditionConstant(reader) for _ in range(numConditions)
        ]

        self.m_DestinationState = reader.read_u_int()
        if version >= (5,):  # 5.0 and up
            self.m_FullPathID = reader.read_u_int()

        self.m_ID = reader.read_u_int()
        self.m_UserID = reader.read_u_int()
        self.m_TransitionDuration = reader.read_float()
        self.m_TransitionOffset = reader.read_float()
        if version >= (5,):  # 5.0 and up
            self.m_ExitTime = reader.read_float()
            self.m_HasExitTime = reader.read_boolean()
            self.m_HasFixedDuration = reader.read_boolean()
            reader.align_stream()
            self.m_InterruptionSource = reader.read_int()
            self.m_OrderedInterruption = reader.read_boolean()
        else:
            self.m_Atomic = reader.read_boolean()

        if version >= (4, 5):  # 4.5 and up
            self.m_CanTransitionToSelf = reader.read_boolean()

        reader.align_stream()


class LeafInfoConstant:
    def __init__(self, reader):
        self.m_IDArray = reader.read_u_int_array()
        self.m_IndexOffset = reader.read_u_int()


class MotionNeighborList:
    def __init__(self, reader):
        self.m_NeighborArray = reader.read_u_int_array()


class Blend2dDataConstant:
    def __init__(self, reader):
        self.m_ChildPositionArray = reader.read_vector2_array()
        self.m_ChildMagnitudeArray = reader.read_float_array()
        self.m_ChildPairVectorArray = reader.read_vector2_array()
        self.m_ChildPairAvgMagInvArray = reader.read_float_array()

        numNeighbours = reader.read_int()
        self.m_ChildNeighborListArray = [
            MotionNeighborList(reader) for _ in range(numNeighbours)
        ]


class Blend1dDataConstant:  # wrong labeled:
    def __init__(self, reader):
        self.m_ChildThresholdArray = reader.read_float_array()


class BlendDirectDataConstant:
    def __init__(self, reader):
        self.m_ChildBlendEventIDArray = reader.read_u_int_array()
        self.m_NormalizedBlendValues = reader.read_boolean()
        reader.align_stream()


class BlendTreeNodeConstant:
    def __init__(self, reader):
        version = reader.version

        if version >= (4, 1):  # 4.1 and up
            self.m_BlendType = reader.read_u_int()
        self.m_BlendEventID = reader.read_u_int()
        if version >= (4, 1):  # 4.1 and up
            self.m_BlendEventYID = reader.read_u_int()
        self.m_ChildIndices = reader.read_u_int_array()
        if version < (4, 1):  # 4.1 down
            self.m_ChildThresholdArray = reader.read_float_array()

        if version >= (4, 1):  # 4.1 and up
            self.m_Blend1dData = Blend1dDataConstant(reader)
            self.m_Blend2dData = Blend2dDataConstant(reader)

        if version >= (5,):  # 5.0 and up
            self.m_BlendDirectData = BlendDirectDataConstant(reader)

        self.m_ClipID = reader.read_u_int()
        if (4, 5) <= version[:2] < (5, 0):  # 4.5 - 5.0
            self.m_ClipIndex = reader.read_u_int()

        self.m_Duration = reader.read_float()

        if version >= (4, 1, 3):  # 4.1.3 and up
            self.m_CycleOffset = reader.read_float()
            self.m_Mirror = reader.read_boolean()
            reader.align_stream()


class BlendTreeConstant:
    def __init__(self, reader):
        version = reader.version

        numNodes = reader.read_int()
        self.m_NodeArray = [BlendTreeNodeConstant(reader) for _ in range(numNodes)]

        if version < (4, 5):  # 4.5 down
            self.m_BlendEventArrayConstant = ValueArrayConstant(reader)


class StateConstant:
    def __init__(self, reader):
        version = reader.version

        numTransistions = reader.read_int()
        self.m_TransitionConstantArray = [
            TransitionConstant(reader) for _ in range(numTransistions)
        ]

        self.m_BlendTreeConstantIndexArray = reader.read_int_array()

        if version < (5, 2):  # 5.2 down
            numInfos = reader.read_int()
            self.m_LeafInfoArray = [LeafInfoConstant(reader) for _ in range(numInfos)]

        numBlends = reader.read_int()
        self.m_BlendTreeConstantArray = [
            BlendTreeConstant(reader) for _ in range(numBlends)
        ]

        self.m_NameID = reader.read_u_int()
        if version >= (4, 3):  # 4.3 and up
            self.m_PathID = reader.read_u_int()
        if version >= (5,):  # 5.0 and up
            self.m_FullPathID = reader.read_u_int()

        self.m_TagID = reader.read_u_int()
        if version >= (5, 1):  # 5.1 and up
            self.m_SpeedParamID = reader.read_u_int()
            self.m_MirrorParamID = reader.read_u_int()
            self.m_CycleOffsetParamID = reader.read_u_int()

        if version >= (2017, 2):  # 2017.2 and up
            self.m_TimeParamID = reader.read_u_int()

        self.m_Speed = reader.read_float()
        if version >= (4, 1):  # 4.1 and up
            self.m_CycleOffset = reader.read_float()
        self.m_IKOnFeet = reader.read_boolean()
        if version >= (5,):  # 5.0 and up
            self.m_WriteDefaultValues = reader.read_boolean()

        self.m_Loop = reader.read_boolean()
        if version >= (4, 1):  # 4.1 and up
            self.m_Mirror = reader.read_boolean()

        reader.align_stream()


class SelectorTransitionConstant:
    def __init__(self, reader):
        self.m_Destination = reader.read_u_int()

        numConditions = reader.read_int()
        self.m_ConditionConstantArray = [
            ConditionConstant(reader) for _ in range(numConditions)
        ]


class SelectorStateConstant:
    def __init__(self, reader):
        numTransitions = reader.read_int()
        self.m_TransitionConstantArray = [
            SelectorTransitionConstant(reader) for _ in range(numTransitions)
        ]
        self.m_FullPathID = reader.read_u_int()
        self.m_isEntry = reader.read_boolean()
        reader.align_stream()


class StateMachineConstant:
    def __init__(self, reader):
        version = reader.version

        numStates = reader.read_int()
        self.m_StateConstantArray = [StateConstant(reader) for _ in range(numStates)]

        numAnyStates = reader.read_int()
        self.m_AnyStateTransitionConstantArray = [
            TransitionConstant(reader) for _ in range(numAnyStates)
        ]

        if version >= (5,):  # 5.0 and up
            numSelectors = reader.read_int()
            self.m_SelectorStateConstantArray = [
                SelectorStateConstant(reader) for _ in range(numSelectors)
            ]

        self.m_DefaultState = reader.read_u_int()
        self.m_MotionSetCount = reader.read_u_int()


class ValueArray:
    def __init__(self, reader):
        version = reader.version

        if version < (5, 5):  # 5.5 down
            self.m_BoolValues = reader.read_boolean_array()
            reader.align_stream()
            self.m_IntValues = reader.read_int_array()
            self.m_FloatValues = reader.read_float_array()

        if version < (4, 3):  # 4.3 down
            self.m_VectorValues = reader.read_vector4_array()
        else:
            numPosValues = reader.read_int()
            self.m_PositionValues = [
                reader.read_vector3()
                if version >= (5, 4)
                else Vector3(reader.read_vector4())  # 5.4 and up
                for _ in range(numPosValues)
            ]

            self.m_QuaternionValues = reader.read_vector4_array()

            numScaleValues = reader.read_int()
            self.m_ScaleValues = [
                reader.read_vector3()
                if version >= (5, 4)
                else Vector3(reader.read_vector4())  # 5.4 and up
                for _ in range(numScaleValues)
            ]

            if version >= (5, 5):  # 5.5 and up
                self.m_FloatValues = reader.read_float_array()
                self.m_IntValues = reader.read_int_array()
                self.m_BoolValues = reader.read_boolean_array()
                reader.align_stream()


class ControllerConstant:
    def __init__(self, reader):
        numLayers = reader.read_int()
        self.m_LayerArray = [LayerConstant(reader) for _ in range(numLayers)]

        numStates = reader.read_int()
        self.m_StateMachineArray = [
            StateMachineConstant(reader) for _ in range(numStates)
        ]

        self.m_Values = ValueArrayConstant(reader)
        self.m_DefaultValues = ValueArray(reader)
