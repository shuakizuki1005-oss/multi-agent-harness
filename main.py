
import argparse
from pathlib import Path

from git_manager import run_git
from implementation_pipeline import start_implementation
from test_runner import run_project_tests
from review_agent import review_code
from repair_agent import repair_code
from implementation_logger import (
    create_implementation_log,
    add_log_entry,
    finalize_implementation_log,
)

MAX_REPAIRS = 3


def confirm(message):
    return input(message).strip().lower() == "y"


def validate_repository(repo_path):
    if not repo_path.is_dir():
        print("指定されたフォルダが存在しません")
        return None

    result = run_git(
        ["rev-parse", "--show-toplevel"],
        repo_path,
    )

    if result.returncode != 0:
        print("Gitリポジトリではありません")
        return None

    repo_path = Path(result.stdout.strip()).resolve()

    result = run_git(
        ["status", "--porcelain"],
        repo_path,
    )

    if result.returncode != 0:
        print("Gitの状態確認に失敗しました")
        return None

    if result.stdout.strip():
        print("未コミットの変更があるため停止しました")
        return None

    return repo_path


def run_verification(task, worktree_path):
    print("\n=== pytest ===")

    passed, test_output = run_project_tests(worktree_path)
    print(test_output)

    print("\n=== Codexレビュー ===")

    review_passed, review = review_code(
        task=task,
        test_output=test_output,
        test_passed=passed,
        repo_path=worktree_path,
    )

    print(review)

    return passed, test_output, review_passed, review


def run_repair_loop(task, worktree_path, log_data):
    for attempt in range(MAX_REPAIRS + 1):
        print(f"\n=== 検証 {attempt + 1} 回目 ===")

        passed, test_output, review_passed, review = (
            run_verification(task, worktree_path)
        )

        add_log_entry(
            log_data=log_data,
            attempt=attempt + 1,
            test_passed=passed,
            test_output=test_output,
            review_passed=review_passed,
            review=review,
            repair_attempted=False,
        )

        if passed and review_passed:
            print("\nテスト・レビューともに成功しました")
            return "SUCCESS"

        if attempt == MAX_REPAIRS:
            print("\n最大修正回数に達しました")
            return "FAILED"

        print(
            f"\n=== Claude: 修正 "
            f"{attempt + 1}/{MAX_REPAIRS} ==="
        )

        log_data["history"][-1]["repair_attempted"] = True

        success = repair_code(
            task=task,
            test_output=test_output,
            review=review,
            repo_path=worktree_path,
        )

        log_data["history"][-1]["repair_succeeded"] = bool(success)

        if not success:
            log_data["error"] = "Repair failed"
            print("Claudeによる修正に失敗しました")
            return "FAILED"

        print("\n=== 修正内容の確認 ===")
        print(f"作業フォルダ: {worktree_path}")

        if not confirm(
            "修正内容を確認しましたか？ "
            "再テストしますか？ (y/n): "
        ):
            print("再テストを中止しました")
            return "CANCELLED"

    return "FAILED"


def dry_run():
    print("=== Dry Run ===")
    print("AI・Git・pytestは実行しません")

    max_repairs = MAX_REPAIRS
    repair_count = 0

    for attempt in range(max_repairs + 1):
        print(f"\n検証 {attempt + 1} 回目")

        if attempt == 0:
            passed = False
            review_passed = False
        else:
            passed = True
            review_passed = True

        print(f"pytest: {passed}")
        print(f"Codexレビュー: {review_passed}")

        if passed and review_passed:
            print("\nSUCCESS: 修正ループの制御を確認")
            return

        if repair_count >= max_repairs:
            print("\nFAILED: 修正回数の上限")
            return

        repair_count += 1
        print(f"Claude修正（模擬）: {repair_count} 回目")


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Harness"
    )

    parser.add_argument(
        "--repo",
        help="対象のGitリポジトリ",
    )

    parser.add_argument(
        "--task",
        help="AIに実装させるタスク",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="AIを使わず修正ループを模擬実行",
    )

    args = parser.parse_args()

    if args.dry_run:
        dry_run()
        return

    if not args.repo or not args.task:
        parser.error(
            "通常実行には --repo と --task が必要です"
        )

    repo_path = Path(args.repo).expanduser().resolve()

    repo_path = validate_repository(repo_path)

    if repo_path is None:
        return

    print("=== Multi-Agent Harness ===")
    print(f"対象: {repo_path}")
    print(f"タスク: {args.task}")

    print("\n=== 実装前のpytest ===")

    if not confirm(
        "既存テストの内容を確認しましたか？ "
        "pytestを実行しますか？ (y/n): "
    ):
        print("処理を中止しました")
        return

    passed, test_output = run_project_tests(repo_path)
    print(test_output)

    if not passed:
        print("既存テストが失敗しているため停止しました")
        return

    print("\n既存テストはすべて成功しました")

    if not confirm(
        "\nClaudeに実装を開始させますか？ (y/n): "
    ):
        print("処理を中止しました")
        return

    try:
        worktree_path, branch_name, success = (
            start_implementation(
                repo_path=repo_path,
                task=args.task,
            )
        )
    except Exception as error:
        print(f"実装エラー: {error}")
        return

    print("\n=== 実装結果 ===")
    print(f"ブランチ: {branch_name}")
    print(f"作業フォルダ: {worktree_path}")

    log_data = create_implementation_log(
        task=args.task,
        repo_path=repo_path,
        branch_name=branch_name,
    )

    status = "FAILED"

    try:
        if not success:
            log_data["error"] = "Implementation failed"
            print("Claudeによる実装に失敗しました")
        else:
            print("\n=== 実装内容の確認 ===")
            print(f"作業フォルダ: {worktree_path}")

            if not confirm(
                "変更内容を確認しましたか？ "
                "pytestとCodexレビューを実行しますか？ (y/n): "
            ):
                status = "CANCELLED"
            else:
                status = run_repair_loop(
                    task=args.task,
                    worktree_path=worktree_path,
                    log_data=log_data,
                )

    except Exception as error:
        log_data["error"] = str(error)
        print(f"\n予期しないエラー: {error}")

    finally:
        finalize_implementation_log(
            log_data=log_data,
            status=status,
        )

        print("\n=== Harness終了 ===")
        print(f"作業フォルダ: {worktree_path}")
        print(f"最終ステータス: {status}")


if __name__ == "__main__":
    main()
