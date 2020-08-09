from .EditorExtension import EditorExtension
from .PPtr import PPtr


class GameObject(EditorExtension):
    """
    public PPtr<Component>[] m_Components;
    public string m_Name;
    public Transform m_Transform;
    public MeshRenderer m_MeshRenderer;
    public MeshFilter m_MeshFilter;
    public SkinnedMeshRenderer m_SkinnedMeshRenderer;
    public Animator m_Animator;
    public Animation m_Animation;
    """

    def __init__(self, reader):
        super().__init__(reader=reader)
        component_size = reader.read_int()
        self.components = []
        for i in range(component_size):
            if self.version < (5, 5):
                first = reader.read_int()
            self.components.append(PPtr(reader))
        self.layer = reader.read_int()
        self.name = reader.read_aligned_string()
