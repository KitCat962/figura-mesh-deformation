import bpy, math
from bpy.types import (
    Object as BlObject,
    Mesh as BlMesh,
    Material as BlMaterial,
    Armature as BlArmature,
    Bone as BlBone,
    Action as BlAction,
)
from bpy.types import Image as BlImage, Operator as BlOperator
from mathutils import Vector as BlVector, Quaternion as BlQuaternion
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
    v.x, v.y, v.z = -v.x * 16, v.z * 16, v.y * 16
    return v


def fixUV(uv: tuple[float, float]) -> tuple[float, float]:
    return (uv[0], 1 - uv[1])


def fixAngle(angle, *, rad=False):
    x, y, z = angle[0], -angle[1], -angle[2]
    if rad:
        x, y, z = math.degrees(x), math.degrees(y), math.degrees(z)
    return (x, y, z)


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
    uuid: str
    pos: BlVector
    tail: BlVector
    children: list["Bone"]

    def __init__(
        self,
        name: str,
        uuid: str,
        pos: BlVector,
        tail: BlVector,
        children: list["Bone"],
    ) -> None:
        self.name = name
        self.uuid = uuid
        self.pos = pos
        self.tail = tail
        self.children = children

    @staticmethod
    def parseArmature(armature: BlArmature) -> list["Bone"]:
        return [Bone.parseBone(bone) for bone in armature.bones if bone.parent == None]

    @staticmethod
    def parseBone(bone: BlBone) -> "Bone":
        from uuid import uuid4

        return Bone(
            fixGroupName(bone.name),
            str(uuid4()),
            fixVector(bone.head_local),
            fixVector(bone.tail_local),
            [Bone.parseBone(child) for child in bone.children],
        )


class Texture:
    name: str
    base64 = str

    def __init__(self, name: str, base64: str) -> None:
        self.name = name
        self.base64 = base64

    @staticmethod
    def parseImage(image: BlImage):
        import os

        filepath = bpy.path.abspath(image.filepath)
        markDel = False
        if not os.path.exists(filepath):
            filepath = bpy.path.abspath(f"//{image.name}")
            image.save(filepath=filepath)
            markDel = True
        data = None
        with open(filepath, "rb") as file:
            from base64 import b64encode

            data = b64encode(file.read()).decode()
        if markDel:
            os.remove(filepath)
        textureName, _ = os.path.splitext(bpy.path.ensure_ext(image.name, ".png"))
        return Texture(textureName, f"data:image/png;base64,{data}")

    @staticmethod
    def parseMaterial(material: BlMaterial):
        matOutputNode = material.node_tree.get_output_node("ALL")
        shaderNode = None
        for link in material.node_tree.links:
            if link.to_node == matOutputNode and link.to_socket.name == "Surface":
                shaderNode = link.from_node
                break
        if shaderNode is None or shaderNode.bl_idname != "ShaderNodeBsdfPrincipled":
            if shaderNode and shaderNode.bl_idname == "ShaderNodeTexImage":
                return Texture.parseImage(textureNode.image)
            img = bpy.data.images.new(f"null_{material.name}", 16, 16)
            color = (1, 0, 1, 1)
            for p in range(0, 16 * 16 * 4, 8):
                for i in range(4):
                    img.pixels[p + i] = color[i]
            img.file_format = "PNG"
            texture = Texture.parseImage(img)
            bpy.data.images.remove(img)
            return texture
        textureNode = None
        for link in material.node_tree.links:
            if link.to_node == shaderNode and link.to_socket.name == "Base Color":
                textureNode = link.from_node
                break
        if textureNode is None or textureNode.bl_idname != "ShaderNodeTexImage":
            img = bpy.data.images.new(f"solid_{material.name}", 1, 1)
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
    def parseMesh(mesh: BlMesh) -> "Mesh":
        uvs = mesh.uv_layers[0].data
        loops = []
        for loop in mesh.loops:
            for f in mesh.polygons:
                if loop.index in f.loop_indices and f.loop_total in {3, 4}:
                    loops.append(Loop(loop.vertex_index, fixUV(uvs[loop.index].uv)))
                    break

        return Mesh(
            [
                Vertex(
                    fixVector(vertex.co),
                    {
                        group.group: group.weight
                        for group in vertex.groups
                        if group.weight >= 0.0001
                    },
                )
                for vertex in mesh.vertices
            ],
            loops,
            [
                Face(face.material_index, [i for i in face.loop_indices])
                for face in mesh.polygons
                if face.loop_total in {3, 4}
            ],
        )


class Keyframe:
    from typing import Literal

    type: Literal["position", "rotation", "scale"]
    bone: str
    time: float
    data: tuple[float, float, float]

    def __init__(self, type, bone, time, data):
        self.type = type
        self.bone = bone
        self.time = time
        self.data = data


# unused. Blender animations are too difficult to convert to blockbench.
class Animation:
    name: str
    length: float
    keyframes: dict[str, list[Keyframe]]
    fps: int

    def __init__(self, name, length, keyframes, fps):
        self.name = name
        self.length = length
        self.keyframes = keyframes
        self.fps = fps

    @staticmethod
    def parseObject(obj: BlObject) -> list["Animation"]:
        animations = []
        for track in obj.animation_data.nla_tracks:
            if len(track.strips) != 1:
                raise TypeError(
                    f"NLATrack {track.name} has an illegal amount of strips ({len(track.strips)}). Exporter only supports 1 strip per track."
                )
            strip = track.strips[0]
            if strip.type != "CLIP":
                raise TypeError(
                    f"NLAStrip {strip.name} in NLATrack {track.name} is an unsupported type {strip.type}. Exporter only supports strip with single action (CLIP)"
                )
            if strip.frame_start != 0:
                raise ValueError(
                    f"NLAStrip {strip.name} in NLATrack {track.name} must start at frame 0."
                )
            animations.append(Animation.parseAction(strip.action, obj))
        return animations

    @staticmethod
    def parseAction(action: BlAction, armature: BlObject) -> "Animation":
        import re

        data = {}
        for curve in action.fcurves:
            bone, type = re.match(
                r"^pose.bones\[\"(.+)\"\]\.(.+)$", curve.data_path
            ).groups()
            if not data.get(bone):
                data[bone] = {
                    frame: {"pos": [0, 0, 0], "rot": [0, 0, 0], "scale": [1, 1, 1]}
                    for frame in range(math.floor(action.frame_range[1]) + 1)
                }
            match type:
                case "location":
                    for frame, d in data[bone].items():
                        d["pos"][curve.array_index] = curve.evaluate(frame)
                case "scale":
                    for frame, d in data[bone].items():
                        d["scale"][curve.array_index] = curve.evaluate(frame)
                case "rotation_euler":
                    for frame, d in data[bone].items():
                        d["rot"][curve.array_index] = curve.evaluate(frame)
                case "rotation_quaternion":
                    pass
        keyframes = {}
        fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
        for bone, d in data.items():
            bbBone = fixGroupName(bone)
            keyframes[bbBone] = []
            for frame, frameData in d.items():
                keyframes[bbBone].append(
                    Keyframe("position", bbBone, frame / fps, tuple(frameData["pos"]))
                )
                keyframes[bbBone].append(
                    Keyframe("scale", bbBone, frame / fps, tuple(frameData["scale"]))
                )
                match armature.pose.bones[bone].rotation_mode:
                    case "QUATERNION":
                        raise TypeError("Animated bones cannot use Quaternions")
                    case "XYZ":
                        keyframes[bbBone].append(
                            Keyframe(
                                "rotation",
                                bbBone,
                                frame / fps,
                                fixAngle(frameData["rot"], rad=True),
                            )
                        )
                    case mode:
                        raise TypeError(
                            f"Bone {bone} uses unsupported rotation mode {mode}. Please change it to either QUATERNION or XYZ"
                        )
        return Animation(action.name, action.frame_range[1] / fps, keyframes, fps)


class Object:
    name: str
    uuid: str
    mesh: Mesh
    textures: list[Texture]
    vertexGroups: dict[str, int]
    bones: list[Bone]
    animations: list[Animation]

    def __init__(
        self,
        name: str,
        uuid: str,
        mesh: Mesh,
        textures: list[Texture],
        vertexGroups: dict[str, int],
        bones: list[Bone],
        animations: list[Animation],
    ):
        self.name = name
        self.uuid = uuid
        self.mesh = mesh
        self.textures = textures
        self.vertexGroups = vertexGroups
        self.bones = bones
        self.animations = animations

    @staticmethod
    def parseObject(obj: BlObject) -> "Object":
        from uuid import uuid4

        return Object(
            fixGroupName(obj.name),
            str(uuid4()),
            Mesh.parseMesh(obj.data),
            [
                Texture.parseMaterial(materialSlot.material)
                for materialSlot in obj.material_slots
            ],
            {fixGroupName(group.name): group.index for group in obj.vertex_groups},
            Bone.parseArmature(obj.find_armature().data),
            Animation.parseObject(obj.find_armature()),
        )


class JsonParser:
    @staticmethod
    def toJson(obj: "Any"):
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
    keywords = [
        "and",
        "break",
        "do",
        "else",
        "elseif",
        "end",
        "false",
        "for",
        "function",
        "if",
        "in",
        "local",
        "nil",
        "not",
        "or",
        "repeat",
        "return",
        "then",
        "true",
        "until",
        "while",
    ]

    @staticmethod
    def isValidName(s: str):
        import re

        return bool(
            type(s) is str
            and re.search(r"^[a-zA-Z0-9_]+$", s)
            and not s.startswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"))
            and not any(s == k for k in LuaParser.keywords)
        )

    @staticmethod
    def toLua(obj: "Any"):
        match obj:
            case dict():
                elemets = [
                    (
                        f"{key}={LuaParser.toLua(value)}"
                        if LuaParser.isValidName(key)
                        else f"[{LuaParser.toLua(key)}]={LuaParser.toLua(value)}"
                    )
                    for key, value in obj.items()
                    if value != None
                ]
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
                return "nil"
            case _:
                raise TypeError(f'Unknown type:"{type(obj)}" ({obj})')


def generateAvatar(name: str, obj: Object):
    def generateBBModel(obj: Object):
        boneUUIDs = {}
        boneCubes = []

        def generateGroup(bone: Bone):
            from uuid import uuid4

            boneUUIDs[bone.name] = bone.uuid
            localPos = bone.tail - bone.pos
            yaw = math.atan2(localPos.x, localPos.z) * 180.0 / math.pi
            pitch = (
                math.atan2(
                    math.sqrt(math.pow(localPos.x, 2) + math.pow(localPos.z, 2)),
                    localPos.y,
                )
                * 180.0
                / math.pi
            )
            cube = {
                "name": "cube",
                "type": "cube",
                "uuid": str(uuid4()),
                "color": 0,
                "origin": [bone.pos.x, bone.pos.y, bone.pos.z],
                "from": [
                    bone.pos.x - 0.25, 
                    bone.pos.y, 
                    bone.pos.z - 0.25
                ],
                "to": [
                    bone.pos.x + 0.25,
                    bone.pos.y + localPos.length,
                    bone.pos.z + 0.25,
                ],
                "rotation": [pitch, yaw, 0],
                "faces": {
                    "north": {"uv": [0, 0, 1, 1]},
                    "east": {"uv": [0, 0, 1, 1]},
                    "south": {"uv": [0, 0, 1, 1]},
                    "west": {"uv": [0, 0, 1, 1]},
                    "up": {"uv": [0, 0, 1, 1]},
                    "down": {"uv": [0, 0, 1, 1]},
                },
            }
            boneCubes.append(cube)
            group = {
                "name": bone.name,
                "uuid": bone.uuid,
                "origin": [bone.pos.x, bone.pos.y, bone.pos.z],
                "children": [generateGroup(child) for child in bone.children],
            }
            group["children"].append(cube["uuid"])
            return group

        bbmodel = {
            "meta": {"format_version": "4.5", "model_format": "free", "box_uv": False},
            "resolution": {"width": 1, "height": 1},
            "outliner": [generateGroup(bone) for bone in obj.bones],
            "elements": [cube for cube in boneCubes],
            "textures": [
                {"name": texture.name, "source": texture.base64}
                for texture in obj.textures
            ],
            # "animations":[
            #     {
            #       "name":animation.name,
            #       "loop":"once",
            #       "length":animation.length,
            #       "snapping":animation.fps,
            #       "animators":{boneUUIDs[bone]:{
            #           "name":bone,
            #           "type":"bone",
            #           "keyframes":[{
            #               "time":keyframe.time,
            #               "channel":keyframe.type,
            #               "interpolation": "linear",
            #               "data_points":[
            #                 {
            #                   "x":keyframe.data[0],
            #                   "y":keyframe.data[1],
            #                   "z":keyframe.data[2],
            #                 }
            #               ]
            #           } for keyframe in keyframes]
            #       } for bone, keyframes in animation.keyframes.items()}
            #     } for animation in obj.animations
            # ]
        }
        bbmodel["outliner"].append(obj.uuid)
        bbmodel["elements"].append(
            {
                "name": "Mesh",
                "origin": [0, 0, 0],
                "rotation": [0, 0, 0],
                "vertices": {
                    str(i): [vert.pos.x, vert.pos.y, vert.pos.z]
                    for i, vert in enumerate(obj.mesh.vertices)
                },
                "faces": {
                    str(i): {
                        "vertices": [
                            str(obj.mesh.loops[loop].vertexIndex)
                            for loop in face.loopIndices
                        ],
                        "uv": {
                            str(obj.mesh.loops[loop].vertexIndex): [
                                obj.mesh.loops[loop].uv[0],
                                obj.mesh.loops[loop].uv[1],
                            ]
                            for loop in face.loopIndices
                        },
                        "texture": face.texture,
                    }
                    for i, face in enumerate(obj.mesh.faces)
                },
                "type": "mesh",
                "uuid": obj.uuid,
            }
        )
        return JsonParser.toJson(bbmodel)

    def generateMeshData(name: str, obj: Object):
        # @type [texture:[list of corners using that texture]]
        figuraVertexMap = [[] for _ in obj.textures]
        for face in obj.mesh.faces:
            for loopIndex in face.loopIndices:
                figuraVertexMap[face.texture].append(loopIndex)
                if (
                    len(face.loopIndices) == 3
                    and loopIndex == face.loopIndices[len(face.loopIndices) - 1]
                ):
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
            return {
                textureIndex + 1: [x + 1 for x in loops]
                for textureIndex, loops in textureVertexIndices.items()
            }

        meshData = {
            "modelName": name,
            "groupMap": {
                groupName: groupIndex + 1
                for groupName, groupIndex in obj.vertexGroups.items()
            },
            "textureMap": [texture.name for texture in obj.textures],
            "vertexData": [
                {
                    "loops": generateLoopIndices(index),
                    "weights": {
                        group + 1: round(weight, 4)
                        for group, weight in vertex.weights.items()
                    }
                    if len(vertex.weights) != 0
                    else None,
                }
                for index, vertex in enumerate(obj.mesh.vertices)
            ],
        }

        allBones = []

        def allBonesRecursive(bone):
            allBones.append(bone)
            for b in bone.children:
                allBonesRecursive(b)

        for b in obj.bones:
            allBonesRecursive(b)

        missingGroups = [
            bone for bone in allBones if bone.name not in meshData["groupMap"].keys()
        ]
        lastGroupIndex=len(obj.vertexGroups)
        for i, group in enumerate(missingGroups):
            meshData["groupMap"][group.name] = lastGroupIndex+i+1

        return "return " + LuaParser.toLua(meshData)

    return (generateBBModel(obj), generateMeshData(name, obj))


class ExportFiguraAvatar(BlOperator, ExportHelper):
    from bpy.props import BoolProperty, StringProperty

    """Exports the currently seleted mesh as a Figura Avatar"""  # Use this as a tooltip for menu items and buttons.
    bl_idname = "export.figura_avatar"  # Unique identifier for buttons and menu items to reference.
    bl_label = "Export Figura Avatar"

    filename_ext = ".bbmodel"
    use_filter_folder = True
    filter_glob: StringProperty(
        default="*.json;*.bbmodel;*.lua",
        options={"HIDDEN"},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    export_with_driver: BoolProperty(name="Export with driver code")

    def execute(self, context):
        meshObj = context.active_object
        if not meshObj or meshObj.type != "MESH":
            self.report({"ERROR"}, "Active Object is not a Mesh")
            return {"CANCELLED"}
        if not meshObj.find_armature():
            self.report({"ERROR"}, "Active Mesh must be Parented to an Armature")
            return {"CANCELLED"}
        if len(meshObj.material_slots) == 0:
            self.report({"ERROR"}, "Active Mesh must have at least 1 material")
            return {"CANCELLED"}

        import os

        directory, file = os.path.split(self.filepath)
        filename, _ = os.path.splitext(file)
        bbmodel, meshdata = generateAvatar(filename, Object.parseObject(meshObj))

        with open(os.path.join(directory, f"{filename}.bbmodel"), "w") as file:
            file.write(bbmodel)

        with open(os.path.join(directory, f"{filename}-MeshData.lua"), "w") as file:
            file.write(meshdata)

        if self.export_with_driver:
            import shutil

            addonDir, addonFile = os.path.split(__file__)
            shutil.copyfile(
                os.path.join(addonDir, "KattMeshDeformation.lua"),
                os.path.join(directory, "KattMeshDeformation.lua"),
            )

        return {"FINISHED"}


def menu_func(self, context):
    self.layout.operator(ExportFiguraAvatar.bl_idname, text="Figura Avatar")


def register():
    bpy.utils.register_class(ExportFiguraAvatar)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ExportFiguraAvatar)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)


if __name__ == "__main__":
    register()
