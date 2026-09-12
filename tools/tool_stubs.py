"""
AgentGuard - Tool bridge for the LangGraph pipeline.

These 4 functions are imported directly by the pipeline. Signatures and return
formats are locked per the spec - do not rename, do not change params, do not
change return shapes without a coordinated change to the pipeline caller.
"""
from camara.sim_swap import check_sim_swap
from camara.device_status import check_device_status
from camara.device_swap import check_device_swap
from camara.number_verification import trigger_number_verification

__all__ = [
    "check_sim_swap",
    "check_device_status",
    "check_device_swap",
    "trigger_number_verification",
]