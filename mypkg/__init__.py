"""rec-radio package."""

# NHK API (exceptions defined in nhk_api.py)
from .nhk_api import NHKApi, NHKApiError, NHKApiHttpError, NHKApiJsonError

# Radiko API (exceptions defined in radiko_api.py)
from .radiko_api import RadikoApi, RadikoApiError, RadikoApiHttpError, RadikoApiXmlError

# Core classes
from .program import Program
from .program_formatter import ProgramFormatter

# Recorders
from .recorder_nhk import RecorderNHK
from .recorder_radiko import RecorderRadiko

__all__ = [
    # NHK API
    "NHKApi",
    "NHKApiError",
    "NHKApiHttpError",
    "NHKApiJsonError",
    # Radiko API
    "RadikoApi",
    "RadikoApiError",
    "RadikoApiHttpError",
    "RadikoApiXmlError",
    # Core
    "Program",
    "ProgramFormatter",
    # Recorders
    "RecorderNHK",
    "RecorderRadiko",
]
