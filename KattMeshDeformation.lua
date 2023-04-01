return function(meshData)
  if type(meshData)=="string" then
    meshData=require(meshData)
  end
  local model = models[meshData.modelName]
  local figuraVertices = model.Mesh:getAllVertices()
  local vertices = {}
  for index, data in ipairs(meshData.vertexData) do
    vertices[index] = {
      verts = {},
    }
    for textureIndex, loopData in pairs(data.loops) do
      for _, vert in ipairs(loopData) do
        table.insert(vertices[index].verts,
          figuraVertices[("%s.%s"):format(meshData.modelName, meshData.textureMap[textureIndex])][vert])
      end
    end
    if next(data.weights) then
      local groupSum=0
      for _, weight in pairs(data.weights) do
        groupSum=groupSum+weight
      end
      vertices[index].groupWeights={}
      for key, weight in pairs(data.weights) do
        vertices[index].groupWeights[key]=1/groupSum*weight
      end
    end
    vertices[index].pos = vertices[index].verts[1]:getPos()
  end

  local boneTree = {}
  do
    local function generateBoneTree(modelPart, parentTable)
      local groupIndex = meshData.groupMap[modelPart:getName()]
      if groupIndex then
        local a = {
          index = groupIndex,
          modelPart = modelPart:setParentType("None"),
        }
        for _, child in ipairs(modelPart:getChildren()) do
          if child:getType() == "GROUP" then
            generateBoneTree(child, a)
          end
        end
        table.insert(parentTable, a)
      end
    end
    for _, child in ipairs(model:getChildren()) do
      if child:getType() == "GROUP" then
        generateBoneTree(child, boneTree)
      end
    end
  end
  do
    local function generateMatrixMap(bone, map, parentMat)
      local mat = parentMat*bone.modelPart:getPositionMatrix()
      map[bone.index] = mat
      for i = 1, #bone do
        generateMatrixMap(bone[i], map, mat)
      end
    end

    local vec3 = vectors.vec3
    local mat4 = matrices.mat4
    function events.render()
      local boneMats = {}
      for i = 1, #boneTree do
        generateMatrixMap(boneTree[i], boneMats, mat4())
      end
      for _, vertData in ipairs(vertices) do
        if vertData.groupWeights then
          local weightSum = vec3()
          for groupIndex, weight in pairs(vertData.groupWeights) do
            weightSum=weightSum + (boneMats[groupIndex]:apply(vertData.pos) * weight)
          end
          for _, vert in ipairs(vertData.verts) do
            vert:setPos(weightSum)
          end
        end
      end
    end
  end
end
