local weights=require("blendWeight")
local model=models.test
local function findGroup(name, modelPart)
  if not modelPart then modelPart=model
  elseif name==modelPart:getName() then
    return modelPart
  end
  local children=modelPart:getChildren()
  if #children~=0 then
    for _, child in ipairs(children) do
      if child:getType()=="GROUP" then
        local val=findGroup(name,child)
        if val then return val end
      end
    end
  end
  return false
end

function events.render()
  for index, value in ipairs(t) do
    
  end
end