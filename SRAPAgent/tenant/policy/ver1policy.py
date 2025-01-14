from . import policy_registry
from .base import BasePolicy


@policy_registry.register("ver1")
class Ver1Policy(BasePolicy):

    def __init__(self,**kargs) -> None:
        return super().__init__(type = "ver1",
                                **kargs)
    
    async def choose_pipeline(self,
                       tenant,
                       forum_manager, 
                        system, 
                        tool, 
                        rule,
                        log_round):

        log_round.set_tenant_information(tenant.id,tenant.name,tenant.max_choose - tenant.choose_times)
        search_infos = tenant.search_forum(forum_manager=forum_manager,
                                         system=system)


        choose_state, community_id, community_choose_reason = await tenant.choose_community(system,search_infos,rule)
        log_round.set_choose_community(community_id,community_choose_reason)
        
        if not choose_state:
            await tenant.publish_forum(forum_manager,system)
            return False,"None"
        
        house_filter_ids = {}
        for filter_label in self.filter_house_labels:
            if filter_label == "house_type":
                if self.group_policy.type in ["multi_list","house_type"]:
                    choose_state, house_type_id, house_type_reason = True,\
                        tenant.queue_name, "Choose house type according to the policy"
                else:
                    choose_state, house_type_id, house_type_reason = await tenant.choose_house_type(system,rule,community_id)
                
                log_round.set_choose_house_type(house_type_id,house_type_reason)
                house_filter_ids["house_type"] = house_type_id
                
            elif filter_label == "house_orientation":
                choose_state, filter_id, reason = await tenant.choose_orientation(system,rule,community_id)
                log_round.set_choose_house_orientation(filter_id, reason)
                house_filter_ids["house_orientation"] = filter_id
                
            elif filter_label == "floor_type":
                choose_state, filter_id, reason = await tenant.choose_floor(system,rule,community_id)
                log_round.set_choose_floor_type(filter_id, reason)
                house_filter_ids["floor_type"] = filter_id
            else:
                assert NotImplementedError
                
            if not choose_state:
                await tenant.publish_forum(forum_manager,system)
                return False,"None"
        
            
        choose_state, house_id, house_choose_reason = await tenant.choose_house(
                                                   system,
                                                   community_id,
                                                   house_filter_ids)

        log_round.set_choose_house(house_id,house_choose_reason)
        
        await tenant.publish_forum(system=system,
                           forum_manager=forum_manager)

             
        if not choose_state:
            return False,"None"
        
        # 更改communitymanager中的remain_num
        system.set_chosed_house(house_id,community_id,tenant.queue_name,house_filter_ids)

        return True,house_id.lower()