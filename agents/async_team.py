from __future__ import annotations
import asyncio
from typing import Dict, Any

class AsyncCollaborativeMusicTeam:
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents

    async def _run_one(self, key: str, agent: Any, user_text: str, **kwargs):
        res = await asyncio.to_thread(agent.run, user_text, **kwargs)
        return key, res.content

    async def run_all(self, user_text: str, **kwargs) -> Dict[str, Any]:
        tasks = [
            self._run_one(key, agent, user_text, **kwargs)
            for key, agent in self.agents.items()
        ]
        results = await asyncio.gather(*tasks)
        return {key: content for key, content in results}