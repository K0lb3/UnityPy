from .helper import *


class Il2CppGlobalMetadataHeader(MetaDataClass):
    sanity: uint
    version: int
    stringLiteralOffset: uint  # string data for managed code
    stringLiteralCount: int
    stringLiteralDataOffset: uint
    stringLiteralDataCount: int
    stringOffset: uint  # string data for metadata
    stringCount: int
    eventsOffset: uint  # Il2CppEventDefinition
    eventsCount: int
    propertiesOffset: uint  # Il2CppPropertyDefinition
    propertiesCount: int
    methodsOffset: uint  # Il2CppMethodDefinition
    methodsCount: int
    parameterDefaultValuesOffset: uint  # Il2CppParameterDefaultValue
    parameterDefaultValuesCount: int
    fieldDefaultValuesOffset: uint  # Il2CppFieldDefaultValue
    fieldDefaultValuesCount: int
    fieldAndParameterDefaultValueDataOffset: uint  # uint8_t
    fieldAndParameterDefaultValueDataCount: int
    fieldMarshaledSizesOffset: int  # Il2CppFieldMarshaledSize
    fieldMarshaledSizesCount: int
    parametersOffset: uint  # Il2CppParameterDefinition
    parametersCount: int
    fieldsOffset: uint  # Il2CppFieldDefinition
    fieldsCount: int
    genericParametersOffset: uint  # Il2CppGenericParameter
    genericParametersCount: int
    genericParameterConstraintsOffset: uint  # TypeIndex
    genericParameterConstraintsCount: int
    genericContainersOffset: uint  # Il2CppGenericContainer
    genericContainersCount: int
    nestedTypesOffset: uint  # TypeDefinitionIndex
    nestedTypesCount: int
    interfacesOffset: uint  # TypeIndex
    interfacesCount: int
    vtableMethodsOffset: uint  # EncodedMethodIndex
    vtableMethodsCount: int
    interfaceOffsetsOffset: int  # Il2CppInterfaceOffsetPair
    interfaceOffsetsCount: int
    typeDefinitionsOffset: uint  # Il2CppTypeDefinition
    typeDefinitionsCount: int
    rgctxEntriesOffset: Union[uint, Version(Max=24.1)]  # Il2CppRGCTXDefinition
    rgctxEntriesCount: Union[int, Version(Max=24.1)]
    imagesOffset: uint  # Il2CppImageDefinition
    imagesCount: int
    assembliesOffset: int  # Il2CppAssemblyDefinition
    assembliesCount: int
    metadataUsageListsOffset: Union[
        uint, Version(Min=19, Max=24.4)
    ]  # Il2CppMetadataUsageList
    metadataUsageListsCount: Union[int, Version(Min=19, Max=24.4)]
    metadataUsagePairsOffset: Union[
        uint, Version(Min=19, Max=24.4)
    ]  # Il2CppMetadataUsagePair
    metadataUsagePairsCount: Union[int, Version(Min=19, Max=24.4)]
    fieldRefsOffset: Union[uint, Version(Min=19)]  # Il2CppFieldRef
    fieldRefsCount: Union[int, Version(Min=19)]
    referencedAssembliesOffset: Union[int, Version(Min=20)]  # int32_t
    referencedAssembliesCount: Union[int, Version(Min=20)]
    attributesInfoOffset: Union[uint, Version(Min=21)]  # Il2CppCustomAttributeTypeRange
    attributesInfoCount: Union[int, Version(Min=21)]
    attributeTypesOffset: Union[uint, Version(Min=21)]  # TypeIndex
    attributeTypesCount: Union[int, Version(Min=21)]
    unresolvedVirtualCallParameterTypesOffset: Union[int, Version(Min=22)]  # TypeIndex
    unresolvedVirtualCallParameterTypesCount: Union[int, Version(Min=22)]
    unresolvedVirtualCallParameterRangesOffset: Union[
        int, Version(Min=22)
    ]  # Il2CppRange
    unresolvedVirtualCallParameterRangesCount: Union[int, Version(Min=22)]
    windowsRuntimeTypeNamesOffset: Union[
        int, Version(Min=23)
    ]  # Il2CppWindowsRuntimeTypeNamePair
    windowsRuntimeTypeNamesSize: Union[int, Version(Min=23)]
    windowsRuntimeStringsOffset: Union[int, Version(Min=27)]  # const char*
    windowsRuntimeStringsSize: Union[int, Version(Min=27)]
    exportedTypeDefinitionsOffset: Union[int, Version(Min=24)]  # TypeDefinitionIndex
    exportedTypeDefinitionsCount: Union[int, Version(Min=24)]


class Il2CppImageDefinition(MetaDataClass):
    nameIndex: uint
    assemblyIndex: int

    typeStart: int
    typeCount: uint

    exportedTypeStart: Union[int, Version(Min=24)]
    exportedTypeCount: Union[uint, Version(Min=24)]

    entryPointIndex: int
    token: Union[uint, Version(Min=19)]

    customAttributeStart: Union[int, Version(Min=24.1)]
    customAttributeCount: Union[uint, Version(Min=24.1)]


class Il2CppTypeDefinition(MetaDataClass):
    nameIndex: uint
    namespaceIndex: uint
    customAttributeIndex: Union[int, Version(Max=24)]
    byvalTypeIndex: int
    byrefTypeIndex: Union[int, Version(Max=24.4)]

    declaringTypeIndex: int
    parentIndex: int
    elementTypeIndex: int  # we can probably remove this one. Only used for enums

    rgctxStartIndex: Union[int, Version(Max=24.1)]
    rgctxCount: Union[int, Version(Max=24.1)]

    genericContainerIndex: int

    delegateWrapperFromManagedToNativeIndex: Union[int, Version(Max=22)]
    marshalingFunctionsIndex: Union[int, Version(Max=22)]
    ccwFunctionIndex: Union[int, Version(Min=21, Max=22)]
    guidIndex: Union[int, Version(Min=21, Max=22)]

    flags: uint

    fieldStart: int
    methodStart: int
    eventStart: int
    propertyStart: int
    nestedTypesStart: int
    interfacesStart: int
    vtableStart: int
    interfaceOffsetsStart: int

    method_count: ushort
    property_count: ushort
    field_count: ushort
    event_count: ushort
    nested_type_count: ushort
    vtable_count: ushort
    interfaces_count: ushort
    interface_offsets_count: ushort

    # bitfield to portably encode boolean values as single bits
    # 01 - valuetype;
    # 02 - enumtype;
    # 03 - has_finalize;
    # 04 - has_cctor;
    # 05 - is_blittable;
    # 06 - is_import_or_windows_runtime;
    # 07-10 - One of nine possible PackingSize values (0, 1, 2, 4, 8, 16, 32, 64, or 128)
    # 11 - PackingSize is default
    # 12 - ClassSize is default
    # 13-16 - One of nine possible PackingSize values (0, 1, 2, 4, 8, 16, 32, 64, or 128) - the specified packing size (even for explicit layouts)
    bitfield: uint
    token: Union[uint, Version(Min=19)]

    @property
    def IsValueType(self) -> bool:
        return (self.bitfield & 0x1) == 1

    @property
    def IsEnum(self) -> bool:
        return ((self.bitfield >> 1) & 0x1) == 1


class Il2CppMethodDefinition(MetaDataClass):
    nameIndex: uint
    declaringType: int
    returnType: int
    parameterStart: int
    customAttributeIndex: Union[int, Version(Max=24)]
    genericContainerIndex: int
    methodIndex: Union[int, Version(Max=24.1)]
    invokerIndex: Union[int, Version(Max=24.1)]
    delegateWrapperIndex: Union[int, Version(Max=24.1)]
    rgctxStartIndex: Union[int, Version(Max=24.1)]
    rgctxCount: Union[int, Version(Max=24.1)]
    token: uint
    flags: ushort
    iflags: ushort
    slot: ushort
    parameterCount: ushort


class Il2CppParameterDefinition(MetaDataClass):
    nameIndex: uint
    token: uint
    customAttributeIndex: Union[int, Version(Max=24)]
    typeIndex: int


class Il2CppFieldDefinition(MetaDataClass):
    nameIndex: uint
    typeIndex: int
    customAttributeIndex: Union[int, Version(Max=24)]
    token: Union[uint, Version(Min=19)]


class Il2CppFieldDefaultValue(MetaDataClass):
    fieldIndex: int
    typeIndex: int
    dataIndex: int


class Il2CppPropertyDefinition(MetaDataClass):
    nameIndex: uint
    get: int
    set: int
    attrs: uint
    customAttributeIndex: Union[int, Version(Max=24)]
    token: Union[uint, Version(Min=19)]


class Il2CppCustomAttributeTypeRange(MetaDataClass):
    token: Union[uint, Version(Min=24.1)]
    start: int
    count: int


class Il2CppMetadataUsageList(MetaDataClass):
    start: uint
    count: uint


class Il2CppMetadataUsagePair(MetaDataClass):
    destinationIndex: uint
    encodedSourceIndex: uint


class Il2CppStringLiteral(MetaDataClass):
    length: uint
    dataIndex: int


class Il2CppParameterDefaultValue(MetaDataClass):
    parameterIndex: int
    typeIndex: int
    dataIndex: int


class Il2CppEventDefinition(MetaDataClass):
    nameIndex: uint
    typeIndex: int
    add: int
    remove: int
    rais: int
    customAttributeIndex: Union[int, Version(Max=24)]
    token: Union[uint, Version(Min=19)]


class Il2CppGenericContainer(MetaDataClass):
    # index of the generic type definition or the generic method definition corresponding to this container
    ownerIndex: int  # either index into Il2CppClass metadata array or Il2CppMethodDefinition array
    type_argc: int
    # If true, we're a generic method, otherwise a generic type definition.
    is_method: int
    # Our type parameters.
    genericParameterStart: int


class Il2CppFieldRef(MetaDataClass):
    typeIndex: int
    fieldIndex: int  # local offset into type fields


class Il2CppGenericParameter(MetaDataClass):
    ownerIndex: int  # Type or method this parameter was defined in.
    nameIndex: uint
    constraintsStart: short
    constraintsCount: short
    num: ushort
    flags: ushort


class Il2CppRGCTXDataType(uint, Enum):
    IL2CPP_RGCTX_DATA_INVALID = 0
    IL2CPP_RGCTX_DATA_TYPE = 1
    IL2CPP_RGCTX_DATA_CLASS = 2
    IL2CPP_RGCTX_DATA_METHOD = 3
    IL2CPP_RGCTX_DATA_ARRAY = 4


class Il2CppRGCTXDefinitionData(MetaDataClass):
    rgctxDataDummy: int

    @property
    def methodIndex(self) -> int:
        return self.rgctxDataDummy

    @property
    def typeIndex(self) -> int:
        return self.rgctxDataDummy


class Il2CppRGCTXDefinition:
    type: Il2CppRGCTXDataType
    data: Il2CppRGCTXDefinitionData

    version: float
    size: int
    parseString: str

    def __init__(self, reader: BinaryIO = None) -> None:
        if not (self.version):
            raise NotImplementedError(
                "Using an unversioned MetaDataClass isn't possible."
            )
        if reader:
            self.read_from(reader)

    def read_from(self, reader: BytesIO):
        self.type = Il2CppRGCTXDataType.read_from(reader)
        self.data = Il2CppRGCTXDefinitionData.generate_versioned_subclass(self.version)(
            reader
        )

    def write_to(self, writer: BytesIO):
        self.type = self.data.write_to(writer)
        self.data.write_to(writer)

    @classmethod
    def generate_versioned_subclass(cls, version: float):
        cls.version = version
        cls.size = 8  # TODO if data changes
        return cls
