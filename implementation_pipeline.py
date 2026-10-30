
from git_manager import create_worktree, get_changes
from implementation_agent import implement_with_claude


def start_implementation(repo_path, task):
    # AI専用worktreeを作成
    worktree_path, branch_name = create_worktree(repo_path)

    print("\n=== AI作業環境 ===")
    print(f"ブランチ: {branch_name}")
    print(f"作業フォルダ: {worktree_path}")

    # Claude Codeが実装
    print("\n=== Claude: 実装 ===")

    success = implement_with_claude(
        task=task,
        cwd=worktree_path
    )

    if not success:
        print("Claudeによる実装に失敗しました")
        return worktree_path, branch_name, False

    # 変更ファイルを確認
    print("\n=== 変更ファイル ===")
    print(get_changes(worktree_path) or "変更なし")

    return worktree_path, branch_name, True
