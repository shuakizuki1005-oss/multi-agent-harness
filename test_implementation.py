
from pathlib import Path
import subprocess
import sys

from git_manager import create_worktree, get_changes
from implementation_agent import implement_with_claude
from repair_agent import repair_code
from review_agent import review_code
from implementation_logger import (
    create_implementation_log,
    add_log_entry,
    finalize_implementation_log
)


TASK = (
    "hello.pyを作成し、"
    "Hello from AI! と表示するPythonコードを書いてください。"
)

MAX_REPAIRS = 3


def run_hello_test(worktree_path):
    hello_file = worktree_path / "hello.py"

    if not hello_file.is_file():
        return False, "hello.pyが存在しません"

    try:
        result = subprocess.run(
            [sys.executable, "-I", str(hello_file)],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            shell=False
        )
    except subprocess.TimeoutExpired:
        return False, "テストがタイムアウトしました"
    except OSError as error:
        return False, f"テスト起動エラー: {error}"

    output = result.stdout.strip()

    if result.returncode == 0 and output == "Hello from AI!":
        return True, output

    return False, (
        f"終了コード: {result.returncode}\n"
        f"標準出力: {output}\n"
        f"エラー: {result.stderr}"
    )


def main():
    repo_path = Path.home() / "harness-test"

    if not repo_path.is_dir():
        print("テスト用リポジトリがありません")
        return

    print("=== Multi-Agent Implementation Test ===")
    print(f"対象リポジトリ: {repo_path}")
    print(f"タスク: {TASK}")

    answer = input(
        "\nClaudeとCodexの連携テストを実行しますか？ (y/n): "
    )

    if answer.strip().lower() != "y":
        print("処理を中止しました")
        return

    try:
        worktree_path, branch_name = create_worktree(repo_path)
    except RuntimeError as error:
        print(f"worktree作成失敗: {error}")
        return

    print("\n=== AI作業環境 ===")
    print(f"作業ブランチ: {branch_name}")
    print(f"作業フォルダ: {worktree_path}")

    log_data = create_implementation_log(
        task=TASK,
        repo_path=repo_path,
        branch_name=branch_name
    )

    status = "FAILED"

    try:
        # ① Claudeによる実装
        print("\n=== Claude: 実装 ===")

        success = implement_with_claude(
            task=TASK,
            cwd=worktree_path
        )

        if not success:
            print("Claudeによる実装に失敗しました")
            log_data["error"] = "Implementation failed"
            return

        # ② Git変更確認
        print("\n=== Git変更確認 ===")
        print(get_changes(worktree_path) or "変更なし")

        # ③ テスト・レビュー・修正ループ
        approved = False

        for attempt in range(MAX_REPAIRS + 1):
            print(f"\n=== 検証 {attempt + 1} 回目 ===")

            passed, test_output = run_hello_test(worktree_path)

            print("\nテスト結果:")
            print(test_output)

            review_passed, review = review_code(
                task=TASK,
                test_output=test_output,
                test_passed=passed,
                repo_path=worktree_path
            )

            print("\nCodexレビュー:")
            print(review)

            both_passed = passed and review_passed

            add_log_entry(
                log_data=log_data,
                attempt=attempt + 1,
                test_passed=passed,
                test_output=test_output,
                review_passed=review_passed,
                review=review,
                repair_attempted=False
            )

            if both_passed:
                approved = True
                print("\nテスト・レビューともに成功！")
                break

            if attempt == MAX_REPAIRS:
                print("\n最大修正回数に達しました")
                break

            # ④ Claudeによる修正
            print(
                f"\n=== Claude: 修正 "
                f"{attempt + 1}/{MAX_REPAIRS} ==="
            )

            # 修正を開始する直前に記録
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

        # ⑤ 最終判定
        if approved:
            status = "SUCCESS"
            print("\nSUCCESS: テスト・レビュー承認")
        else:
            print("\nFAILED: 未承認")

        # ⑥ 最終変更確認
        print("\n=== 最終Git変更確認 ===")
        print(get_changes(worktree_path) or "変更なし")

    except Exception as error:
        log_data["error"] = str(error)
        print(f"\n予期しないエラー: {error}")

    finally:
        # 成功・失敗・return時にも実行される
        finalize_implementation_log(
            log_data=log_data,
            status=status
        )

        print("\n=== Harness終了 ===")
        print(f"作業フォルダ: {worktree_path}")


if __name__ == "__main__":
    main()
