
from pathlib import Path

from git_manager import create_worktree, get_changes
from implementation_agent import implement_with_claude
from repair_agent import repair_code
from review_agent import review_code
from test_runner import run_project_tests
from implementation_logger import (
    create_implementation_log,
    add_log_entry,
    finalize_implementation_log
)


TASK = (
    "calculator.pyにsubtract(a, b)関数を追加してください。"
    "既存のadd(a, b)関数は変更しないでください。"
    "subtract(a, b)はaからbを引いた値を返してください。"
)

MAX_REPAIRS = 3


def main():
    # ① テスト用リポジトリ
    repo_path = Path.home() / "harness-test"

    if not repo_path.is_dir():
        print("テスト用リポジトリがありません")
        return

    print("=== Multi-Agent Implementation Test ===")
    print(f"対象リポジトリ: {repo_path}")
    print(f"タスク: {TASK}")

    # ② 実行確認
    answer = input(
        "\nClaudeとCodexの連携テストを実行しますか？ (y/n): "
    )

    if answer.strip().lower() != "y":
        print("処理を中止しました")
        return

    # ③ AI専用worktreeを作成
    try:
        worktree_path, branch_name = create_worktree(repo_path)
    except RuntimeError as error:
        print(f"worktree作成失敗: {error}")
        return

    print("\n=== AI作業環境 ===")
    print(f"作業ブランチ: {branch_name}")
    print(f"作業フォルダ: {worktree_path}")

    # ④ ログの初期化
    log_data = create_implementation_log(
        task=TASK,
        repo_path=repo_path,
        branch_name=branch_name
    )

    status = "FAILED"

    try:
        # ⑤ Claude Codeによる実装
        print("\n=== Claude: 実装 ===")

        success = implement_with_claude(
            task=TASK,
            cwd=worktree_path
        )

        if not success:
            print("Claudeによる実装に失敗しました")
            log_data["error"] = "Implementation failed"
            return

        # ⑥ Git変更確認
        print("\n=== Git変更確認 ===")
        print(get_changes(worktree_path) or "変更なし")

        # ⑦ pytest・レビュー・修正ループ
        approved = False

        for attempt in range(MAX_REPAIRS + 1):
            print(f"\n=== 検証 {attempt + 1} 回目 ===")

            # pytestを実行
            passed, test_output = run_project_tests(worktree_path)

            print("\n=== pytest結果 ===")
            print(test_output)

            # Codexによるレビュー
            review_passed, review = review_code(
                task=TASK,
                test_output=test_output,
                test_passed=passed,
                repo_path=worktree_path
            )

            print("\n=== Codexレビュー ===")
            print(review)

            both_passed = passed and review_passed

            # 結果をJSONログに記録
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
            if both_passed:
                approved = True
                print("\nテスト・レビューともに成功！")
                break

            # 修正回数の上限
            if attempt == MAX_REPAIRS:
                print("\n最大修正回数に達しました")
                break

            # Claude Codeによる修正
            print(
                f"\n=== Claude: 修正 "
                f"{attempt + 1}/{MAX_REPAIRS} ==="
            )

            log_data["history"][-1]["repair_attempted"] = True

            success = repair_code(
                task=TASK,
                test_output=test_output,
                review=review,
                repo_path=worktree_path
            )

            log_data["history"][-1]["repair_succeeded"] = bool(success)

            if not success:
                print("Claudeによる修正に失敗しました")
                log_data["error"] = "Repair failed"
                break

        # ⑧ 最終判定
        print("\n=== 最終判定 ===")

        if approved:
            status = "SUCCESS"
            print("SUCCESS: pytest・Codexレビュー承認")
        else:
            print("FAILED: 未承認")

        # ⑨ 最終Git変更確認
        print("\n=== 最終Git変更確認 ===")
        print(get_changes(worktree_path) or "変更なし")

    except Exception as error:
        log_data["error"] = str(error)
        print(f"\n予期しないエラー: {error}")

    finally:
        # ⑩ エラー時にもログ保存
        finalize_implementation_log(
            log_data=log_data,
            status=status
        )

        print("\n=== Harness終了 ===")
        print(f"作業フォルダ: {worktree_path}")


if __name__ == "__main__":
    main()
