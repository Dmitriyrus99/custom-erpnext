"""Minimal :mod:`frappe.model.document` implementation for the tests."""

from __future__ import annotations

import copy
from types import SimpleNamespace
from typing import Any

import frappe
import frappe.utils
from frappe import _get_doctype_class, _guess_doctype, _register_doctype


class DocumentMeta(type):
        def __new__(mcls, name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> type:
                cls = super().__new__(mcls, name, bases, attrs)
                if not attrs.get("__register__", True):
                        return cls
                doctype = attrs.get("doctype") or _guess_doctype(attrs.get("__module__", ""), name)
                cls.doctype = doctype  # type: ignore[attr-defined]
                _register_doctype(doctype, cls)  # type: ignore[arg-type]
                return cls


class Document(metaclass=DocumentMeta):
        """A tiny drop-in stand-in for :class:`frappe.model.document.Document`."""

        __register__ = False  # prevent registration of the base class itself

        def __init__(
                self,
                *,
                data: dict[str, Any] | None = None,
                doctype: str | None = None,
                is_new: bool = True,
        ) -> None:
                self.doctype = doctype or getattr(self, "doctype")
                self.name: str | None = None
                self.owner = frappe.session.user
                self.docstatus = 0
                self.creation = frappe.utils.now_datetime()
                self.modified = self.creation
                self._is_new = is_new
                self._original_values: dict[str, Any] = {}
                if data:
                        self._load(data)
                        self._original_values = self._snapshot()

        # -- helpers ---------------------------------------------------------
        def _load(self, data: dict[str, Any]) -> None:
                for key, value in data.items():
                        if key.startswith("_"):
                                continue
                        setattr(self, key, self._coerce_value(value))

        def _coerce_value(self, value: Any) -> Any:
                if isinstance(value, list):
                        coerced = []
                        for item in value:
                                if isinstance(item, dict):
                                        coerced.append(SimpleNamespace(**item))
                                else:
                                        coerced.append(copy.deepcopy(item))
                        return coerced
                return copy.deepcopy(value)

        def _snapshot(self) -> dict[str, Any]:
                state: dict[str, Any] = {}
                for key, value in self.__dict__.items():
                        if key.startswith("_"):
                                continue
                        if isinstance(value, list):
                                serialised = []
                                for item in value:
                                        if isinstance(item, SimpleNamespace):
                                                serialised.append(item.__dict__.copy())
                                        else:
                                                serialised.append(copy.deepcopy(item))
                                state[key] = serialised
                        else:
                                state[key] = copy.deepcopy(value)
                return state

        def _current_value(self, field: str) -> Any:
                value = getattr(self, field, None)
                if isinstance(value, list):
                        return [item.__dict__.copy() if isinstance(item, SimpleNamespace) else copy.deepcopy(item) for item in value]
                return copy.deepcopy(value)

        # -- API -------------------------------------------------------------
        def __getattr__(self, item: str) -> Any:
                if item.startswith("_"):
                        raise AttributeError(item)
                return None

        def is_new(self) -> bool:
                        return self._is_new

        def insert(self) -> "Document":
                if not self.is_new():
                        return self.save()
                self.before_insert()
                self.before_save()
                self.validate()
                if not self.name:
                        if self.doctype == "User" and getattr(self, "email", None):
                                self.name = self.email
                        elif self.doctype == "Customer" and getattr(self, "customer_name", None):
                                self.name = self.customer_name
                        else:
                                self.name = frappe.db.generate_name(self.doctype)
                if not getattr(self, "owner", None):
                        self.owner = frappe.session.user
                self.creation = self.creation or frappe.utils.now_datetime()
                self.modified = self.creation
                frappe.db.insert(self)
                self._is_new = False
                self._original_values = self._snapshot()
                self.after_insert()
                self.on_update()
                return self

        def save(self) -> "Document":
                if self.is_new():
                        return self.insert()
                self.before_save()
                self.validate()
                self.modified = frappe.utils.now_datetime()
                frappe.db.update(self)
                self.on_update()
                self._original_values = self._snapshot()
                return self

        def submit(self) -> "Document":
                self.docstatus = 1
                self.before_submit()
                self.validate()
                self.modified = frappe.utils.now_datetime()
                frappe.db.update(self)
                self.on_submit()
                self._original_values = self._snapshot()
                return self

        def reload(self) -> "Document":
                if not self.name:
                        raise ValidationError("Cannot reload document without a name")
                data = frappe.db.get_doc_data(self.doctype, self.name)
                if not data:
                        raise ValidationError(f"Document {self.doctype} {self.name} missing")
                self._load(data)
                self._is_new = False
                self._original_values = self._snapshot()
                return self

        def append(self, field: str, value: dict[str, Any]) -> SimpleNamespace:
                items = getattr(self, field, None)
                if items is None:
                        items = []
                        setattr(self, field, items)
                item = SimpleNamespace(**value)
                items.append(item)
                return item

        def db_set(self, field: str, value: Any, commit: bool | None = None) -> None:  # noqa: ARG002 - API compat
                setattr(self, field, value)
                frappe.db.set_value(self.doctype, self.name, field, value)
                self._original_values[field] = copy.deepcopy(value)

        def has_value_changed(self, field: str) -> bool:
                return self._original_values.get(field) != self._current_value(field)

        def has_changed(self, field: str) -> bool:
                return self.has_value_changed(field)

        def add_comment(self, *_: Any, **__: Any) -> None:  # pragma: no cover - audit trail not needed
                pass

        def add_roles(self, *roles: str) -> None:
                if not self.name:
                        raise ValidationError("User document must be inserted before assigning roles")
                for role in roles:
                        frappe.add_user_role(self.name, role)

        # -- hook stubs ------------------------------------------------------
        def before_insert(self) -> None:  # pragma: no cover - default hook
                pass

        def after_insert(self) -> None:  # pragma: no cover - default hook
                pass

        def before_save(self) -> None:  # pragma: no cover - default hook
                pass

        def before_submit(self) -> None:  # pragma: no cover - default hook
                pass

        def on_submit(self) -> None:  # pragma: no cover - default hook
                pass

        def on_update(self) -> None:  # pragma: no cover - default hook
                pass

        def validate(self) -> None:  # pragma: no cover - default hook
                pass


class GenericDocument(Document):
        __register__ = False


def get_document_class(doctype: str) -> type[Document]:
        cls = _get_doctype_class(doctype)
        if cls:
                return cls  # type: ignore[return-value]
        return GenericDocument


ValidationError = frappe.ValidationError

