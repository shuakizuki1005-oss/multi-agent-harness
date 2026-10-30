
from unittest.mock import patch

from main import run_repair_loop


def test_repair_loop_success():
    log_data = {"history": []}

    with (
        patch("main.run_verification") as mock_verify,
        patch("main.add_log_entry") as mock_log,
        patch("main.repair_code") as mock_repair,
    ):
        mock_verify.return_value = (
            True,
            "7 passed",
            True,
            "VERDICT: PASS",
        )

        result = run_repair_loop(
            task="テスト用タスク",
            worktree_path="dummy_path",
            log_data=log_data,
        )

        assert result == "SUCCESS"
        mock_verify.assert_called_once()
        mock_log.assert_called_once()
        mock_repair.assert_not_called()


def test_repair_loop_failure():
    log_data = {"history": []}

    with (
        patch("main.run_verification") as mock_verify,
        patch("main.add_log_entry") as mock_log,
        patch("main.repair_code") as mock_repair,
        patch("main.confirm", return_value=True),
    ):
        mock_verify.return_value = (
            False,
            "1 failed",
            False,
            "VERDICT: REVISE",
        )

        def add_history(**kwargs):
            log_data["history"].append(
                {"repair_attempted": False}
            )

        mock_log.side_effect = add_history
        mock_repair.return_value = True

        result = run_repair_loop(
            task="テスト用タスク",
            worktree_path="dummy_path",
            log_data=log_data,
        )

        assert result == "FAILED"
        assert mock_verify.call_count == 4
        assert mock_repair.call_count == 3

def test_repair_loop_success_after_repair():
    log_data = {"history": []}

    with (
        patch("main.run_verification") as mock_verify,
        patch("main.add_log_entry") as mock_log,
        patch("main.repair_code") as mock_repair,
        patch("main.confirm", return_value=True),
    ):
        mock_verify.side_effect = [
            (False, "1 failed", False, "VERDICT: REVISE"),
            (True, "8 passed", True, "VERDICT: PASS"),
        ]

        def add_history(**kwargs):
            log_data["history"].append(
                {"repair_attempted": False}
            )

        mock_log.side_effect = add_history
        mock_repair.return_value = True

        result = run_repair_loop(
            task="テスト用タスク",
            worktree_path="dummy_path",
            log_data=log_data,
        )

        assert result == "SUCCESS"
        assert mock_verify.call_count == 2
        mock_repair.assert_called_once()
        assert log_data["history"][0]["repair_attempted"] is True