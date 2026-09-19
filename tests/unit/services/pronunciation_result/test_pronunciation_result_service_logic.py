"""Happy-path flow: each public method delegates to exactly one broker call
and returns its result unchanged. Strict call-count verification."""


class TestCreatePronunciationResult:

    def test_should_insert_and_return_broker_row(self, service, mock_pronunciation_result_broker, make_result):
        # given
        submitted = make_result()
        stored = make_result(id=7)
        mock_pronunciation_result_broker.insert_pronunciation_result.return_value = stored

        # when
        actual = service.create_pronunciation_result(submitted)

        # then
        assert actual is stored
        mock_pronunciation_result_broker.insert_pronunciation_result.assert_called_once_with(submitted)
        assert mock_pronunciation_result_broker.select_all_pronunciation_results.call_count == 0

    def test_should_accept_prosody_score_and_boundary_scores(
        self, service, mock_pronunciation_result_broker, make_result
    ):
        # given -- 0 and 100 are inclusive bounds; 0 must not be rejected as falsy
        submitted = make_result(accuracy_score=0, fluency_score=100, prosody_score=0.0, words_json=[])
        mock_pronunciation_result_broker.insert_pronunciation_result.return_value = submitted

        # when
        service.create_pronunciation_result(submitted)

        # then
        mock_pronunciation_result_broker.insert_pronunciation_result.assert_called_once_with(submitted)
        assert mock_pronunciation_result_broker.select_all_pronunciation_results.call_count == 0


class TestListPronunciationResults:

    def test_should_return_broker_rows_unchanged(self, service, mock_pronunciation_result_broker, make_result):
        # given
        rows = [make_result(id=1), make_result(id=2)]
        mock_pronunciation_result_broker.select_all_pronunciation_results.return_value = rows

        # when
        actual = service.list_pronunciation_results()

        # then
        assert actual == rows
        mock_pronunciation_result_broker.select_all_pronunciation_results.assert_called_once_with()
        assert mock_pronunciation_result_broker.insert_pronunciation_result.call_count == 0

    def test_should_return_empty_list_when_nothing_stored(self, service, mock_pronunciation_result_broker):
        mock_pronunciation_result_broker.select_all_pronunciation_results.return_value = []

        assert service.list_pronunciation_results() == []
        mock_pronunciation_result_broker.select_all_pronunciation_results.assert_called_once_with()
        assert mock_pronunciation_result_broker.insert_pronunciation_result.call_count == 0
