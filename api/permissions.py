"""Compatibility imports; permissions are owned by the relevant feature apps."""

from drivers.permissions import IsDriver, IsDriverAccount
from operations.permissions import IsStaffAdmin

__all__ = ["IsDriver", "IsDriverAccount", "IsStaffAdmin"]
