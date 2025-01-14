from langchain.prompts import BaseChatPromptTemplate as PromptTemplate
from SARPAgent.prompt.chat_prompt import chat_prompt_registry
# from SARPAgent.prompt.chat_prompt.prompt_value import PromptValue

from langchain.schema import PromptValue
from langchain.prompts.chat import ChatPromptValue
from typing import Any

from abc import abstractmethod



# Set up a prompt template
@chat_prompt_registry.register("base_chat")
class BaseChatPromptTemplate(PromptTemplate):
    # The template to use
    template: str
    
    def format(self, **kwargs: Any) -> str:
        return self.format_prompt(**kwargs).to_string()

    def format_prompt(self, **kwargs: Any) -> PromptValue:
        messages = self.format_messages(**kwargs)
        return ChatPromptValue(messages=messages)
    
    @abstractmethod
    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
        pass