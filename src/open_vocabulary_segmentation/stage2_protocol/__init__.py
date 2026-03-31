"""Stage-2 Oracle-Obj protocol landing scaffold.

The package intentionally stays thin: it exposes protocol contracts and
descriptor factories for the approved E3 design pack without implementing
residual-part logic or scientific validation.
"""

from .contracts import (
    EvaluatorBindingSpec,
    ObjectSupportSpec,
    Stage2ProtocolDescriptor,
)
from .ade234_binding import ADE234_PROTOCOL_ID, build_ade234_protocol_descriptor
from .evaluator_binding import build_stage2_protocol, resolve_stage2_evaluator_binding
from .pp116_binding import PP116_PROTOCOL_ID, build_pp116_protocol_descriptor

__all__ = [
    "ADE234_PROTOCOL_ID",
    "EvaluatorBindingSpec",
    "ObjectSupportSpec",
    "PP116_PROTOCOL_ID",
    "Stage2ProtocolDescriptor",
    "build_ade234_protocol_descriptor",
    "build_pp116_protocol_descriptor",
    "build_stage2_protocol",
    "resolve_stage2_evaluator_binding",
]
