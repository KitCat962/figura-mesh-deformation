
import bpy
import os
import base64
import mathutils
from bpy_extras.io_utils import ExportHelper
from uuid import uuid4 as newUUID
bl_info = {
    "name": "Export as Figura Avatar",
    "blender": (3, 4, 0),
    "category": "Import-Export",
    "location": "File > Export > Export Figura Avatar",
}


def fixGroupName(name: str):
    return name.replace(".", "").replace(" ", "_")


def fixVector(vector: mathutils.Vector) -> mathutils.Vector:
    v = vector.copy()
    v.x, v.y, v.z = v.x*16, v.z*16, -v.y*16
    return v


def fixUV(uv: tuple[float, float]) -> tuple[float, float]:
    return (uv[0], 1-uv[1])


class Vertex:
    pos: mathutils.Vector
    weights: dict[int, float]

    def __init__(self, pos: tuple[float, float, float], weights: dict[int, float]) -> None:
        self.pos = pos
        self.weights = weights


class Loop:
    vertexIndex: int
    uv: tuple[float, float]

    def __init__(self, vertexIndex: int, uv: tuple[float, float]) -> None:
        self.vertexIndex = vertexIndex
        self.uv = uv


class Face:
    texture: int
    loopIndices: list[int]

    def __init__(self, texture: int, loopIndices: list[int]) -> None:
        self.texture = texture
        self.loopIndices = loopIndices


class Bone:
    name: str
    pos: mathutils.Vector
    children: list['Bone']

    def __init__(self, name: str, pos: mathutils.Vector, children: list['Bone']) -> None:
        self.name = name
        self.pos = pos
        self.children = children

    def parseArmature(armature: bpy.types.Armature) -> list['Bone']:
        return [Bone.parseBone(bone) for bone in armature.bones if bone.parent == None]

    def parseBone(bone: bpy.types.Bone) -> 'Bone':
        return Bone(fixGroupName(bone.name), fixVector(bone.head_local), [Bone.parseBone(child) for child in bone.children])


class Texture:
    name:str
    base64 = str

    def __init__(self,name:str, base64: str) -> None:
        self.name=name
        self.base64 = base64

    def parseImage(image: bpy.types.Image):
        filepath = image.filepath
        if not os.path.exists(filepath):
            filepath = bpy.path.ensure_ext(bpy.path.abspath(
                f"//{image.name}"), ext=".png", case_sensitive=True)
            image.save(filepath=filepath)
            markDel = True
        data = None
        with open(filepath, 'rb') as file:
            data = base64.b64encode(file.read()).decode()
        if markDel:
            os.remove(filepath)
        return Texture(image.name,f'data:image/png;base64,{data}')

    def parseMaterial(material: bpy.types.Material):
        matOutputNode = material.node_tree.get_output_node('ALL')
        shaderNode = None
        for link in material.node_tree.links:
            if link.to_node == matOutputNode:
                shaderNode = link.from_node
                break
        if shaderNode is None or shaderNode.bl_idname != 'ShaderNodeBsdfPrincipled':
            img = bpy.data.images.new(
                f"null_{material.name}_{str(newUUID())}.png", 16, 16)
            color = (1, 0, 1, 1)
            for p in range(0, 16*16*4, 8):
                for i in range(4):
                    img.pixels[p+i] = color[i]
            img.file_format = "PNG"
            texture = Texture.parseImage(img)
            bpy.data.images.remove(img)
            return texture
        textureNode = None
        for link in material.node_tree.links:
            if link.to_node == shaderNode:
                textureNode = link.from_node
                break
        if textureNode is None or textureNode.bl_idname != 'ShaderNodeTexImage':
            img = bpy.data.images.new(
                f"solid_{material.name}_{str(newUUID())}.png", 1, 1)
            color = shaderNode.inputs["Base Color"].default_value
            for i in range(4):
                img.pixels[i] = color[i]
            img.file_format = "PNG"
            texture = Texture.parseImage(img)
            bpy.data.images.remove(img)
            return texture
        return Texture.parseImage(textureNode.image)


class Mesh:
    uuid: str
    vertices: list[Vertex]
    loops: list[Loop]
    faces: list[Face]
    textures: list[Texture]
    bones: list[Bone]

    def __init__(self, meshObj: bpy.types.Object):
        self.uuid = str(newUUID())
        mesh: bpy.types.Mesh = meshObj.data
        self.vertices = [Vertex(fixVector(vertex.co), {
                                group.group: group.weight for group in vertex.groups}) for vertex in mesh.vertices]
        uvs = mesh.uv_layers[0].data
        self.loops = [Loop(loop.vertex_index, fixUV(uvs[loop.index].uv))
                      for loop in mesh.loops]
        self.faces = [Face(face.material_index, [i for i in face.loop_indices])
                      for face in mesh.polygons]
        self.bones = Bone.parseArmature(meshObj.find_armature().data)
        self.textures = [Texture.parseMaterial(
            materialSlot.material) for materialSlot in meshObj.material_slots]


def generateVertices(vertices):
    return ",".join('"{}":[{},{},{}]'.format(str(index), vert[0], vert[1], vert[2]) for index, vert in enumerate(vertices))


def generateFaces(faces):
    return ",".join('"{name}":{{"vertices":[{vertices}],"uv":{{{uvs}}},"texture":0}}'.format(
        name=str(faceIndex),
        vertices=",".join('"{}"'.format(
            str(vertIndex)
        ) for vertIndex in face["verts"]),
        uvs=",".join('"{}":[{},{}]'.format(
            str(vertIndex),
            face["uv"][index][0],
            face["uv"][index][1]
        ) for index, vertIndex in enumerate(face["verts"]))
    ) for faceIndex, face in enumerate(faces))


def generateMesh(mesh):
    return ('{{"name":"mesh","vertices":{{{vertices}}},"faces":{{{faces}}},"type":"mesh","uuid":"{uuid}"}}').format(
        uuid=mesh["uuid"],
        vertices=generateVertices(mesh["vertices"]),
        faces=generateFaces(mesh["faces"])
    )


def generateVertexGroupData(vertexGroups):
    return "return {{{}}}".format(
        ",".join('["{}"]={{{}}}'.format(
            name,
            ",".join((str(weight) if weight else "0") for weight in group)
        ) for name, group in vertexGroups.items())
    )


def generateGroup(group):
    return ('{{"name":"{name}","origin":[{x},{y},{z}],"children":[{children}]}}').format(
        name=group["name"],
        x=group["pos"][0], y=group["pos"][1], z=group["pos"][2],
        children=",".join(generateGroup(child) for child in group["children"])
    )


def generateBBmodel(mesh, groups):
    outliner = [generateGroup(group) for group in groups]
    outliner.append('"{}"'.format(mesh["uuid"]))
    return ('{{"meta": {{"format_version": "4.5","model_format": "free","box_uv": false}},"name":"Avatar","resolution":{{"width":1,"height":1}},"elements":[{mesh}],"outliner":[{outliner}]}}').format(
        outliner=",".join(outliner),
        mesh=generateMesh(mesh)
    )


def generateVertexIndexMap(vertexMap):
    return "{{{}}}".format(",".join("[{}]={{{}}}".format(index+1, ",".join(str(i+1) for i in verts)) for index, verts in enumerate(vertexMap)))


def generateVertexGroups(groupWeights):
    return "{{{}}}".format(",".join("[{}]={{{}}}".format(index+1, ",".join("[{}]={}".format(group+1, weight) for group, weight in weights.items())) for index, weights in groupWeights.items()))


def generateGroupMap(groupMap):
    return "{{{}}}".format(",".join('["{}"]={}'.format(name, index+1) for name, index in groupMap.items()))


def generateScript(vertexMap, groups, groupMap):
    return "return {{vertexMap={},groups={},groupMap={}}}".format(
        generateVertexIndexMap(vertexMap),
        generateVertexGroups(groups),
        generateGroupMap(groupMap)
    )



class ExportFiguraAvatar(bpy.types.Operator, ExportHelper):
    """Exports the currently seleted mesh as a Figura Avatar"""      # Use this as a tooltip for menu items and buttons.
    bl_idname = "export.figura_avatar"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Export Figura Avatar"

    filename_ext = ".bbmodel"
    use_filter_folder = True
    filter_glob: bpy.props.StringProperty(
        default="*.json;*.bbmodel;*.lua",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        print(self.filepath)
        print(os.path.dirname(self.filepath))
        meshObj = context.active_object
        if not meshObj or meshObj.type != "MESH":
            self.report({'ERROR'}, "Active Object is not a Mesh")
            return {'CANCELLED'}
        if not meshObj.find_armature():
            self.report(
                {'ERROR'}, "Active Mesh must be Parented to an Armature")
            return {'CANCELLED'}

        # print(Mesh(meshObj))
        print(bpy.data.materials[1])
        print(Texture.parseMaterial(bpy.data.materials[1]))
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ExportFiguraAvatar.bl_idname, text="Figura Avatar")


def register():
    bpy.utils.register_class(ExportFiguraAvatar)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ExportFiguraAvatar)


if __name__ == "__main__":
    register()
