from . import neurofocus as _neurofocus  # noqa: F401
from . import serial_device as _serial_device  # noqa: F401
from . import synthetic as _synthetic  # noqa: F401  (registers 'synthetic' scheme)

try:  # brainflow is an optional dependency
    from . import brainflow_device as _brainflow_device  # noqa: F401
except Exception:  # pragma: no cover
    pass
try:  # pylsl is an optional dependency
    from . import lsl_device as _lsl_device  # noqa: F401
except Exception:  # pragma: no cover
    pass
