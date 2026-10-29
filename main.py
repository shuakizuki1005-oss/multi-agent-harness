from git_manager import run_git, prepare_branch
import argparse
from pathlib import Path

from runner import run_command
from orchestrator import run_agents


def main():
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

    repo_path = Path(args.repo).expanduser().resolve()

    if not repo_path.is_dir():
        print("エラー：指定されたフォルダが存在しません")
        return

    if not (repo_path / ".git").exists():
        print("エラー：Gitリポジトリではありません")
        return

    print("=== Multi-Agent Harness ===")
    print(f"対象リポジトリ: {repo_path}")
    print(f"実行タスク: {args.task}")
    print("準備完了！")

    # Gitの状態を確認
    result = run_command(
        ["git", "status", "--short"],
        cwd=repo_path
    )

    print("\n=== Gitの状態 ===")

    if result.returncode != 0:
        print("Gitの状態取得に失敗しました")
        print(result.stderr)
        return

    print(result.stdout or "変更なし")

    result = run_git(
        ["status", "--porcelain"],
        repo_path
    )

    if result.returncode != 0:
        print("Gitの状態確認に失敗しました")
        return
    
    if result.stdout.strip():
        print("\n未コミットの変更があるため停止しました。")
        print("AIによる編集を始める前に変更を整理してください。")
        return
    
    print("\nGitの作業ディレクトリはクリーンです。")

    answer = input(
        "\nAI専用の作業ブランチを作成しますか？ (y/n): "
    )

    if answer.lower() != "y":
        print("処置を中止しました。")
        return

    try:
        original_branch, new_branch = prepare_branch(repo_path)

    except RuntimeError as error:
        print(f"ブランチ作成エラー: {error}")
        return

    print(f"元のブランチ: {original_branch}")
    print(f"作業ブランチ: {new_branch}")
    # マルチエージェント処理を開始
    run_agents(
        task=args.task,
        repo_path=repo_path
    )


if __name__ == "__main__":
    main()
