from .metadata_class import *
from typing import List, Dict
from collections import OrderedDict


class Metadata:
    header: Il2CppGlobalMetadataHeader
    imageDefs: List[Il2CppImageDefinition]
    typeDefs: List[Il2CppTypeDefinition]
    methodDefs: List[Il2CppMethodDefinition]
    parameterDefs: List[Il2CppParameterDefinition]
    fieldDefs: List[Il2CppFieldDefinition]
    fieldDefaultValuesDic: Dict[int, Il2CppFieldDefaultValue]
    parameterDefaultValuesDic: Dict[int, Il2CppParameterDefaultValue]
    propertyDefs: List[Il2CppPropertyDefinition]
    attributeTypeRanges: List[Il2CppCustomAttributeTypeRange]
    attributeTypeRangesDic: Dict[Il2CppImageDefinition, Dict[uint, int]]
    stringLiterals: List[Il2CppStringLiteral]
    metadataUsageLists: List[Il2CppMetadataUsageList]
    metadataUsagePairs: List[Il2CppMetadataUsagePair]
    attributeTypes: List[int]
    interfaceIndices: List[int]
    metadataUsageDic: Dict[uint, OrderedDict[uint, uint]]
    maxMetadataUsages: int  # long
    nestedTypeIndices: List[int]
    eventDefs: List[Il2CppEventDefinition]
    genericContainers: List[Il2CppGenericContainer]
    fieldRefs: List[Il2CppFieldRef]
    genericParameters: List[Il2CppGenericParameter]
    constraintIndices: List[int]
    vtableMethods: List[uint]
    rgctxEntries: List[Il2CppRGCTXDefinition]

    stringCache: Dict[uint, str]
    Address: int  # ulong

    version: int
    Version: float

    def __init__(self, stream: BytesIO):
        self.reader = stream
        self.stringCache = {}

        sanity = uint.read_from(stream)
        if sanity != 0xFAB11BAF:
            raise ValueError(
                "ERROR: Metadata file supplied is not valid metadata file."
            )
        self.version = version = int.read_from(stream)
        if version < 16 or version > 27:
            raise NotImplementedError(
                f"ERROR: Metadata file supplied is not a supported version[{version}]."
            )

        self.Version = Version = float(version)
        self.header = header = self.ReadClass(Il2CppGlobalMetadataHeader, 0)
        if version == 24:
            if header.stringLiteralOffset == 264:
                self.Version = Version = 24.2
                self.header = header = self.ReadClass(Il2CppGlobalMetadataHeader, 0)
            else:
                self.imageDefs = imageDefs = self.ReadMetadataClassArray(
                    Il2CppImageDefinition, header.imagesOffset, header.imagesCount
                )
                if any(x.token != 1 for x in imageDefs):
                    self.Version = Version = 24.1

        self.imageDefs = imageDefs = self.ReadMetadataClassArray(
            Il2CppImageDefinition, header.imagesOffset, header.imagesCount
        )
        self.typeDefs = self.ReadMetadataClassArray(
            Il2CppTypeDefinition,
            header.typeDefinitionsOffset,
            header.typeDefinitionsCount,
        )
        self.methodDefs = self.ReadMetadataClassArray(
            Il2CppMethodDefinition, header.methodsOffset, header.methodsCount
        )
        self.parameterDefs = self.ReadMetadataClassArray(
            Il2CppParameterDefinition, header.parametersOffset, header.parametersCount
        )
        self.fieldDefs = self.ReadMetadataClassArray(
            Il2CppFieldDefinition, header.fieldsOffset, header.fieldsCount
        )
        self.fieldDefaultValues = self.ReadMetadataClassArray(
            Il2CppFieldDefaultValue,
            header.fieldDefaultValuesOffset,
            header.fieldDefaultValuesCount,
        )
        self.parameterDefaultValues = self.ReadMetadataClassArray(
            Il2CppParameterDefaultValue,
            header.parameterDefaultValuesOffset,
            header.parameterDefaultValuesCount,
        )
        self.fieldDefaultValuesDic = {x.fieldIndex: x for x in self.fieldDefaultValues}
        self.parameterDefaultValuesDic = {
            x.parameterIndex: x for x in self.parameterDefaultValues
        }
        self.propertyDefs = self.ReadMetadataClassArray(
            Il2CppPropertyDefinition, header.propertiesOffset, header.propertiesCount
        )
        self.interfaceIndices = self.ReadClassArray(
            int, header.interfacesOffset, header.interfacesCount // 4
        )
        self.nestedTypeIndices = self.ReadClassArray(
            int, header.nestedTypesOffset, header.nestedTypesCount // 4
        )
        self.eventDefs = self.ReadMetadataClassArray(
            Il2CppEventDefinition, header.eventsOffset, header.eventsCount
        )
        self.genericContainers = self.ReadMetadataClassArray(
            Il2CppGenericContainer,
            header.genericContainersOffset,
            header.genericContainersCount,
        )
        self.genericParameters = self.ReadMetadataClassArray(
            Il2CppGenericParameter,
            header.genericParametersOffset,
            header.genericParametersCount,
        )
        self.constraintIndices = self.ReadClassArray(
            int,
            header.genericParameterConstraintsOffset,
            header.genericParameterConstraintsCount // 4,
        )
        self.vtableMethods = self.ReadClassArray(
            uint, header.vtableMethodsOffset, header.vtableMethodsCount // 4
        )
        if 16 < Version < 27:  # TODO
            self.stringLiterals = self.ReadMetadataClassArray(
                Il2CppStringLiteral,
                header.stringLiteralOffset,
                header.stringLiteralCount,
            )
            self.metadataUsageLists = self.ReadMetadataClassArray(
                Il2CppMetadataUsageList,
                header.metadataUsageListsOffset,
                header.metadataUsageListsCount,
            )
            self.metadataUsagePairs = self.ReadMetadataClassArray(
                Il2CppMetadataUsagePair,
                header.metadataUsagePairsOffset,
                header.metadataUsagePairsCount,
            )

            self.ProcessingMetadataUsage()

            self.fieldRefs = self.ReadMetadataClassArray(
                Il2CppFieldRef, header.fieldRefsOffset, header.fieldRefsCount
            )

        if Version > 20:
            self.attributeTypeRanges = self.ReadMetadataClassArray(
                Il2CppCustomAttributeTypeRange,
                header.attributesInfoOffset,
                header.attributesInfoCount,
            )
            self.attributeTypes = self.ReadClassArray(
                int, header.attributeTypesOffset, header.attributeTypesCount // 4
            )

        if Version >= 24.1:
            self.attributeTypeRangesDic = attributeTypeRangesDic = {}
            for imageDef in imageDefs:
                dic = {}
                attributeTypeRangesDic[imageDef] = dic
                end = imageDef.customAttributeStart + imageDef.customAttributeCount
                for i in range(imageDef.customAttributeStart, end):
                    dic[self.attributeTypeRanges[i].token] = i

        if Version <= 24.1:
            self.rgctxEntries = self.ReadMetadataClassArray(
                Il2CppRGCTXDefinition,
                header.rgctxEntriesOffset,
                header.rgctxEntriesCount,
            )

    def ReadClass(self, clz: MetaDataClass, addr: int) -> List[MetaDataClass]:
        self.reader.seek(addr)
        return clz.generate_versioned_subclass(self.Version)(self.reader)

    def ReadClassArray(
        self,
        clz: Union[MetaDataClass, CustomIntWrapper, Il2CppRGCTXDefinition],
        addr: int,
        count: int,
    ) -> List[MetaDataClass]:
        self.reader.seek(addr)
        if issubclass(clz, (MetaDataClass, Il2CppRGCTXDefinition)):
            return [clz(self.reader) for _ in range(count)]
        elif issubclass(clz, CustomIntWrapper):
            return [clz.read_from(self.reader) for _ in range(count)]
        elif clz == Il2CppRGCTXDefinition:
            return [clz.read_from(self.reader) for _ in range(count)]
        else:
            raise ValueError("Invalid clz type")

    def ReadMetadataClassArray(
        self, clz: MetaDataClass, addr: int, count: int
    ) -> List[MetaDataClass]:
        clz = clz.generate_versioned_subclass(self.Version)
        return self.ReadClassArray(clz, addr, count // clz.size)

    def GetFieldDefaultValueFromIndex(self, index: int) -> Il2CppFieldDefaultValue:
        return self.fieldDefaultValuesDic.get(index, None)

    def GetParameterDefaultValueFromIndex(
        self, index: int
    ) -> Il2CppParameterDefaultValue:
        return self.parameterDefaultValuesDic.get(index, None)

    def GetDefaultValueFromIndex(self, index: int) -> int:
        return self.header.fieldAndParameterDefaultValueDataOffset + index

    def GetStringFromIndex(self, index: int) -> str:
        result = self.stringCache.get(index, None)
        if result == None:
            result = self.ReadStringToNull(self.header.stringOffset + index)
            self.stringCache[index] = result
        return result

    # public int GetCustomAttributeIndex(Il2CppImageDefinition imageDef, int customAttributeIndex, uint token)
    # {
    #     if (Version > 24)
    #     {
    #         if (attributeTypeRangesDic[imageDef].TryGetValue(token, out var index))
    #         {
    #             return index
    #         }
    #         else
    #         {
    #             return -1
    #         }
    #     }
    #     else
    #     {
    #         return customAttributeIndex
    #     }
    # }

    def GetStringLiteralFromIndex(self, index: int) -> str:
        stringLiteral = self.stringLiterals[index]
        self.reader.seek(self.header.stringLiteralDataOffset + stringLiteral.dataIndex)
        return self.reader.read(stringLiteral.Length).encode("utf8")

    def GetStringLiterals(self):
        return [self.GetDecodedMethodIndex(i) for i in range(len(self.stringLiterals))]

    def ProcessingMetadataUsage(self):
        self.metadataUsageDic = metadataUsageDic = {
            i: OrderedDict() for i in range(1, 7)
        }
        for metadataUsageList in self.metadataUsageLists:
            for i in range(metadataUsageList.count):
                offset = metadataUsageList.start + i
                metadataUsagePair = self.metadataUsagePairs[offset]
                usage = self.GetEncodedIndexType(metadataUsagePair.encodedSourceIndex)
                decodedIndex = self.GetDecodedMethodIndex(
                    metadataUsagePair.encodedSourceIndex
                )
                metadataUsageDic[usage][
                    metadataUsagePair.destinationIndex
                ] = decodedIndex

        self.maxMetadataUsages = (
            max(y for x in metadataUsageDic.values() for y in x.keys()) + 1
        )

    def GetEncodedIndexType(self, index: int) -> int:
        return (index & 0xE0000000) >> 29

    def GetDecodedMethodIndex(self, index: int):
        if self.Version >= 27:
            return (index & 0x1FFFFFFE) >> 1
        return index & 0x1FFFFFFF

    def SizeOf(typ) -> int:
        return typ.size

    def ReadString(self, numChars: int) -> str:
        start = self.reader.tell()
        # UTF8 takes up to 4 bytes per character
        string = self.reader.read(numChars * 4).encode("utf8")[:numChars]
        # make our position what it would have been if we'd known the exact number of bytes needed.
        self.reader.seek(start)
        self.reader.read(len(string.encode("utf8")))
        return string

    def ReadStringToNull(self, offset: int) -> str:
        read_one = lambda: self.reader.read(1)
        start = self.reader.seek(offset)
        c = b"\x00"
        ret = []
        while c == b"\x00":
            c = read_one()
            ret.append(c)
        return b"".join(ret).encode("utf8")
