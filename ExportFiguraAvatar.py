
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
    pos: BlVector
    children: list['Bone']

    def __init__(self, name: str, pos: BlVector, children: list['Bone']) -> None:
        self.name = name
        self.pos = pos
        self.children = children

    def parseArmature(armature: BlArmature) -> list['Bone']:
        return [Bone.parseBone(bone) for bone in armature.bones if bone.parent == None]

    def parseBone(bone: BlBone) -> 'Bone':
        return Bone(fixGroupName(bone.name), fixVector(bone.head_local), [Bone.parseBone(child) for child in bone.children])


class Texture:
    name: str
    base64 = str

    def __init__(self, name: str, base64: str) -> None:
        self.name = name
        self.base64 = base64

    def parseImage(image: BlImage):
        import os
        filepath = image.filepath
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
    name: str
    uuid: str
    vertices: list[Vertex]
    loops: list[Loop]
    faces: list[Face]
    textures: list[Texture]
    bones: list[Bone]
    vertexGroups: dict[str, int]

    def __init__(self, name: str, uuid: str, vertices: list[Vertex], loops: list[Loop], faces: list[Face], textures: list[Texture], bones: list[Bone], vertexGroups: dict[str, int]):
        self.name = name
        self.uuid = uuid
        self.vertices = vertices
        self.loops = loops
        self.faces = faces
        self.textures = textures
        self.bones = bones
        self.vertexGroups = vertexGroups

    def parseMesh(meshObj: BlObject) -> 'Mesh':
        from uuid import uuid4
        mesh: BlMesh = meshObj.data
        uvs = mesh.uv_layers[0].data
        loops=[]
        for loop in mesh.loops:
            for f in mesh.polygons:
                if loop.index in f.loop_indices and f.loop_total in {3,4}:
                  loops.append(Loop(loop.vertex_index, fixUV(uvs[loop.index].uv)))
                  break
                    
        return Mesh(
            fixGroupName(meshObj.name),
            str(uuid4()),
            [Vertex(fixVector(vertex.co),
                    {group.group: group.weight for group in vertex.groups if group.weight>=0.0001}) for vertex in mesh.vertices],
            loops,
            [Face(face.material_index, [i for i in face.loop_indices])
             for face in mesh.polygons if face.loop_total in {3,4}],
            [Texture.parseMaterial(
                materialSlot.material) for materialSlot in meshObj.material_slots],
            Bone.parseArmature(meshObj.find_armature().data),
            {fixGroupName(group.name)             : group.index for group in meshObj.vertex_groups}
        )


def generateAvatar(name: str, mesh: Mesh):
    def generateBBModel(mesh: Mesh):
        def generateVertices(vertices: list[Vertex]):
            return (f'"{str(i)}":[{vert.pos.x},{vert.pos.y},{vert.pos.z}]' for i, vert in enumerate(vertices))

        def generateFaces(faces: list[Face], loops: list[Loop]):
            def generateFaceVertices(face: Face):
                return (f'"{str(loops[loop].vertexIndex)}"' for loop in face.loopIndices)

            def generateFaceUVs(face: Face):
                return (f'"{loops[loop].vertexIndex}":[{loops[loop].uv[0]},{loops[loop].uv[1]}]'for loop in face.loopIndices)
            return (
                (
                    f'"{str(i)}":{{'
                    f' "vertices":['
                    f'  {",".join(generateFaceVertices(face))}'
                    f' ],'
                    f' "uv":{{'
                    f'  {",".join(generateFaceUVs(face))}'
                    f' }},'
                    f' "texture":{face.texture}'
                    f'}}'
                ) for i, face in enumerate(faces))

        def generateOutliner(bones: list[Bone], meshUUID: str):
            def generateGroup(bone: Bone):
                return (
                    f'{{'
                    f' "name":"{bone.name}",'
                    f' "origin":[{bone.pos.x},{bone.pos.y},{bone.pos.z}],'
                    f' "children":['
                    f'  {",".join(generateGroup(child) for child in bone.children)}'
                    f' ]'
                    f'}}'
                )
            outliner = [generateGroup(bone) for bone in bones]
            outliner.append(f'"{meshUUID}"')
            return outliner

        def generateTextures(textures: list[Texture]):
            return ((
                f'{{'
                f' "name":"{texture.name}",'
                f' "source":"{texture.base64}"'
                f'}}'
            ) for texture in textures)
        return (
            f'{{'
            f' "meta":{{'
            f'  "format_version":"4.5",'
            f'  "model_format":"free",'
            f'  "box_uv":false'
            f' }},'
            f' "name":"KattMeshDeformation",'
            f' "resolution":{{'
            f'  "width":1,'
            f'  "height":1'
            f' }},'
            f' "elements":['
            f'  {{'
            f'   "name":"Mesh",'
            f'   "origin":[0,0,0],'
            f'   "rotation":[0,0,0],'
            f'   "vertices":{{'
            f'    {",".join(generateVertices(mesh.vertices))}'
            f'   }},'
            f'   "faces":{{'
            f'    {",".join(generateFaces(mesh.faces, mesh.loops))}'
            f'   }},'
            f'   "type":"mesh",'
            f'   "uuid":"{mesh.uuid}"'
            f'  }}'
            f' ],'
            f' "outliner":['
            f'  {",".join(generateOutliner(mesh.bones,mesh.uuid))}'
            f' ],'
            f' "textures":['
            f'  {",".join(generateTextures(mesh.textures))}'
            f' ]'
            f'}}'
        )

    def generateMeshData(name: str, mesh: Mesh):
        def generateGroupMap(groupMap: dict[str, int]):
            return (f'["{groupName}"]={groupIndex+1}' for groupName, groupIndex in groupMap.items())

        def generateTextureMap(textures: list[Texture]):
            return (f'[{textureIndex+1}]="{texture.name}"' for textureIndex, texture in enumerate(textures))

        def generateVertexData(mesh: Mesh):
            textureVertexMap = [[]for _ in mesh.textures]
            for face in mesh.faces:
                for loopIndex in face.loopIndices:
                    textureVertexMap[face.texture].append(loopIndex)
                    if len(face.loopIndices)==3 and loopIndex == face.loopIndices[len(face.loopIndices)-1]:
                        textureVertexMap[face.texture].append(loopIndex)

            def generateLoopIndices(vertexIndex: int):
                textureVertexIndices: dict[int, list[int]] = {}
                for textureIndex, loops in enumerate(textureVertexMap):
                    for loopIndex in loops:
                        if mesh.loops[loopIndex].vertexIndex == vertexIndex:
                            break
                    else:
                        continue
                    textureVertexIndices[textureIndex] = []
                    for index, loopIndex in enumerate(loops):
                        if mesh.loops[loopIndex].vertexIndex == vertexIndex:
                            textureVertexIndices[textureIndex].append(index)
                return ((
                    f'[{textureIndex+1}]={{'
                    f' {",".join(str(x+1) for x in loops)}'
                    f'}}'
                ) for textureIndex, loops in textureVertexIndices.items())

            def generateVertexWeights(vertex: Vertex):
                return (f'[{group+1}]={round(weight,4)}' for group, weight in vertex.weights.items())
            return ((
                f'[{index+1}]={{'
                f' loops={{'
                f'  {",".join(generateLoopIndices(index))}'
                f' }},'
                f' weights={{'
                f'  {",".join(generateVertexWeights(vertex))}'
                f' }}'
                f'}}'
            ) for index, vertex in enumerate(mesh.vertices))
        return (
            f'return {{'
            f' modelName="{name}",'
            f' groupMap={{'
            f'  {",".join(generateGroupMap(mesh.vertexGroups))}'
            f' }},'
            f' textureMap={{'
            f'  {",".join(generateTextureMap(mesh.textures))}'
            f' }},'
            f' vertexData={{'
            f'  {",".join(generateVertexData(mesh))}'
            f' }}'
            f'}}'
        )
    return (generateBBModel(mesh), generateMeshData(name, mesh))


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
        bbmodel, meshdata = generateAvatar(filename, Mesh.parseMesh(meshObj))

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
