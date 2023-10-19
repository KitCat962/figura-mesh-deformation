This plugin is for Blender, allowing for Mesh Deformation in the Figura mod.

It works by exporting a specifically formatted bbmodel and a lua file containing the vertex data that blockbench does not retain. Both of these files are used within a generic driver script to achieve mesh deformation in Figura.

# Installing the plugin
Download the entire repository as a zip file.

In Blender, navigate to Preferences under the Edit tab. Select Add-ons. Top right of the menu is Install. Select the zip you just downloaded. Install Addon.

Now you need to enable the installed addon. Bender should have auto filled the search bar. If it did not, search for Figura. Select the checkbox to enable the addon.

Close the plugins menu. Under File->Export you should see the option Figura Avatar. If you do not, something went wrong in an earlier step.

# Preparing your Mesh + Armature for export
The exporter expects a single Mesh object parented to an Armature object. Multiple meshes in a single armature are not supported.

Normal armature parenting is expected. If you do not know how to do that, 
* select both the Mesh and Armature object,
* Object -> Parent -> Armature Deform
* either 'With Empty Groups' or 'With Automatic Weights'.

Multiple textures on the mesh are supported. Specifically, multiple materials. However, the materials must be set up with a specific node setup.

Materials have 3 valid node setups:
* TextureNode (ShaderNodeTexImage) -> Material Output
* TextureNode (ShaderNodeTexImage) -> Principled BSDF (ShaderNodeBsdfPrincipled) -> Material Output
* Principled BSDF (ShaderNodeBsdfPrincipled) -> Material Output
  * This results in a 1x1 Solid Color texture being exported

Any other node setup will result in a 16x16 Missing Texture being exported.

Any animations present *will not be exported*. This plugin does not convert Blender animations to Blockbench animations. I've tried and it's not simple at all. If you want that functionality, either code it yourself and make a pull request, or point me to a plugin that already does it so I can steal it.

A blender model with the correct setup is avaiable in the [example folder](example), so if my explaination did not make sense, you have a visual aid to compare with.

Also, a working Figura Avatar using that example blender model is in there as well.

# Exporting your Mesh + Armature
Before exporting, be in Object mode and select your mesh object.

Then you can do File -> Export -> Figura Avatar.

For the first export, you want to have 'Export with driver code' on the right side of the window enabled.<br>
'Export with driver code' will put 'KattMeshDeformation.lua' in the same location as the exported bbmodel and mesh data file. More on that later.

You can then select the location you want to export the mesh to. I would recommend the avatar folder that will be using the mesh.

Keep an eye out for any errors that pop up.
* Active Object is not a Mesh
  * You do not have a mesh slected. Multi-select is not valid.
* Active Mesh must be Parented to an Armature
  * The exporter only supports exporting meshes with armatures. Otherwise, what is the point? You can just export as an obj and import that directly into blockbench.
* Active Mesh must have at least 1 material
  * Your mesh has no materials associated with it. The exporter cannot function with zero materials.

There should now be 3 files at the location where you exported. `x.bbmodel`, `x-MeshData.lua`, and `KattMeshDeformation.lua`, where `x` is the name you provided during export.

# Getting it working in Figura
For the duration of this section, I will explain things as if you exported the model with the name `HatsuneMiku`. So `HatsuneMiku.bbmodel` and `HatsuneMiku-MeshData.lua`.

If you havn't already, place all 3 files in your avatar folder. They must be in the root of your avatar. IE, they cannot be in any subfolders.

Then open one of ***your*** script files. It cannot be `HatsuneMiku-MeshData.lua` or `KattMeshDeformation.lua`. If those are your only 2 script files, create a new one named `script.lua`

In that script file, put `require("KattMeshDeformation")("name")`, replacing `name` with the name of the bbmodel without the `.bbmodel`.<br>
Mine is `HatsuneMiku` so I will do `require("KattMeshDeformation")("HatsuneMiku")`

And that is it. Your mesh will now deform based on the armature and vertex weights defined in blockbench. You can modify the ModelParts in the bbmodel via script or Blockbench Animations and the mesh will deform based on those changes.

# Vanilla ParentTypes
ParentTypes/Keywords that change the position/rotation of a ModelPart are not supported by this script. What I mean is naming a group `Head` to follow the vanilla head transformations. The fix is to `setPos` the bones via script using the values returned by `getOriginRot` and `getOriginPos`.

For example, to make a bone follow the vanilla head's rotation
```lua
function events.render(delta, context)
  models.HatsuneMiku.Spine1.Spine2.Spine3.Head:setRot(vanilla_model.HEAD:getOriginRot())
end
```
# BlockBench Animations
As stated somewhere above, Blender animations will not be exported from your blend file. However, the plugin still supports Blockbench animations.

Due to the way the code works, the armature and mesh are completely seperateed in blockbench. Since the groups are the things being animated and not the mesh itself, animating in blockbench can be difficult.

To fix this the plugin also provides cubes that represent the armature, making animating via blockbench feasible.

You do not need to worry about these cubes while in-game at all. The cubes have no texture, meaning they will not be loaded by figura. They will not take any file space, and are not valid ModelParts.
