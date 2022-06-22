"""This module contains base class for secret adapter."""

import typing as _t
from abc import ABC
from abc import abstractmethod


class BaseSecret(ABC):
    """Base class for secret adapter.

    Must be sub-classed per implementation details.
    """

    @property
    def type(self) -> str:
        """Name of the configuration type.

        This attribute always returns ``secret``.
        """
        return "secret"

    @abstractmethod
    def get(self, key: str, default: _t.Any = "") -> _t.Any:
        """Get specific secret.

        Subclass **MUST** implement this method.
        """

    @abstractmethod
    def set(self, key: str, value: _t.Any) -> bool:
        """Set specific secret.

        Subclass **MUST** implement this method.
        """

    def all(self) -> dict[str, _t.Any]:  # pragma: no cover
        """Get all secrets (deprecated in favor of ``get_all``)."""
        return self.get_all()

    @abstractmethod
    def set_all(self, data: dict[str, _t.Any]) -> bool:
        """Set all secrets.

        Subclass **MUST** implement this method.
        """

    @abstractmethod
    def get_all(self) -> dict[str, _t.Any]:
        """Get all secrets.

        Subclass **MUST** implement this method.
        """
