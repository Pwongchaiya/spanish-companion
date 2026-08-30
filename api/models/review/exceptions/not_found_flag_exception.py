"""Backward-compatible re-export shim.

NotFoundFlagException moved to api.models.flag.exceptions as part of the
6-layer rebuild's Flag Foundation service (Wave 4) -- it's Flag's own leaf
now, not Review's. This shim keeps api.services.review.review_service_exceptions
and api.controllers.review importing successfully in the interim: per the
rebuild's migration mechanics, a Foundation build must ADD new code without
breaking a consumer that a later wave hasn't rewired yet. Wave 5 rewires
ReviewOrchestrator onto FlagService directly and deletes this shim along with
its __init__.py re-export.
"""

from api.models.flag.exceptions.not_found_flag_exception import NotFoundFlagException

__all__ = ["NotFoundFlagException"]
