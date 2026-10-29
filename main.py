
import argparse
from pathlib import Path

from runner import run_command
from git_manager import run_git, create_worktree
from orchestrator import run_agents


def main():
    # ① コマンドライン引数を設定
    parser = argparse.ArgumentParser(
        description="Multi-Agent Harness"
    )

    parser.add_argument(
        "--repo",
        required=True,
        help="対象のGitリポジトリのパス"
    )

    parser.add_argument(
        "--task",
        required=True,
        help="AIに実行させるタスク"
    )

    args = parser.parse_args()

    # ② リポジトリのパスを取得
    repo_path = Path(args.repo).expanduser().resolve()

    if not repo_path.is_dir():
        print("エラー：指定されたフォルダが存在しません")
        return

    # Gitリポジトリか確認
    result = run_git(
        ["rev-parse", "--show-toplevel"],
        repo_path
    )

    if result.returncode != 0:
        print("エラー：Gitリポジトリではありません")
        return

    # サブフォルダが指定された場合もルートに統一
    repo_path = Path(result.stdout.strip()).resolve()

    print("=== Multi-Agent Harness ===")
    print(f"対象リポジトリ: {repo_path}")
    print(f"実行タスク: {args.task}")

    # ③ Gitの状態を確認
    result = run_command(
        ["git", "status", "--short"],
        cwd=repo_path
    )

    if result.returncode != 0:
        print("Gitの状態取得に失敗しました")
        print(result.stderr)
        return

    print("\n=== Gitの状態 ===")
    print(result.stdout or "変更なし")

    # ④ 未コミットの変更を確認
    result = run_git(
        ["status", "--porcelain"],
        repo_path
    )

    if result.returncode != 0:
        print("Gitの安全確認に失敗しました")
        print(result.stderr)
        return

    if result.stdout.strip():
        print("\n未コミットの変更があるため停止しました。")
        print("変更をコミットまたは退避してください。")
        return

    print("\nGitの作業ディレクトリはクリーンです。")

    # ⑤ worktree作成の確認
    answer = input(
        "\nAI専用worktreeを作成しますか？ (y/n): "
    )

    if answer.strip().lower() != "y":
        print("処理を中止しました。")
        return

    # ⑥ AI専用worktreeを作成
    try:
        worktree_path, branch_name = create_worktree(repo_path)

    except RuntimeError as error:
        print(f"worktree作成エラー: {error}")
        return

    print("\n=== AI作業環境 ===")
    print(f"作業ブランチ: {branch_name}")
    print(f"AI専用フォルダ: {worktree_path}")

    # ⑦ AIを専用worktree内で実行
    run_agents(
        task=args.task,
        repo_path=worktree_path
    )

    print("\n=== Harness終了 ===")
    print(f"作業フォルダ: {worktree_path}")
    print("元の作業フォルダは変更していません。")


if __name__ == "__main__":
    main()
