"""Interface for the learner-profile Processing service.

typing.Protocol, not abc.ABC -- same convention as the Foundation interface
(i_learner_profile_service.py) and this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers), extended to service
interfaces project-wide.
"""

from typing import Protocol

from api.models.foundations.learner_profile.learner_profile import LearnerProfile


class ILearnerProfileProcessingService(Protocol):
    """External-facing contract for LearnerProfile's Processing service."""

    def ensure_profile(self, default_level: str) -> LearnerProfile:
        """Get the singleton profile row, creating it if it doesn't exist yet.

        Calls Foundation's get_learner_profile(); on
        LearnerProfileValidationException (Foundation's not-found signal),
        calls create_learner_profile(default_level) instead. Any other
        exception from Foundation propagates unchanged.
        """
        ...
