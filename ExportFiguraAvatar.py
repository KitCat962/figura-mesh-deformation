
import bpy
from bpy.types import Object as BlObject, Mesh as BlMesh, Material as BlMaterial, Armature as BlArmature, Bone as BlBone
from bpy.types import Image as BlImage, Operator as BlOperator
from mathutils import Vector as BlVector
from bpy_extras.io_utils import ExportHelper
bl_info = {
    "name": "Export Figura Avatar",
    "author": "KitCat962",
    "description": "Exports a bbmodel file with a corresponding script file, allowing for controlled mesh deformation in Figura via armatures.",
    "blender": (3, 4, 0),
    "category": "Import-Export",
    "location": "File > Export > Export Figura Avatar",
}

def fixGroupName(name: str):
    return name.replace(".", "").replace(" ", "_")


def fixVector(vector: BlVector) -> BlVector:
    v = vector.copy()
    v.x, v.y, v.z = -v.x*16, v.z*16, v.y*16
    return v


def fixUV(uv: tuple[float, float]) -> tuple[float, float]:
    return (uv[0], 1-uv[1])


class Vertex:
    pos: BlVector
    weights: dict[int, float]

    def __init__(self, pos: BlVector, weights: dict[int, float]) -> None:
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
    pos: BlVector
    children: list['Bone']

    def __init__(self, name: str, pos: BlVector, children: list['Bone']) -> None:
        self.name = name
        self.pos = pos
        self.children = children

    @staticmethod
    def parseArmature(armature: BlArmature) -> list['Bone']:
        return [Bone.parseBone(bone) for bone in armature.bones if bone.parent == None]

    @staticmethod
    def parseBone(bone: BlBone) -> 'Bone':
        return Bone(fixGroupName(bone.name), fixVector(bone.head_local), [Bone.parseBone(child) for child in bone.children])


class Texture:
    name: str
    base64 = str

    def __init__(self, name: str, base64: str) -> None:
        self.name = name
        self.base64 = base64

    @staticmethod
    def parseImage(image: BlImage):
        import os
        filepath = image.filepath
        markDel=False
        if not os.path.exists(filepath):
            filepath = bpy.path.abspath(f"//{image.name}")
            image.save(filepath=filepath)
            markDel = True
        data = None
        with open(filepath, 'rb') as file:
            from base64 import b64encode
            data = b64encode(file.read()).decode()
        if markDel:
            os.remove(filepath)
        return Texture(image.name, f'data:image/png;base64,{data}')

    @staticmethod
    def parseMaterial(material: BlMaterial):
        matOutputNode = material.node_tree.get_output_node('ALL')
        shaderNode = None
        for link in material.node_tree.links:
            if link.to_node == matOutputNode and link.to_socket.name=="Surface":
                shaderNode = link.from_node
                break
        if shaderNode is None or shaderNode.bl_idname != 'ShaderNodeBsdfPrincipled':
            img = bpy.data.images.new(
                f"null_{material.name}", 16, 16)
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
            if link.to_node == shaderNode and link.to_socket.name=="Base Color":
                textureNode = link.from_node
                break
        if textureNode is None or textureNode.bl_idname != 'ShaderNodeTexImage':
            img = bpy.data.images.new(
                f"solid_{material.name}", 1, 1)
            color = shaderNode.inputs["Base Color"].default_value
            for i in range(4):
                img.pixels[i] = color[i]
            img.file_format = "PNG"
            texture = Texture.parseImage(img)
            bpy.data.images.remove(img)
            return texture
        return Texture.parseImage(textureNode.image)


class Mesh:
    vertices: list[Vertex]
    loops: list[Loop]
    faces: list[Face]

    def __init__(self, vertices: list[Vertex], loops: list[Loop], faces: list[Face]):
        self.vertices = vertices
        self.loops = loops
        self.faces = faces

    @staticmethod
    def parseMesh(mesh: BlMesh) -> 'Mesh':
        uvs = mesh.uv_layers[0].data
        loops=[]
        for loop in mesh.loops:
            for f in mesh.polygons:
                if loop.index in f.loop_indices and f.loop_total in {3,4}:
                  loops.append(Loop(loop.vertex_index, fixUV(uvs[loop.index].uv)))
                  break
                    
        return Mesh(
            [Vertex(fixVector(vertex.co), {group.group: group.weight for group in vertex.groups if group.weight>=0.0001}) for vertex in mesh.vertices],
            loops,
            [Face(face.material_index, [i for i in face.loop_indices]) for face in mesh.polygons if face.loop_total in {3,4}]
        )
    
class Object:
    name: str
    uuid: str
    mesh:Mesh
    textures: list[Texture]
    bones: list[Bone]
    vertexGroups: dict[str, int]
    
    def __init__(self, name:str,uuid:str,mesh:Mesh,textures:list[Texture],bones:list[Bone],vertexGroups:dict[str,int]):
        self.name=name
        self.uuid=uuid
        self.mesh=mesh
        self.textures=textures
        self.bones=bones
        self.vertexGroups=vertexGroups

    @staticmethod
    def parseObject(obj:BlObject) -> 'Object':
        from uuid import uuid4
        return Object(
            fixGroupName(obj.name),
            str(uuid4()),
            Mesh.parseMesh(obj.data),
            [Texture.parseMaterial(materialSlot.material) for materialSlot in obj.material_slots],
            Bone.parseArmature(obj.find_armature().data),
            {fixGroupName(group.name) : group.index for group in obj.vertex_groups}
        )

class JsonParser:
    @staticmethod
    def toJson(obj:'Any'):
        match obj:
            case dict():
                return f'{{{",".join(f"{JsonParser.toJson(key)}:{JsonParser.toJson(value)}" for key,value in obj.items())}}}'
            case list():
                return f'[{",".join(JsonParser.toJson(value) for value in obj)}]'
            case str():
                return f'"{obj}"'
            case bool():
                return "true" if obj else "false"
            case int():
                return str(obj)
            case float():
                return str(obj)
            case set():
                print(obj)
                for i in obj:
                    print(i)
                raise TypeError("wtf is a set")
            case _:
                raise TypeError(f'Unknown type:"{type(obj)}" ({obj})')
class LuaParser:
    keywords=["and","break","do","else","elseif","end","false","for","function","if","in","local","nil","not","or","repeat","return","then","true","until","while"]
    @staticmethod
    def isValidName(s:str):
        import re
        return bool(type(s) is str and re.search(r'^[a-zA-Z0-9_]+$', s) and not s.startswith(('0','1','2','3','4','5','6','7','8','9')) and not any(s==k for k in LuaParser.keywords))
    @staticmethod
    def toLua(obj:'Any'):
        match obj:
            case dict():
                elemets=[(f'{key}:{LuaParser.toLua(value)}' if LuaParser.isValidName(key) else f'[{LuaParser.toLua(key)}]={LuaParser.toLua(value)}') for key,value in obj.items() if value!=None]
                return f'{{{",".join(elemets)}}}'
            case list():
                return f'{{{",".join(LuaParser.toLua(value) for value in obj)}}}'
            case str():
                return f'"{obj}"'
            case bool():
                return "true" if obj else "false"
            case int():
                return str(obj)
            case float():
                return str(obj)
            case None:
                return 'nil'
            case _:
                raise TypeError(f'Unknown type:"{type(obj)}" ({obj})')
        
def generateAvatar(name: str, obj: Object):
    def generateBBModel(obj: Object):
        def generateGroup(bone: Bone):
            return {
                "name":bone.name,
                "origin":[bone.pos.x,bone.pos.y,bone.pos.z],
                "children":[generateGroup(child) for child in bone.children]
            }
        bbmodel={
            "meta":{
              "format_version":"4.5",
              "model_format":"free",
              "box_uv":False
            },
            "name":"KattMeshDeformation",
            "resolution":{
              "width":1,
              "height":1
            },
            "elements":[{
              "name":"Mesh",
              "origin":[0,0,0],
              "rotation":[0,0,0],
              "vertices":{
                str(i):[
                  vert.pos.x,
                  vert.pos.y,
                  vert.pos.z
                ] for i, vert in enumerate(obj.mesh.vertices)
              },
              "faces":{
                str(i):{
                  "vertices":[str(obj.mesh.loops[loop].vertexIndex) for loop in face.loopIndices],
                  "uv":{
                    str(obj.mesh.loops[loop].vertexIndex):[
                      obj.mesh.loops[loop].uv[0],
                      obj.mesh.loops[loop].uv[1]
                    ] for loop in face.loopIndices
                  },
                  "texture":face.texture
                } for i, face in enumerate(obj.mesh.faces)
              },
              "type":"mesh",
              "uuid":obj.uuid
            }],
            "outliner":[generateGroup(bone) for bone in obj.bones],
            "textures":[{
              "name":texture.name,
              "source":texture.base64
            } for texture in obj.textures]
        }
        bbmodel["outliner"].append(obj.uuid)
        return JsonParser.toJson(bbmodel)

    def generateMeshData(name: str, obj: Object):
        # @type [texture:[list of corners using that texture]]
        figuraVertexMap = [[] for _ in obj.textures]
        for face in obj.mesh.faces:
            for loopIndex in face.loopIndices:
                figuraVertexMap[face.texture].append(loopIndex)
                if len(face.loopIndices)==3 and loopIndex == face.loopIndices[len(face.loopIndices)-1]:
                    figuraVertexMap[face.texture].append(loopIndex)
        def generateLoopIndices(vertexIndex: int):
            textureVertexIndices: dict[int, list[int]] = {}
            for textureIndex, loops in enumerate(figuraVertexMap):
                for loopIndex in loops:
                    if obj.mesh.loops[loopIndex].vertexIndex == vertexIndex:
                        break
                else:
                    continue
                textureVertexIndices[textureIndex] = []
                for index, loopIndex in enumerate(loops):
                    if obj.mesh.loops[loopIndex].vertexIndex == vertexIndex:
                        textureVertexIndices[textureIndex].append(index)
            return {textureIndex+1:[x+1 for x in loops] for textureIndex, loops in textureVertexIndices.items()}
        return "return "+LuaParser.toLua({
            "modelName":name,
            "groupMap":{groupName:groupIndex+1 for groupName, groupIndex in obj.vertexGroups.items()},
            "textureMap":[texture.name for texture in obj.textures],
            "vertexData":[{
              "loops":generateLoopIndices(index),
              "weights":{group+1:round(weight,4) for group, weight in vertex.weights.items()} if len(vertex.weights)!=0 else None
            } for index,vertex in enumerate(obj.mesh.vertices)]
        })
    return (generateBBModel(obj), generateMeshData(name, obj))


class ExportFiguraAvatar(BlOperator, ExportHelper):
    from bpy.props import BoolProperty, StringProperty
    """Exports the currently seleted mesh as a Figura Avatar"""      # Use this as a tooltip for menu items and buttons.
    bl_idname = "export.figura_avatar"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Export Figura Avatar"

    filename_ext = ".bbmodel"
    use_filter_folder = True
    filter_glob: StringProperty(
        default="*.json;*.bbmodel;*.lua",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    export_with_driver: BoolProperty(
        name="Export with driver code"
    )

    def execute(self, context):
        meshObj = context.active_object
        if not meshObj or meshObj.type != "MESH":
            self.report({'ERROR'}, "Active Object is not a Mesh")
            return {'CANCELLED'}
        if not meshObj.find_armature():
            self.report(
                {'ERROR'}, "Active Mesh must be Parented to an Armature")
            return {'CANCELLED'}
        if len(meshObj.material_slots)==0:
            self.report(
                {'ERROR'}, "Active Mesh must have at least 1 material")
            return {'CANCELLED'}

        import os
        directory, file = os.path.split(self.filepath)
        filename = os.path.splitext(file)[0]
        bbmodel, meshdata = generateAvatar(filename, Object.parseObject(meshObj))

        with open(os.path.join(directory, f'{filename}.bbmodel'), 'w') as file:
            file.write(bbmodel)

        with open(os.path.join(directory, f'{filename}-MeshData.lua'), 'w') as file:
            file.write(meshdata)

        if self.export_with_driver:
            import shutil
            addonDir, addonFile = os.path.split(__file__)
            shutil.copyfile(os.path.join(addonDir,"KattMeshDeformation.lua"),os.path.join(directory,"KattMeshDeformation.lua"))

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
