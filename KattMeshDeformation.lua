return function(meshData)
  local model = models[meshData.modelName]
  local figuraVertices = model.Mesh:getAllVertices()
  local vertices = {}
  for index, data in ipairs(meshData.vertexData) do
    vertices[index] = {
      verts = {},
      groupWeights = data.weights
    }
    for textureIndex, loopData in pairs(data.loops) do
      for _, vert in ipairs(loopData) do
        table.insert(vertices[index].verts,
          figuraVertices[("%s.%s"):format(meshData.modelName, meshData.textureMap[textureIndex])][vert])
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
          modelPart = modelPart,
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
      local mat = bone.modelPart:getPositionMatrix():multiply(parentMat)
      map[bone.index] = mat
      for i = 1, #bone do
        generateMatrixMap(bone[i], map, mat)
      end
    end

    local insert = table.insert
    local vec3 = vectors.vec3
    local mat4 = matrices.mat4
    function events.render()
      local boneMats = {}
      for i = 1, #boneTree do
        generateMatrixMap(boneTree[i], boneMats, mat4())
      end
      for index, vertData in ipairs(vertices) do
        local t = {}
        for groupIndex, weight in pairs(vertData.groupWeights) do
          insert(t, boneMats[groupIndex]:apply(vertData.pos) * weight)
        end
        local sum = vec3()
        for i = 1, #t do
          sum = sum + t[i]
        end
        local verts = vertData.verts
        for i = 1, #verts do
          verts[i]:setPos(sum)
        end
      end
    end
  end
end
