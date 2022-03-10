from tkinter.messagebox import NO
from .EditorExtension import EditorExtension
from .PPtr import PPtr
from ..enums import ClassIDType


class GameObject(EditorExtension):
    m_Components: list
    m_Layer: int
    name: str
    m_Animator: PPtr
    m_Animation: PPtr
    m_Transform: PPtr
    m_MeshRenderer: PPtr
    m_SkinnedMeshRender: PPtr
    m_MeshFilter: PPtr

    def __init__(self, reader):
        super().__init__(reader=reader)

        self.m_Animator = None
        self.m_Animation = None
        self.m_Transform = None
        self.m_MeshRenderer = None
        self.m_SkinnedMeshRenderer = None
        self.m_MeshFilter = None

        component_size = reader.read_int()

        self.m_Components = [None] * component_size
        for i in range(component_size):
            if self.version < (5, 5):
                first = reader.read_int()
            component = PPtr(reader)
            self.m_Components[i] = component

            if component.type == ClassIDType.Animator:
                self.m_Animator = component
            elif component.type == ClassIDType.Animation:
                self.m_Animation = component
            elif component.type == ClassIDType.Transform:
                self.m_Transform = component
            elif component.type == ClassIDType.MeshRenderer:
                self.m_MeshRenderer = component
            elif component.type == ClassIDType.SkinnedMeshRenderer:
                self.m_SkinnedMeshRenderer = component
            elif component.type == ClassIDType.MeshFilter:
                self.m_MeshFilter = component

        self.m_Layer = reader.read_int()
        self.name = reader.read_aligned_string()
