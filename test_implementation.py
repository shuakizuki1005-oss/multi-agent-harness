
from pathlib import Path
import subprocess
import sys

from git_manager import create_worktree, get_changes
from implementation_agent import implement_with_claude
from codex_agent import ask_codex
from repair_agent import repair_code


# AIに依頼するタスク
TASK = (
    "hello.pyを作成し、"
    "Hello from AI! と表示するPythonコードを書いてください。"
)

# 最大修正回数
MAX_REPAIRS = 3


def run_hello_test(worktree_path):
    """hello.pyの動作を確認する"""

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

    # ④ Claude Codeによる実装
    print("\n=== Claude: 実装 ===")

    success = implement_with_claude(
        task=TASK,
        cwd=worktree_path
    )

    if not success:
        print("Claudeによる実装に失敗しました")
        return

    # ⑤ Gitの変更を確認
    print("\n=== Git変更確認 ===")

    try:
        changes = get_changes(worktree_path)

    except RuntimeError as error:
        print(f"Git変更確認エラー: {error}")
        return

    print(changes or "変更なし")

    # ⑥ Codexによるレビュー
    print("\n=== Codex: コードレビュー ===")

    review = ask_codex(
        prompt="""
        このリポジトリの変更内容をレビューしてください。

        確認項目:
        - コードが正しく動くか
        - バグがないか
        - セキュリティ上の問題がないか
        - 改善点があるか

        ファイルは変更しないでください。
        """,
        cwd=worktree_path
    )

    if not review:
        print("Codexレビューに失敗しました")
        return

    print(review)

    # ⑦ テストと自動修正
    print("\n=== Python: テストと自動修正 ===")

    for attempt in range(MAX_REPAIRS + 1):
        passed, test_output = run_hello_test(worktree_path)

        print(f"\nテスト実行 {attempt + 1} 回目")
        print(test_output)

        # テスト成功なら終了
        if passed:
            print("\nテスト成功！")
            break

        # 最大修正回数に達したら停止
        if attempt == MAX_REPAIRS:
            print("\n最大修正回数に達しました")
            print("テストは成功していません")
            break

        # Claudeに修正を依頼
        print(
            f"\n=== Claude: 修正 "
            f"{attempt + 1}/{MAX_REPAIRS} ==="
        )

        success = repair_code(
            task=TASK,
            test_output=test_output,
            review=review,
            repo_path=worktree_path
        )

        if not success:
            print("Claudeによる修正に失敗しました")
            break

    # ⑧ 最終的なGit変更確認
    print("\n=== 最終Git変更確認 ===")

    try:
        changes = get_changes(worktree_path)
        print(changes or "変更なし")

    except RuntimeError as error:
        print(f"Git変更確認エラー: {error}")

    print("\n=== Harness終了 ===")
    print(f"作業フォルダ: {worktree_path}")
    print("元のリポジトリの作業ファイルは変更していません")


if __name__ == "__main__":
    main()
