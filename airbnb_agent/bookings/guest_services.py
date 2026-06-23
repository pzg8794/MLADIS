"""Bridge for the object-driven Guests service.

The project still has a legacy ``bookings.services`` module, so importing
``bookings.services.guests`` directly would require a broad package migration.
This bridge keeps the requested service implementation in
``bookings/services/guests.py`` while avoiding that risky import change.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


_SERVICE_PATH = Path(__file__).with_name("services") / "guests.py"
_SPEC = importlib.util.spec_from_file_location("bookings_guest_services_impl", _SERVICE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Could not load Guests service from {_SERVICE_PATH}")

_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)

Guest = _MODULE.Guest
GuestAnalyticsService = _MODULE.GuestAnalyticsService
GuestDataLakeService = _MODULE.GuestDataLakeService
GuestMessageService = _MODULE.GuestMessageService
GuestService = _MODULE.GuestService
GuestTimelineService = _MODULE.GuestTimelineService
