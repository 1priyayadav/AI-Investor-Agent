from typing import Callable, Any

from backend.utils.logger import logger


class AgentSupervisor:
    """
    Supervisor responsible for executing agents, validating outputs,
    and enforcing a maximum of 3 retries on failures or schema errors.
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def execute_with_retry(self, node_name: str, agent_func: Callable, state: dict) -> dict:
        retries = state.get("retry_counts", {}).get(node_name, 0)

        try:
            logger.info(f"Supervisor: Executing {node_name} (Attempt {retries + 1})")

            new_state_updates = agent_func(state)

            if "retry_counts" not in state:
                state["retry_counts"] = {}
            state["retry_counts"][node_name] = 0

            logs = [f"{node_name} completed successfully."]
            new_state_updates["agent_logs"] = logs
            return new_state_updates

        except Exception as e:
            logger.error(f"Supervisor: {node_name} failed. Error: {e}")
            retries += 1

            retry_state = state.get("retry_counts", {})
            retry_state[node_name] = retries

            if retries >= self.max_retries:
                logger.error(f"Supervisor: {node_name} exceeded max retries. Escalating.")
                return {
                    "retry_counts": retry_state,
                    "agent_logs": [f"CRIT: {node_name} failed permanently after {self.max_retries} retries."],
                }
            return {
                "retry_counts": retry_state,
                "agent_logs": [f"WARN: {node_name} failed. Initiating retry..."],
            }


__all__ = ["AgentSupervisor"]
