from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, List, Optional

from pydantic import BaseModel
import random
from LLM_PublicHouseAllocation.environments.rules.order import BaseOrder, order_registry
from LLM_PublicHouseAllocation.environments.rules.visibility import BaseVisibility, visibility_registry
from LLM_PublicHouseAllocation.environments.rules.updater import BaseUpdater, updater_registry
from LLM_PublicHouseAllocation.environments.rules.describer import BaseDescriber, describer_registry


if TYPE_CHECKING:
    from LLM_PublicHouseAllocation.environments.base import BaseEnvironment

from LLM_PublicHouseAllocation.message import Message


class Rule(BaseModel):
    """
    Rule for the environment. It controls the speaking order of the agents 
    and maintain the set of visible agents for each agent.
    """
    order: BaseOrder
    visibility: BaseVisibility
    updater: BaseUpdater
    describer: BaseDescriber

    def __init__(self, 
                 order_config,
                 updater_config,
                 visibility_config,
                 describer_config
                 ):
        order = order_registry.build(**order_config)
        updater = updater_registry.build(**updater_config)
        visibility = visibility_registry.build(**visibility_config)
        describer = describer_registry.build(**describer_config)
        super().__init__(order=order,
                         updater=updater,
                         visibility=visibility,
                         describer=describer)

    def get_next_agent_idx(self, environment: BaseEnvironment) -> List[int]:
        """Return the index of the next agent to speak"""
        return self.order.get_next_agent_idx(environment)

    def generate_deque(self, environment):
        return self.order.generate_deque(environment)

    def requeue(self, environment, tenant):
        self.order.requeue(environment,tenant)

    def reset(self, environment: BaseEnvironment) -> None:
        self.order.reset()
        
    def post_messages(self,**kargs):
        self.updater.post_messages(**kargs)