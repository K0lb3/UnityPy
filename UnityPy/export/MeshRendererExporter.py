import os
from ..classes import Renderer, SkinnedMeshRenderer, Material
from .MeshExporter import export_mesh_obj


def get_mesh(meshR: Renderer):
    if isinstance(meshR, SkinnedMeshRenderer.SkinnedMeshRenderer):
        if meshR.m_Mesh:
            return meshR.m_Mesh.read()
    else:
        m_GameObject = meshR.m_GameObject.read()
        if m_GameObject.m_MeshFilter:
            filter = m_GameObject.m_MeshFilter.read()
            if filter.m_Mesh:
                return filter.m_Mesh.read()
    return None


def export_mesh_renderer(obj: Renderer, export_dir: str) -> None:
    env = mesh.assets_file.enviroment
    env.fs.makedirs(export_dir, exist_ok=True)
    meshR = obj.read()
    mesh = get_mesh(meshR)
    if not mesh:
        return

    firstSubMesh = 0
    if hasattr(meshR, "m_StaticBatchInfo") and meshR.m_StaticBatchInfo.subMeshCount > 0:
        firstSubMesh = meshR.m_StaticBatchInfo.firstSubMesh
    elif hasattr(meshR, "m_SubsetIndices"):
        firstSubMesh = min(meshR.m_SubsetIndices)

    materials = []
    material_names = []
    for i, submesh in enumerate(mesh.m_SubMeshes):
        mat_index = i - firstSubMesh
        if mat_index < 0 or mat_index >= len(meshR.m_Materials):
            continue
        matPtr = meshR.m_Materials[i - firstSubMesh]
        if matPtr:
            mat = matPtr.read()
        else:
            material_names.append(None)
            continue
        materials.append(export_material(mat))
        material_names.append(mat.name)
        # save material textures
        for key, texEnv in mat.m_SavedProperties.m_TexEnvs.items():
            if not texEnv.m_Texture:
                continue
            tex = texEnv.m_Texture.read()
            texName = f"{tex.m_Name if tex.m_Name else key}.png"
            with env.fs.open(env.fs.sep.join([export_dir, texName]), "wb") as f:
                tex.read().image.save(f)

    # save .obj
    with env.fs.open(
        env.fs.sep.join([export_dir, f"{mesh.m_Name}.obj"]),
        "wt",
        encoding="utf8",
        newline="",
    ) as f:
        f.write(export_mesh_obj(mesh, material_names))

    # save .mtl
    with env.fs.open(
        env.fs.sep.join([export_dir, f"{mesh.m_Name}.mtl"]),
        "wt",
        encoding="utf8",
        newline="",
    ) as f:
        f.write("\n".join(materials))


def export_material(mat: Material) -> str:
    """Creates a material file (.mtl) for the given material."""

    def clt(color):  # color to tuple
        return (
            color if isinstance(color, tuple) else (color.R, color.G, color.B, color.A)
        )

    colors = mat.m_SavedProperties.m_Colors
    floats = mat.m_SavedProperties.m_Floats
    texEnvs = mat.m_SavedProperties.m_TexEnvs

    diffuse = clt(colors.get("_Color", (0.8, 0.8, 0.8, 1)))
    ambient = clt(colors.get("_SColor", (0.2, 0.2, 0.2, 1)))
    emissive = clt(colors.get("_EmissionColor", (0, 0, 0, 1)))
    specular = clt(colors.get("_SpecularColor", (0.2, 0.2, 0.2, 1)))
    reflection = clt(colors.get("_ReflectColor", (0, 0, 0, 1)))
    shininess = floats.get("_Shininess", 20.0)
    transparency = floats.get("_Transparency", 0.0)

    sb = []
    sb.append(f"newmtl {mat.name}")
    # Ka r g b
    # defines the ambient color of the material to be (r,g,b). The default is (0.2,0.2,0.2);
    sb.append(f"Ka {ambient[0]:.4f} {ambient[1]:.4f} {ambient[2]:.4f}")
    # Kd r g b
    # defines the diffuse color of the material to be (r,g,b). The default is (0.8,0.8,0.8);
    sb.append(f"Kd {diffuse[0]:.4f} {diffuse[1]:.4f} {diffuse[2]:.4f}")
    # Ks r g b
    # defines the specular color of the material to be (r,g,b). This color shows up in highlights. The default is (1.0,1.0,1.0);
    sb.append(f"Ks {specular[0]:.4f} {specular[1]:.4f} {specular[2]:.4f}")
    # d alpha
    # defines the non-transparency of the material to be alpha. The default is 1.0 (not transparent at all). The quantities d and Tr are the opposites of each other, and specifying transparency or nontransparency is simply a matter of user convenience.
    # Tr alpha
    # defines the transparency of the material to be alpha. The default is 0.0 (not transparent at all). The quantities d and Tr are the opposites of each other, and specifying transparency or nontransparency is simply a matter of user convenience.
    sb.append(f"Tr {transparency:.4f}")
    # Ns s
    # defines the shininess of the material to be s. The default is 0.0;
    sb.append(f"Ns {shininess:.4f}")
    # illum n
    # denotes the illumination model used by the material. illum = 1 indicates a flat material with no specular highlights, so the value of Ks is not used. illum = 2 denotes the presence of specular highlights, and so a specification for Ks is required.
    # map_Ka filename
    # names a file containing a texture map, which should just be an ASCII dump of RGB values;
    texName = None
    tex = None
    for key, texEnv in texEnvs.items():
        if not texEnv.m_Texture:
            continue
        tex = texEnv.m_Texture.read()
        texName = f"{tex.m_Name if tex.m_Name else key}.png"
        if key == "_MainTex":
            sb.append(f"map_Kd {texName}")
        elif key == "_BumpMap":
            # TODO: bump is default, some use map_bump
            sb.append(f"map_bump {texName}")
            sb.append(f"bump {texName}")
        elif "Specular" in key:
            sb.append(f"map_Ks {texName}")
        elif "Normal" in key:
            # TODO: figure out the key
            pass
    ret = "\n".join(sb)
    return ret
