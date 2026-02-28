from typing import Dict, Any

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Any] = {}

    def add(self, key: str, agent: Any):
        self._agents[key] = agent

    def get(self, key: str) -> Any:
        return self._agents[key]

    def all(self) -> Dict[str, Any]:
        return dict(self._agents)