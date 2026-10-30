import argparse
from pathlib import Path

from git_manager import run_git
from implementation_pipeline import start_implementation

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

    #① 対象リポジトリを確認
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

    #② Gitの状態を確認
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
    
    #③ ユーザーに確認
    answer = input(
        "\nClaudeに実装を開始させますか？ (y/n): "
    )

    if answer.strip().lower() != "y":
        print("中止しました")
        return

    #④ AI専用worktreeで実装
    try:
        worktree_path , branch_name, success = start_implementation(
            repo_path=repo_path,
            task=args.task
        )
    
    except Exception as error:
        print(f"実装エラー: {error}")
        return
    
    print("\n=== 実装結果 ===")
    print(f"ブランチ: {branch_name}")
    print(f"作業フォルダ: {worktree_path}")

    if success:
        print("Claudeによる実装処理が終了しました")
        print("変更内容を確認してください")
    else:
        print("Claudeによる実装に失敗しました")
    
if __name__ == "__main__":
    main()