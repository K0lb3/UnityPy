# Change Log

## 1.20

- overall type-hint improvements
- **UnityPy.classes**
  - replace hard-coded UnityPy.classes with generated class stubs
    - UnityPy.classes.legacy_patch to provide backward compatibility
    - classes are all parsed and dumped/stored using typetrees now
- **TypeTree**
  - use a hierarchical instead of a flat structure
    - list to Node.m_Children
  - rewrite the typetree read and write functions to reflect this
  - **remove map typetree type type due to its multi-dict nature**
- **Exporter**
  - extended Sprite-mesh support (solves some dicings automatically)
