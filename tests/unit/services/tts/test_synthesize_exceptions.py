"""Unit tests for TtsService.synthesize_speech() -- broker-failure and
catch-all cases.

Pattern mirrors NL.Core.Entitlements.Api.Tests.Unit/Foundations/Entitlements/
EntitlementServiceTests.Validations.RetrieveById.cs:59-101, via the
FlagService/TopicCoveredService precedent already used in this project.
"""

from api.models.foundations.tts.exceptions import TtsDependencyException, TtsUnavailableError


class TestTtsServiceSynthesizeExceptions:

    def test_should_wrap_broker_failure_in_dependency_exception(self, service, mock_broker, mock_logging_broker):
        # given
        mock_broker.synthesize.side_effect = RuntimeError("Azure Speech unreachable")

        # when
        try:
            service.synthesize_speech("perro")
            raise AssertionError("expected TtsDependencyException")
        except TtsDependencyException as e:
            # then
            assert isinstance(e.inner_exception, TtsUnavailableError)

        mock_broker.synthesize.assert_called_once_with("perro", 1.0)
        mock_logging_broker.log_error.assert_called_once()
        logged_exception = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged_exception) is TtsDependencyException
