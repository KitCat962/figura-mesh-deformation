
import bpy
from uuid import uuid4 as newUUID
bl_info = {
    "name": "Export as Figura Avatar",
    "blender": (3, 4, 0),
    "category": "Object",
}


def fixGroupName(name: str):
    return name.replace(".", "").replace(" ", "_")


def fixAxis(vector):
    v = vector.copy()
    v.x, v.y, v.z = v.x*16, v.z*16, -v.y*16
    return v


def fixUV(uv):
    u = [i for i in uv]
    u[0], u[1] = u[0], 1-u[1]
    return u


def parseVertexGroups(meshObj):
    return {fixGroupName(group.name): group.index for group in meshObj.vertex_groups}


def parseVertexWeights(meshObj):
    return {vert.index: {group.group: round(group.weight, 4) for group in vert.groups} for vert in meshObj.data.vertices}
    vertWeights = {}
    for vert in meshObj.data.vertices:
        vertWeights[vert.index] = {}
        for group in vert.groups:
            vertWeights[vert.index][group.group] = round(group.weight, 4)

    print(vertWeights)
    return vertWeights
    # for vertGroup in meshObj.vertex_groups:
    #     vertGroupName = validateGroupName(vertGroup.name)
    #     vertGroupData[vertGroupName] = []
    #     for face in meshObj.data.polygons:
    #         for vert in face.vertices:
    #             try:
    #                 weight = vertGroup.weight(vert)
    #             except:
    #                 weight = None
    #             vertGroupData[vertGroupName].append(weight)
    return vertWeights


def parseVertexIndices(meshObj):
    verts = [[] for _ in range(len(meshObj.data.vertices))]
    for i, face in enumerate(meshObj.data.polygons):
        for o, vert in enumerate(face.vertices):
            verts[vert].append(i*(4)+o)
    return verts


def parseMesh(meshObj):
    uvs = meshObj.data.uv_layers[0].data
    mesh = {
        "vertices": [fixAxis(vert.co) for vert in meshObj.data.vertices],
        "faces": [{"verts": [i for i in face.vertices], "uv": [fixUV(uvs[uvIndex].uv) for uvIndex in face.loop_indices]} for face in meshObj.data.polygons],
        "uuid": str(newUUID())
    }
    return mesh


def parseBone(bone):
    return {
        "name": fixGroupName(bone.name),
        "pos": fixAxis(bone.head_local),
        "children": [parseBone(child) for child in bone.children]
    }


def parseArmature(armatureObj):
    return [parseBone(bone) for bone in armatureObj.data.bones if bone.parent == None]


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


class ExportBlockBench(bpy.types.Operator):
    """When used on a mesh with an Armature, will do stuff"""      # Use this as a tooltip for menu items and buttons.
    bl_idname = "object.export"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Export Blockbench"         # Display name in the interface.
    bl_options = {'REGISTER'}  # Enable undo for the operator.

    def execute(self, context):
        meshObj = context.active_object
        if not meshObj:
            return {'CANCELLED'}
        if meshObj.type != "MESH":
            return {'CANCELLED'}
        armature = meshObj.find_armature()
        if not armature:
            return {'CANCELLED'}

        boneTree = parseArmature(armature)
        vertexGroups = parseVertexGroups(meshObj)
        mesh = parseMesh(meshObj)
        # print(mesh)
        # print(generateVertexGroupData(vertexGroups))

        # print(generateBBmodel(mesh, groups))
        vertMap, groupWeights, groupMap = parseVertexIndices(
            meshObj), parseVertexWeights(meshObj), parseVertexGroups(meshObj)
        print("vertIndex ", vertMap)
        print("vertWeights ", groupWeights)
        print("vertGroups ", groupMap)
        print()
        print(generateScript(vertMap, groupWeights, groupMap))
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ExportBlockBench.bl_idname)


def register():
    bpy.utils.register_class(ExportBlockBench)
    # Adds the new operator to an existing menu.
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ExportBlockBench)


if __name__ == "__main__":
    register()
