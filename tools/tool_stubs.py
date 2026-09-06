"""
AgentGuard - Tool bridge for Amer's LangGraph pipeline.

Amer imports these 4 functions directly. Signatures and return formats are
locked per the spec - do not rename, do not change params, do not change
return shapes. If something needs to change here, that's a conversation with
Ghaith first, not a unilateral edit.
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