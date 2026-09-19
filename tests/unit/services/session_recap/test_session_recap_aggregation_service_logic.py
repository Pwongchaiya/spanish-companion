"""Unit tests for SessionRecapAggregationService's composition logic
(roadmap C2) -- pairing ProgressOrchestrationService's latest-completed-
session read with ReviewOrchestrationService's current flag list.
"""

from datetime import timedelta

from tests.unit.services.session_recap.conftest import FIXED_NOW


class TestGetLatestRecap:

    def test_should_return_none_when_no_session_has_ever_completed(
        self, service, mock_progress_service, mock_review_service
    ):
        mock_progress_service.get_latest_completed_session.return_value = None

        actual = service.get_latest_recap()

        assert actual is None
        # No point asking Review for flags when there's no session to pair them with.
        mock_review_service.list_flags.assert_not_called()

    def test_should_pair_the_latest_session_with_its_flag_categories(
        self, service, mock_progress_service, mock_review_service, make_session_log_entry, make_flag
    ):
        mock_progress_service.get_latest_completed_session.return_value = make_session_log_entry(
            entry_id=7, minutes=15, flag_count=2
        )
        mock_review_service.list_flags.return_value = [
            make_flag("ser-vs-estar", "f1"),
            make_flag("gender-agreement", "f2"),
        ]

        actual = service.get_latest_recap()

        assert actual.flag_count == 2
        assert actual.categories_flagged == ["gender-agreement", "ser-vs-estar"]
        assert actual.session_started_at == FIXED_NOW
        assert actual.session_ended_at == FIXED_NOW + timedelta(minutes=15)

    def test_should_dedupe_and_sort_repeated_categories(
        self, service, mock_progress_service, mock_review_service, make_session_log_entry, make_flag
    ):
        mock_progress_service.get_latest_completed_session.return_value = make_session_log_entry(flag_count=3)
        mock_review_service.list_flags.return_value = [
            make_flag("ser-vs-estar", "f1"),
            make_flag("ser-vs-estar", "f2"),
            make_flag("subjunctive", "f3"),
        ]

        actual = service.get_latest_recap()

        assert actual.categories_flagged == ["ser-vs-estar", "subjunctive"]

    def test_should_report_flag_count_from_session_log_not_from_the_flag_list_length(
        self, service, mock_progress_service, mock_review_service, make_session_log_entry, make_flag
    ):
        # session_log.flag_count is the count Voice Conversation itself wrote
        # at session-end -- the source of truth per CLAUDE.md, not a
        # recompute off whatever list_flags() happens to return.
        mock_progress_service.get_latest_completed_session.return_value = make_session_log_entry(flag_count=5)
        mock_review_service.list_flags.return_value = [make_flag("ser-vs-estar", "f1")]

        actual = service.get_latest_recap()

        assert actual.flag_count == 5

    def test_should_return_empty_categories_when_the_session_had_no_flags(
        self, service, mock_progress_service, mock_review_service, make_session_log_entry
    ):
        mock_progress_service.get_latest_completed_session.return_value = make_session_log_entry(flag_count=0)
        mock_review_service.list_flags.return_value = []

        actual = service.get_latest_recap()

        assert actual.categories_flagged == []


class TestGetLatestRecapSpeech:

    def test_should_return_none_and_skip_tts_when_no_session_has_completed(
        self, service, mock_progress_service, mock_review_service, mock_tts_service
    ):
        mock_progress_service.get_latest_completed_session.return_value = None

        assert service.get_latest_recap_speech() is None

        mock_progress_service.get_latest_completed_session.assert_called_once_with()
        mock_review_service.list_flags.assert_not_called()
        mock_tts_service.synthesize_speech.assert_not_called()

    def test_should_synthesize_spanish_script_with_count_and_categories(
        self, service, mock_progress_service, mock_review_service, mock_tts_service, make_session_log_entry, make_flag
    ):
        mock_progress_service.get_latest_completed_session.return_value = make_session_log_entry(flag_count=2)
        mock_review_service.list_flags.return_value = [make_flag("ser-vs-estar", "f1"), make_flag("subjunctive", "f2")]
        mock_tts_service.synthesize_speech.return_value = b"RIFFwav"

        actual = service.get_latest_recap_speech()

        assert actual == b"RIFFwav"
        mock_tts_service.synthesize_speech.assert_called_once_with(
            "En tu última sesión marqué 2 errores. Categorías: ser vs estar, subjunctive."
        )
        mock_progress_service.get_latest_completed_session.assert_called_once_with()
        mock_review_service.list_flags.assert_called_once_with()

    def test_should_use_singular_for_one_flag(
        self, service, mock_progress_service, mock_review_service, mock_tts_service, make_session_log_entry, make_flag
    ):
        mock_progress_service.get_latest_completed_session.return_value = make_session_log_entry(flag_count=1)
        mock_review_service.list_flags.return_value = [make_flag("subjunctive")]

        service.get_latest_recap_speech()

        mock_tts_service.synthesize_speech.assert_called_once_with(
            "En tu última sesión marqué 1 error. Categorías: subjunctive."
        )

    def test_should_congratulate_when_no_flags(
        self, service, mock_progress_service, mock_review_service, mock_tts_service, make_session_log_entry
    ):
        mock_progress_service.get_latest_completed_session.return_value = make_session_log_entry(flag_count=0)
        mock_review_service.list_flags.return_value = []

        service.get_latest_recap_speech()

        mock_tts_service.synthesize_speech.assert_called_once_with(
            "En tu última sesión no marqué ningún error. ¡Buen trabajo!"
        )
