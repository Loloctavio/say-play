from dataclasses import dataclass
from typing import Any, Optional, Type

from agents.prompts import BASE_SYSTEM, role_prompt

@dataclass
class AgentDefaults:
    name_prefix: str = "Music"
    markdown: bool = True

class BaseMusicAgentBuilder:
    def __init__(
        self,
        *,
        model: Any,
        defaults: AgentDefaults = AgentDefaults(),
        output_schema: Optional[Type[Any]] = None,
        tools: Optional[list[Any]] = None,
    ):
        self.model = model
        self.defaults = defaults
        self.output_schema = output_schema
        self.shared_tools = tools or []

    def build(
        self,
        *,
        name: str,
        role: str,
        extra_instructions: str = "",
        tools: Optional[list[Any]] = None,
        **kwargs,
    ):
        from agno.agent import Agent
        instructions = "\n\n".join([
            BASE_SYSTEM.strip(),
            role_prompt(role).strip(),
            extra_instructions.strip(),
        ]).strip()

        return Agent(
            name=f"{self.defaults.name_prefix}:{name}",
            model=self.model,
            instructions=instructions,
            tools=[*self.shared_tools, *(tools or [])],
            markdown=self.defaults.markdown,
            output_schema=self.output_schema,
            **kwargs,
        )