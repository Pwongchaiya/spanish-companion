"""Unit tests for ReviewOrchestrationService.list_flags() -- broker-failure path.

H7 of the architecture conformance audit: this method bypassed _try_catch, so
a FlagService failure escaped the orchestrator unwrapped and reached Flask
raw. FlagDependencyException is not caught by name in the validation or
dependency tier (see review_service_exceptions.py's cited omissions), so it
lands in the service-tier safety net -- which is what the route now maps.
"""

import pytest

from api.models.foundations.flag.exceptions import FlagDependencyException, FlagUnavailableError
from api.models.orchestrations.review.exceptions import ReviewOrchestrationServiceException


class TestReviewOrchestratorListFlagsExceptions:

    def test_should_raise_service_exception_when_flag_service_fails(
        self, service, mock_flag_service, mock_logging_broker
    ):
        # given
        leaf = FlagUnavailableError("disk read failed")
        mock_flag_service.list_flags.side_effect = FlagDependencyException(inner_exception=leaf)

        # when
        with pytest.raises(ReviewOrchestrationServiceException):
            service.list_flags()

        # then
        mock_flag_service.list_flags.assert_called_once_with()
        mock_logging_broker.log_error.assert_called_once()
