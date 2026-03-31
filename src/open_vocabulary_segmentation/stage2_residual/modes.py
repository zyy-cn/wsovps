from __future__ import annotations

from enum import Enum
from pathlib import Path


class ResidualMode(str, Enum):
    B0_DIRECT = "b0_direct"
    B1_OBJ_CONDITIONED_NO_RESIDUAL = "b1_obj_conditioned_no_residual"
    B2_RESIDUAL_ONLY = "b2_residual_only"


PP116_FIRST_DEFAULT_CONFIG_PATH = Path(
    "src/open_vocabulary_segmentation/configs/pp116/default.yml"
)


def parse_residual_mode(raw_mode: str) -> ResidualMode:
    normalized = raw_mode.strip().lower()
    try:
        return ResidualMode(normalized)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in ResidualMode)
        raise ValueError(f"unsupported residual mode: {raw_mode!r}; allowed: {allowed}") from exc


def resolve_pp116_first_config_path(config_path: str | Path | None = None) -> Path:
    resolved = Path(config_path) if config_path is not None else PP116_FIRST_DEFAULT_CONFIG_PATH
    if not resolved.exists():
        raise FileNotFoundError(f"PP116-first config path does not exist: {resolved}")
    return resolved
