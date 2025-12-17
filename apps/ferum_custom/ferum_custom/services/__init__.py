"""Business services package.

Contains orchestration logic (usecases) and business policies independent from
DocType controllers to keep controllers thin and testable.
"""

from .projects import get_project_manager_email

__all__ = ["get_project_manager_email"]
