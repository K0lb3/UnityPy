from .helper import *


class Il2CppCodeRegistration(MetaDataClass):
    methodPointersCount: Union[long, Version(Max=24.1)]
    methodPointers: Union[ulong, Version(Max=24.1)]
    delegateWrappersFromNativeToManagedCount: Union[ulong, Version(Max=21)]
    delegateWrappersFromNativeToManaged: Union[
        ulong, Version(Max=21)
    ]  # note the double indirection to handle different calling conventions
    reversePInvokeWrapperCount: Union[long, Version(Min=22)]
    reversePInvokeWrappers: Union[ulong, Version(Min=22)]
    delegateWrappersFromManagedToNativeCount: Union[ulong, Version(Max=22)]
    delegateWrappersFromManagedToNative: Union[ulong, Version(Max=22)]
    marshalingFunctionsCount: Union[ulong, Version(Max=22)]
    marshalingFunctions: Union[ulong, Version(Max=22)]
    ccwMarshalingFunctionsCount: Union[ulong, Version(Min=21, Max=22)]
    ccwMarshalingFunctions: Union[ulong, Version(Min=21, Max=22)]
    genericMethodPointersCount: long
    genericMethodPointers: ulong
    genericAdjustorThunks: Union[ulong, Version(Min=24.4, Max=24.4), Version(Min=27.1)]
    invokerPointersCount: long
    invokerPointers: ulong
    customAttributeCount: Union[long, Version(Max=24.4)]
    customAttributeGenerators: Union[ulong, Version(Max=24.4)]
    guidCount: Union[long, Version(Min=21, Max=22)]
    guids: Union[ulong, Version(Min=21, Max=22)]  # Il2CppGuid
    unresolvedVirtualCallCount: Union[long, Version(Min=22)]
    unresolvedVirtualCallPointers: Union[ulong, Version(Min=22)]
    interopDataCount: Union[ulong, Version(Min=23)]
    interopData: Union[ulong, Version(Min=23)]
    windowsRuntimeFactoryCount: Union[ulong, Version(Min=24.3)]
    windowsRuntimeFactoryTable: Union[ulong, Version(Min=24.3)]
    codeGenModulesCount: Union[long, Version(Min=24.2)]
    codeGenModules: Union[ulong, Version(Min=24.2)]


class Il2CppMetadataRegistration(MetaDataClass):
    genericClassesCount: long
    genericClasses: ulong
    genericInstsCount: long
    genericInsts: ulong
    genericMethodTableCount: long
    genericMethodTable: ulong
    typesCount: long
    types: ulong
    methodSpecsCount: long
    methodSpecs: ulong
    methodReferencesCount: Union[long, Version(Max=16)]
    methodReferences: Union[ulong, Version(Max=16)]

    fieldOffsetsCount: long
    fieldOffsets: ulong

    typeDefinitionsSizesCount: long
    typeDefinitionsSizes: ulong
    metadataUsagesCount: Union[ulong, Version(Min=19)]
    metadataUsages: Union[ulong, Version(Min=19)]


class Il2CppTypeEnum(uint, Enum):
    IL2CPP_TYPE_END = 0x00  # End of List
    IL2CPP_TYPE_VOID = 0x01
    IL2CPP_TYPE_BOOLEAN = 0x02
    IL2CPP_TYPE_CHAR = 0x03
    IL2CPP_TYPE_I1 = 0x04
    IL2CPP_TYPE_U1 = 0x05
    IL2CPP_TYPE_I2 = 0x06
    IL2CPP_TYPE_U2 = 0x07
    IL2CPP_TYPE_I4 = 0x08
    IL2CPP_TYPE_U4 = 0x09
    IL2CPP_TYPE_I8 = 0x0A
    IL2CPP_TYPE_U8 = 0x0B
    IL2CPP_TYPE_R4 = 0x0C
    IL2CPP_TYPE_R8 = 0x0D
    IL2CPP_TYPE_STRING = 0x0E
    IL2CPP_TYPE_PTR = 0x0F  # arg: <type> token
    IL2CPP_TYPE_BYREF = 0x10  # arg: <type> token
    IL2CPP_TYPE_VALUETYPE = 0x11  # arg: <type> token
    IL2CPP_TYPE_CLASS = 0x12  # arg: <type> token
    IL2CPP_TYPE_VAR = 0x13  # Generic parameter in a generic type definition, represented as number (compressed unsigned integer) number
    IL2CPP_TYPE_ARRAY = 0x14  # type, rank, boundsCount, bound1, loCount, lo1
    IL2CPP_TYPE_GENERICINST = 0x15  # <type> <type-arg-count> <type-1> \x{2026} <type-n>
    IL2CPP_TYPE_TYPEDBYREF = 0x16
    IL2CPP_TYPE_I = 0x18
    IL2CPP_TYPE_U = 0x19
    IL2CPP_TYPE_FNPTR = 0x1B  # arg: full method signature
    IL2CPP_TYPE_OBJECT = 0x1C
    IL2CPP_TYPE_SZARRAY = 0x1D  # 0-based one-dim-array
    IL2CPP_TYPE_MVAR = 0x1E  # Generic parameter in a generic method definition, represented as number (compressed unsigned integer)
    IL2CPP_TYPE_CMOD_REQD = 0x1F  # arg: typedef or typeref token
    IL2CPP_TYPE_CMOD_OPT = 0x20  # optional arg: typedef or typref token
    IL2CPP_TYPE_INTERNAL = 0x21  # CLR internal type

    IL2CPP_TYPE_MODIFIER = 0x40  # Or with the following types
    IL2CPP_TYPE_SENTINEL = 0x41  # Sentinel for varargs method signature
    IL2CPP_TYPE_PINNED = 0x45  # Local var that points to pinned object

    IL2CPP_TYPE_ENUM = 0x55  # an enumeration


# class Il2CppType(MetaDataClass):
#     datapoint: ulong
#     bits: uint
#     data { get: Union set; }
#     attrs { get: uint set; }
#     type { get: Il2CppTypeEnum set; }
#     num_mods { get: uint set; }
#     byref { get: uint set; }
#     pinned { get: uint set; }

#     public void Init()
#     {
#         attrs = bits & 0xffff;
#         type = (Il2CppTypeEnum)((bits >> 16) & 0xff);
#         num_mods = (bits >> 24) & 0x3f;
#         byref = (bits >> 30) & 1;
#         pinned = bits >> 31;
#         data = new Union { dummy = datapoint };
#     }

#     public class Union
#     {
#         dummy: ulong
#         #/ <summary>
#         #/ for VALUETYPE and CLASS
#         #/ </summary>
#         klassIndex => (long)dummy: long
#         #/ <summary>
#         #/ for VALUETYPE and CLASS at runtime
#         #/ </summary>
#         typeHandle => dummy: ulong
#         #/ <summary>
#         #/ for PTR and SZARRAY
#         #/ </summary>
#         type => dummy: ulong
#         #/ <summary>
#         #/ for ARRAY
#         #/ </summary>
#         array => dummy: ulong
#         #/ <summary>
#         #/ for VAR and MVAR
#         #/ </summary>
#         genericParameterIndex => (long)dummy: long
#         #/ <summary>
#         #/ for VAR and MVAR at runtime
#         #/ </summary>
#         genericParameterHandle => dummy: ulong
#         #/ <summary>
#         #/ for GENERICINST
#         #/ </summary>
#         generic_class => dummy: ulong
#     }
# }


class Il2CppGenericContext(MetaDataClass):
    # The instantiation corresponding to the class generic parameters
    class_inst: ulong
    # The instantiation corresponding to the method generic parameters
    method_inst: ulong


class Il2CppGenericClass(MetaDataClass):
    typeDefinitionIndex: Union[long, Version(Max=24.4)]  # the generic type definition
    type: Union[ulong, Version(Min=27)]  # the generic type definition
    context: Il2CppGenericContext  # a context that contains the type instantiation doesn't contain any method instantiation
    cached_class: ulong  # if present, the Il2CppClass corresponding to the instantiation.


class Il2CppGenericInst(MetaDataClass):
    type_argc: long
    type_argv: ulong


class Il2CppArrayType(MetaDataClass):
    etype: ulong
    rank: byte
    numsizes: byte
    numlobounds: byte
    sizes: ulong
    lobounds: ulong


class Il2CppGenericMethodIndices(MetaDataClass):
    methodIndex: int
    invokerIndex: int
    adjustorThunk: Union[int, Version(Min=24.4, Max=24.4), Version(Min=27.1)]


class Il2CppGenericMethodFunctionsDefinitions(MetaDataClass):
    genericMethodIndex: int
    indices: Il2CppGenericMethodIndices


class Il2CppMethodSpec(MetaDataClass):
    methodDefinitionIndex: int
    classIndexIndex: int
    methodIndexIndex: int


class Il2CppCodeGenModule(MetaDataClass):
    moduleName: ulong
    methodPointerCount: long
    methodPointers: ulong
    adjustorThunkCount: Union[long, Version(Min=24.4, Max=24.4), Version(Min=27.1)]
    adjustorThunks: Union[ulong, Version(Min=24.4, Max=24.4), Version(Min=27.1)]
    invokerIndices: ulong
    reversePInvokeWrapperCount: ulong
    reversePInvokeWrapperIndices: ulong
    rgctxRangesCount: long
    rgctxRanges: ulong
    rgctxsCount: long
    rgctxs: ulong
    debuggerMetadata: ulong
    customAttributeCacheGenerator: Union[ulong, Version(Min=27)]
    moduleInitializer: Union[ulong, Version(Min=27)]
    staticConstructorTypeIndices: Union[ulong, Version(Min=27)]
    metadataRegistration: Union[ulong, Version(Min=27)]  # Per-assembly mode only
    codeRegistaration: Union[ulong, Version(Min=27)]  # Per-assembly mode only


class Il2CppRange(MetaDataClass):
    start: int
    length: int


class Il2CppTokenRangePair(MetaDataClass):
    token: uint
    range: Il2CppRange
