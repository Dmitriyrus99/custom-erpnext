"""Lightweight in-memory Frappe test double.

This module provides a very small subset of the Frappe API that is required by
the unit tests that ship with this kata.  The real Frappe framework is far too
heavy to install in the execution environment used for the exercises, so the
tests interact with this shim instead.  Only the behaviour that is exercised by
the tests is implemented which keeps the surface area intentionally tiny while
still feeling familiar to anyone who has used Frappe before.
"""

from __future__ import annotations

import copy
import datetime as _dt
import importlib
import traceback
from typing import Any, MutableMapping

__all__ = [
        "Document",
        "ValidationError",
        "_",
        "db",
        "enqueue",
        "get_all",
        "get_doc",
        "get_list",
        "get_roles",
        "log_error",
        "logger",
        "msgprint",
        "new_doc",
        "sendmail",
        "session",
        "set_user",
        "throw",
        "whitelist",
]


class ValidationError(Exception):
        """Exception raised by :func:`throw`."""


def _(text: str) -> str:
        """Translate text.  The test double simply returns the text unchanged."""

        return text


def throw(message: str) -> None:
        raise ValidationError(message)


def msgprint(message: str) -> None:  # pragma: no cover - side effect only
        """Display a message to the user (no-op in the shim)."""


def log_error(message: str, title: str | None = None) -> None:  # pragma: no cover - side effect only
        """Record an error message.  The shim stores it in memory for introspection."""

        _error_log.append((title, message))


def sendmail(*_, **__):  # pragma: no cover - transport side effect only
        """Pretend to send an email."""


def enqueue(*_, **__):  # pragma: no cover - background job side effect only
        """Pretend to enqueue a background job."""


def whitelist(arg: Any | None = None, **__: Any):
        """Decorator used by Frappe to expose functions via RPC."""

        def decorator(func):
                return func

        if callable(arg):
                return decorator(arg)
        return decorator


def get_traceback() -> str:
        return "".join(traceback.format_exception(*traceback.sys.exc_info()))


class _Logger:
        def info(self, *_: Any, **__: Any) -> None:  # pragma: no cover - diagnostics only
                pass

        def warning(self, *_: Any, **__: Any) -> None:  # pragma: no cover - diagnostics only
                pass

        def exception(self, *_: Any, **__: Any) -> None:  # pragma: no cover - diagnostics only
                pass


def logger() -> _Logger:  # pragma: no cover - diagnostics only
        return _Logger()


class _Session:
        user: str = "Administrator"


session = _Session()

_user_roles: dict[str, list[str]] = {"Administrator": ["System Manager"]}
_error_log: list[tuple[str | None, str]] = []


def set_user(user: str) -> None:
        session.user = user


def get_roles(user: str | None = None) -> list[str]:
        user = user or session.user
        return list(_user_roles.get(user, []))


def add_user_role(user: str, role: str) -> None:
        roles = _user_roles.setdefault(user, [])
        if role not in roles:
                roles.append(role)


def scrub(value: str) -> str:
        return value.replace(" ", "_").replace("/", "_").lower()


def _guess_doctype(module: str, class_name: str) -> str:
        if ".doctype." in module:
                slug = module.split(".doctype.", 1)[1].split(".", 1)[0]
                return " ".join(part.capitalize() for part in slug.split("_"))
        # Fall back to the class name when we cannot derive it from the module
        return " ".join(_split_camel_case(class_name))


def _split_camel_case(name: str) -> list[str]:
        parts: list[str] = []
        start = 0
        for index, char in enumerate(name):
                if index and char.isupper():
                        parts.append(name[start:index])
                        start = index
        parts.append(name[start:])
        return [part.capitalize() for part in parts if part]


_doctype_registry: dict[str, type["Document"]] = {}


def _register_doctype(doctype: str, cls: type["Document"]) -> None:
        _doctype_registry[doctype] = cls


def _get_doctype_class(doctype: str) -> type["Document"] | None:
        return _doctype_registry.get(doctype)


def _load_doctype_module(doctype: str) -> None:
        if _get_doctype_class(doctype):
                return
        slug = scrub(doctype)
        module_path = f"ferum_custom.ferum_custom.doctype.{slug}.{slug}"
        try:
                importlib.import_module(module_path)
        except ModuleNotFoundError:
                # Not all doctypes are implemented in the repository.  Those
                # missing ones fall back to a generic Document implementation.
                pass


class _Database:
        def __init__(self) -> None:
                self.reset()

        def reset(self) -> None:
                self._data: dict[str, dict[str, dict[str, Any]]] = {}
                self._autoname: dict[str, int] = {}
                # Bootstrap core records required by the tests
                self.upsert(
                        "User",
                        "Administrator",
                        {
                                "email": "administrator@example.com",
                                "first_name": "Administrator",
                                "user_type": "System User",
                                "enabled": 1,
                        },
                )
                add_user_role("Administrator", "System Manager")
                self.upsert("Role", "Client", {"desk_access": 0})

        # -- storage helpers -------------------------------------------------
        def upsert(self, doctype: str, name: str, data: MutableMapping[str, Any]) -> None:
                stored = copy.deepcopy(dict(data))
                stored["name"] = name
                stored.setdefault("owner", "Administrator")
                self._data.setdefault(doctype, {})[name] = stored

        def generate_name(self, doctype: str) -> str:
                prefix = "".join(part[0].upper() for part in doctype.split() if part)
                counter = self._autoname.setdefault(doctype, 0) + 1
                self._autoname[doctype] = counter
                return f"{prefix}-{counter:05d}" if prefix else f"AUTO-{counter:05d}"

        def insert(self, doc: "Document") -> None:
                if not doc.name:
                        doc.name = self.generate_name(doc.doctype)
                self._data.setdefault(doc.doctype, {})[doc.name] = doc._snapshot()

        def update(self, doc: "Document") -> None:
                if doc.name not in self._data.get(doc.doctype, {}):
                        raise ValidationError(f"Document {doc.doctype} {doc.name} does not exist")
                self._data[doc.doctype][doc.name] = doc._snapshot()

        def get_doc_data(self, doctype: str, name_or_filters: Any) -> dict[str, Any] | None:
                if isinstance(name_or_filters, str):
                        record = self._data.get(doctype, {}).get(name_or_filters)
                        return copy.deepcopy(record) if record else None
                if isinstance(name_or_filters, dict):
                        for record in self._data.get(doctype, {}).values():
                                if _match_filters(record, name_or_filters):
                                        return copy.deepcopy(record)
                        return None
                raise TypeError("name_or_filters must be a string or mapping")

        # -- query helpers ---------------------------------------------------
        def exists(self, doctype: str, filters: Any) -> bool:
                return self.get_doc_name(doctype, filters) is not None

        def get_doc_name(self, doctype: str, filters: Any) -> str | None:
                if isinstance(filters, str):
                        return filters if filters in self._data.get(doctype, {}) else None
                if isinstance(filters, dict):
                        for name, record in self._data.get(doctype, {}).items():
                                if _match_filters(record, filters):
                                        return name
                return None

        def get_value(
                self,
                doctype: str,
                filters: Any,
                fieldname: str | Iterable[str] | None = None,
                *,
                as_dict: bool = False,
        ) -> Any:
                record = self.get_doc_data(doctype, filters)
                if not record:
                        return None
                if fieldname is None:
                        return record.get("name")
                if isinstance(fieldname, (list, tuple)):
                        result = {field: record.get(field) for field in fieldname}
                        return result if as_dict else tuple(result.values())
                value = record.get(fieldname)
                if as_dict:
                        return {fieldname: value}
                return value

        def set_value(self, doctype: str, name: str, field: Any, value: Any | None = None) -> None:
                record = self._data.get(doctype, {}).get(name)
                if not record:
                        raise ValidationError(f"Document {doctype} {name} not found")
                updates: dict[str, Any]
                if isinstance(field, dict):
                        updates = field
                else:
                        updates = {field: value}
                record.update(copy.deepcopy(updates))
                record["modified"] = _dt.datetime.now()

        def get_all(
                self,
                doctype: str,
                *,
                filters: dict[str, Any] | None = None,
                pluck: str | None = None,
        ) -> list[Any]:
                records = []
                for record in self._data.get(doctype, {}).values():
                        if filters and not _match_filters(record, filters):
                                continue
                        if pluck:
                                records.append(record.get(pluck))
                        else:
                                records.append(copy.deepcopy(record))
                return records

        def get_list(
                self,
                doctype: str,
                *,
                filters: dict[str, Any] | None = None,
                pluck: str | None = None,
        ) -> list[Any]:
                return self.get_all(doctype, filters=filters or {}, pluck=pluck)

        def sql(
                self,
                *_: Any,
                **__: Any,
        ) -> list[Any]:  # pragma: no cover - simple stub
                return []


def _match_filters(record: MutableMapping[str, Any], filters: dict[str, Any]) -> bool:
        for field, expected in filters.items():
                value = record.get(field)
                if isinstance(expected, (list, tuple)) and expected:
                        operator = expected[0]
                        operand = expected[1] if len(expected) > 1 else None
                        if operator == "in":
                                if value not in set(operand or []):
                                        return False
                        elif operator == "not in":
                                if value in set(operand or []):
                                        return False
                        else:
                                raise NotImplementedError(f"Unsupported operator {operator!r}")
                else:
                        if value != expected:
                                return False
        return True


db = _Database()


# ``Document`` and helpers are imported at the bottom of the module to avoid
# circular import issues.  The class lives in ``frappe.model.document`` but the
# majority of the shim interacts with it via this module.
from .model.document import Document, get_document_class  # noqa: E402  (import at end of file)


def new_doc(doctype: str) -> "Document":
        _load_doctype_module(doctype)
        cls = get_document_class(doctype)
        return cls(doctype=doctype)


def get_doc(doctype: str, name_or_filters: Any) -> "Document":
        _load_doctype_module(doctype)
        cls = get_document_class(doctype)
        data = db.get_doc_data(doctype, name_or_filters)
        if data is None:
                raise ValidationError(f"Document {doctype} not found")
        return cls(data=data, doctype=doctype, is_new=False)


def get_all(
        doctype: str,
        *,
        filters: dict[str, Any] | None = None,
        pluck: str | None = None,
) -> list[Any]:
        return db.get_all(doctype, filters=filters or {}, pluck=pluck)


def get_list(
        doctype: str,
        *,
        filters: dict[str, Any] | None = None,
        pluck: str | None = None,
        ignore_permissions: bool | None = None,  # noqa: ARG001 - matches API
) -> list[Any]:
        _ = ignore_permissions
        return db.get_list(doctype, filters=filters or {}, pluck=pluck)
