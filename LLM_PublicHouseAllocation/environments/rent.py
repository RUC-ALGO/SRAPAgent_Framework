import asyncio
import logging
from typing import List, Deque, Optional
from LLM_PublicHouseAllocation.tenant.multiprompt_tenant import BaseMultiPromptTenant
from LLM_PublicHouseAllocation.tenant.langchain_tenant import LangchainTenant
import json
from LLM_PublicHouseAllocation.manager import TenantManager,ForumManager
from LLM_PublicHouseAllocation.involvers import System,Tool,Search_forum_topk,LogRound
from . import env_registry as EnvironmentRegistry
from .base import BaseEnvironment
import copy
@EnvironmentRegistry.register("rent")
class RentEnvironment(BaseEnvironment):
    """
    A environment implementing the logic of conversation.

    Args:
        agents: tenant_manager
        rule: Rule for the environment
        max_turns: Maximum number of turns
        cnt_turn: Current turn number
        last_messages: Messages from last turn
        rule_params: Variables set by the rule
    """
    tenant_manager: TenantManager
    forum_manager: ForumManager
    system: System
    tool: Optional[Tool] = None
    deque: Optional[Deque] = None
    log:Optional[LogRound]=None
    class Config:
        arbitrary_types_allowed = True

    def __init__(self, rule,**kwargs):

        super().__init__(rule=rule, **kwargs)

    def line_up(self):
        self.deque=self.rule.generate_deque(self)

    def broadcast(self):
        self.tenant_manager.broadcast(self.system)

    def reset(self) -> None:
        """Reset the environment"""
        self.deque.clear()
        self.rule.reset(self)
        self.tenant_manager.reset()
        self.system.reset()
        self.cnt_turn = 0

    def is_done(self) -> bool:
        """Check if the environment is done"""
        self.log.set_log_list()
        self.log.save_data()
        cur,fur=self.system.community_manager.split(self.system.community_manager.get_available_community_info())
        if (cur==[] and fur==[] ) or len(self.deque)==0:
            return False
        else:
            self.forum_manager.save_data()
            self.save_tenant_memory()
            return True

    #test 测试用 要改
    def communication(self):
        tenant_ids = list(self.tenant_manager.data.keys())
        # tenant_ids = tenant_ids[:2] # test
        
        for tenant_id in tenant_ids:
            tenant = self.tenant_manager.data[tenant_id]
            if isinstance(tenant, LangchainTenant):
                asyncio.run(tenant.async_communication(self.forum_manager, self.system,self.log,3))
            else:
                raise NotImplementedError("Tenant type {} not implemented".format(tenant.__class__))
        #return self.log_round

    def step(self):
        tenant = self.rule.get_next_agent_idx(self)
        
        if isinstance(tenant, LangchainTenant):
            choose_state= tenant.choose_process(self.forum_manager, self.system, self.tool, self.log)
        elif isinstance(tenant,BaseMultiPromptTenant):
            choose_state = tenant.choose(self.forum_manager, self.system, self.log)
        else:
            raise NotImplementedError("Tenant type {} not implemented".format(tenant.__class__))
        if not choose_state and tenant.available==True:
            self.deque.append(tenant)
        
        self.update_social_net(tenant=tenant)
        
        self.cnt_turn += 1
        if (self.cnt_turn+1) %5==0:
            self.system.community_manager.publish_community()
    
        return self.log
    
    def update_social_net(self,tenant):
        assert isinstance(tenant,LangchainTenant)
        post_messages = tenant.post_messages()
        
        self.rule.post_messages(post_messages=post_messages,
                                tenant_manager=self.tenant_manager)

    def save_tenant_memory(self, dir="LLM_PublicHouseAllocation/tasks/PHA_50tenant_3community_19house/result/tenant_memory.json"):
        log_memory={}
        for tenant_id,tenant in self.tenant_manager.data.items():
            assert isinstance(tenant,LangchainTenant)
            memory_temp=copy.deepcopy(tenant.memory)
            memory_tenant = {"messages":memory_temp.messages,
                             "summarys":memory_temp.summarys,
                             "received_messages":memory_temp.received_messages,
                             "received_summarys":memory_temp.received_summarys,
                             "post_message_buffer":memory_temp.post_message_buffer
                             }
            for k,v in memory_tenant.items():
                if isinstance(v,list):
                    v=[str(v_) for v_ in v]
                elif isinstance(v,dict):
                    for m_k,m_v in v.items():
                      if isinstance(m_v,list):
                        m_v=[str(m_v_) for m_v_ in m_v]  
                        v[m_k]=m_v
                memory_tenant[k]=v
                        
            log_memory[tenant_id]=memory_tenant
        with open(dir, encoding='utf-8', mode='w') as fr:
            json.dump(log_memory, fr, indent=4, separators=(',', ':'), ensure_ascii=False)





