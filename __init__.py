
import bpy
from uuid import uuid4 as newUUID
bl_info = {
    "name": "Cursor Array",
    "blender": (3, 4, 0),
    "category": "Object",
}


def validateGroupName(name: str):
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
    vertGroupData = {}
    for vertGroup in meshObj.vertex_groups:
        vertGroupName = validateGroupName(vertGroup.name)
        vertGroupData[vertGroupName] = []
        for face in meshObj.data.polygons:
            for vert in face.vertices:
                weight = None
                try:
                    weight = vertGroup.weight(vert)
                except:
                    pass
                vertGroupData[vertGroupName].append(weight)
    return vertGroupData


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
        "name": validateGroupName(bone.name),
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

        groups = parseArmature(armature)
        vertexGroups = parseVertexGroups(meshObj)
        mesh = parseMesh(meshObj)
        # print(mesh)

        print(generateBBmodel(mesh, groups))
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
