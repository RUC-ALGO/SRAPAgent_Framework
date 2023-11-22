from . import group_registry
from pydantic import BaseModel
from abc import abstractmethod

@group_registry.register("base")
class BaseGroupPolicy(BaseModel):
    
    type = "base"
    priority:bool = False
    log_fixed = {} # fixed_log for tenants : tenant_id[house_type_id,house_choose_reason]
    async def group(self,
                tenant,
                tenant_manager,
                forum_manager, 
                system, 
                tool, 
                rule,
                log_round_tenant,
                tenant_ids): # tenant_ids 为最新添加的一批tenant
        # return group_id
        return "default" # 所有tenant分在同一组
    