from __future__ import annotations

from typing import TYPE_CHECKING, Any, List

from pydantic import BaseModel

from . import describer_registry as DescriberRegistry

if TYPE_CHECKING:
    from LLM_PublicHouseAllocation.environments import BaseEnvironment


@DescriberRegistry.register("base")
class BaseDescriber(BaseModel):

    def reset(self) -> None:
        pass