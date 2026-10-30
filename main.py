
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
    finalize_implementation_log
)


MAX_REPAIRS = 3


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Harness"
    )

    parser.add_argument(
        "--repo",
        required=True,
        help="対象のGitリポジトリ"
    )

    parser.add_argument(
        "--task",
        required=True,
        help="AIに実装させるタスク"
    )

    args = parser.parse_args()

    # ① 対象リポジトリを確認
    repo_path = Path(args.repo).expanduser().resolve()

    if not repo_path.is_dir():
        print("指定されたフォルダが存在しません")
        return

    result = run_git(
        ["rev-parse", "--show-toplevel"],
        repo_path
    )

    if result.returncode != 0:
        print("Gitリポジトリではありません")
        return

    repo_path = Path(result.stdout.strip()).resolve()

    print("=== Multi-Agent Harness ===")
    print(f"対象: {repo_path}")
    print(f"タスク: {args.task}")

    # ② Gitの状態を確認
    result = run_git(
        ["status", "--porcelain"],
        repo_path
    )

    if result.returncode != 0:
        print("Gitの状態確認に失敗しました")
        return

    if result.stdout.strip():
        print("未コミットの変更があるため停止しました")
        return

    # ③ 実装前のpytest
    print("\n=== 実装前のpytest ===")

    answer = input(
        "既存テストの内容を確認しましたか？ "
        "pytestを実行しますか？ (y/n): "
    )

    if answer.strip().lower() != "y":
        print("テストを実行せず終了しました")
        return

    passed, test_output = run_project_tests(repo_path)

    print(test_output)

    if not passed:
        print("\n既存テストが失敗しているため、実装を中止しました")
        return

    print("\n既存テストはすべて成功しました")

    # ④ Claude Codeの実行確認
    answer = input(
        "\nClaudeに実装を開始させますか？ (y/n): "
    )

    if answer.strip().lower() != "y":
        print("処理を中止しました")
        return

    # ⑤ AI専用worktreeで実装
    try:
        worktree_path, branch_name, success = start_implementation(
            repo_path=repo_path,
            task=args.task
        )

    except Exception as error:
        print(f"実装エラー: {error}")
        return

    print("\n=== 実装結果 ===")
    print(f"ブランチ: {branch_name}")
    print(f"作業フォルダ: {worktree_path}")

    # ⑥ ログを初期化
    log_data = create_implementation_log(
        task=args.task,
        repo_path=repo_path,
        branch_name=branch_name
    )

    status = "FAILED"

    try:
        if not success:
            print("Claudeによる実装に失敗しました")
            log_data["error"] = "Implementation failed"
            return

        # ⑦ 実装内容の確認
        print("\n=== 実装内容の確認 ===")
        print(f"作業フォルダ: {worktree_path}")

        print(
            "\n変更されたファイルを開いて、"
            "実装内容を確認してください。"
        )

        answer = input(
            "\n変更内容を確認しましたか？ "
            "pytestとCodexレビューを実行しますか？ (y/n): "
        )

        if answer.strip().lower() != "y":
            print("テストを実行せず終了しました")
            status = "CANCELLED"
            return

        # ⑧ pytest・レビュー・修正ループ
        approved = False

        for attempt in range(MAX_REPAIRS + 1):
            print(f"\n=== 検証 {attempt + 1} 回目 ===")

            # pytestを実行
            passed, test_output = run_project_tests(
                worktree_path
            )

            print("\n=== pytest ===")
            print(test_output)

            # Codexレビュー
            review_passed, review = review_code(
                task=args.task,
                test_output=test_output,
                test_passed=passed,
                repo_path=worktree_path
            )

            print("\n=== Codexレビュー ===")
            print(review)

            # 結果をログに記録
            add_log_entry(
                log_data=log_data,
                attempt=attempt + 1,
                test_passed=passed,
                test_output=test_output,
                review_passed=review_passed,
                review=review,
                repair_attempted=False
            )

            # テストとレビューの両方が成功
            if passed and review_passed:
                approved = True
                print("\nテスト・レビューともに成功！")
                break

            # 修正回数の上限
            if attempt == MAX_REPAIRS:
                print("\n最大修正回数に達しました")
                break

            # ⑨ Claude Codeによる修正
            print(
                f"\n=== Claude: 修正 "
                f"{attempt + 1}/{MAX_REPAIRS} ==="
            )

            log_data["history"][-1]["repair_attempted"] = True

            success = repair_code(
                task=args.task,
                test_output=test_output,
                review=review,
                repo_path=worktree_path
            )

            log_data["history"][-1]["repair_succeeded"] = bool(success)

            if not success:
                print("Claudeによる修正に失敗しました")
                log_data["error"] = "Repair failed"
                break

            # ⑩ 修正内容を確認してから再テスト
            print("\n=== 修正内容の確認 ===")
            print(f"作業フォルダ: {worktree_path}")
            print("Claudeが修正したファイルを確認してください。")

            answer = input(
                "\n修正内容を確認しましたか？ "
                "再テストしますか？ (y/n): "
            )

            if answer.strip().lower() != "y":
                print("再テストを中止しました")
                status = "CANCELLED"
                break

        # ⑪ 最終判定
        print("\n=== 最終結果 ===")

        if approved:
            status = "SUCCESS"
            print("SUCCESS: pytest・Codexレビュー承認")

        elif status == "CANCELLED":
            print("CANCELLED: ユーザーが処理を中止しました")

        else:
            status = "FAILED"
            print("FAILED: テストまたはレビューが未承認")

    except Exception as error:
        log_data["error"] = str(error)
        print(f"\n予期しないエラー: {error}")

    finally:
        # ⑫ 成功・失敗・キャンセル時にもログ保存
        finalize_implementation_log(
            log_data=log_data,
            status=status
        )

        print("\n=== Harness終了 ===")
        print(f"作業フォルダ: {worktree_path}")
        print(f"最終ステータス: {status}")


if __name__ == "__main__":
    main()
