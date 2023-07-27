return function(meshData)
  if type(meshData) == "string" then
    local file, found = meshData, nil
    found, meshData = pcall(require, file)
    if not found then
      found, meshData = pcall(require, ("%s-MeshData"):format(file))
      if not found then
        error(("MeshData %q could not be found."):format(file), 2)
      end
    end
  end
  local modelName, vertexData, groupMap, textureMap = meshData.modelName, meshData.vertexData, meshData.groupMap, meshData.textureMap
  local model = models[modelName]
  local figuraVertices = model.Mesh:getAllVertices()
  local vertices = {}
  local modelTextureFString = modelName..".%s"
  for index, data in ipairs(vertexData) do
    local vertex = {}
    local vertexObjects = {}
    for textureIndex, loopData in pairs(data.loops) do
      local textureVertices = figuraVertices[modelTextureFString:format(textureMap[textureIndex])]
      for _, vert in ipairs(loopData) do
        table.insert(vertexObjects, textureVertices[vert])
      end
    end
    vertex.verts = vertexObjects
    if data.weights then
      local groupSum = 0
      for _, weight in pairs(data.weights) do
        groupSum = groupSum + weight
      end
      local groupWeights = {}
      for key, weight in pairs(data.weights) do
        groupWeights[key] = 1 / groupSum * weight
      end
      vertex.groupWeights = groupWeights
    end
    vertex.pos = vertex.verts[1]:getPos()
    vertices[index] = vertex
  end

  local boneTree = {}
  do
    local function generateBoneTree(modelPart, parentIndex)
      local groupIndex = groupMap[modelPart:getName()]
      if groupIndex then
        local a = {
          parent = parentIndex,
          index = groupIndex,
          modelPart = modelPart:setParentType("None"),
        }
        table.insert(boneTree, a)
        for _, child in ipairs(modelPart:getChildren()) do
          if child:getType() == "GROUP" then
            generateBoneTree(child, a.index)
          end
        end
      end
    end
    for _, child in ipairs(model:getChildren()) do
      if child:getType() == "GROUP" then
        generateBoneTree(child)
      end
    end
  end
  do
    local vec3 = vectors.vec3
    local mat4 = matrices.mat4()
    function events.render()
      local boneMats = {}
      for _, bone in ipairs(boneTree) do
        boneMats[bone.index] = (boneMats[bone.parent] or mat4) * bone.modelPart:getPositionMatrix()
      end
      for _, vertData in ipairs(vertices) do
        if vertData.groupWeights then
          local weightSum = vec3()
          for groupIndex, weight in pairs(vertData.groupWeights) do
            weightSum = weightSum + (boneMats[groupIndex]:apply(vertData.pos) * weight)
          end
          for _, vert in ipairs(vertData.verts) do
            vert:setPos(weightSum)
          end
        end
      end
    end
  end
end
