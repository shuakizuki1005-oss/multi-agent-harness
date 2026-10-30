
import argparse
import subprocess
from pathlib import Path


def run_git(args, repo_path):
    return subprocess.run(
        ["git", *args],
        cwd=repo_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def list_worktrees(repo_path):
    result = run_git(
        ["worktree", "list", "--porcelain"],
        repo_path,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    worktrees = []

    for block in result.stdout.strip().split("\n\n"):
        if not block.strip():
            continue

        info = {}

        for line in block.splitlines():
            if line.startswith("worktree "):
                info["path"] = line[len("worktree "):]

            elif line.startswith("branch "):
                info["branch"] = line[len("branch "):]

            elif line == "bare":
                info["bare"] = True

            elif line == "locked" or line.startswith("locked "):
                info["locked"] = True

            elif line == "prunable" or line.startswith("prunable "):
                info["prunable"] = True

        if "path" in info:
            worktrees.append(info)

    return worktrees


def inspect_worktree(worktree, main_path):
    path = Path(worktree["path"]).resolve()
    branch = worktree.get("branch", "(detached HEAD)")

    # 元のリポジトリを保護
    if path == main_path:
        return "元のリポジトリ（保護）"

    # ロック中のworktreeを保護
    if worktree.get("locked"):
        return "ロック中（保護）"

    # Git管理情報が残っているworktree
    if worktree.get("prunable"):
        return "要確認（作業フォルダが見つからない可能性）"

    if not path.is_dir():
        return "要確認（フォルダが存在しない）"

    if worktree.get("bare"):
        return "要確認（bareリポジトリ）"

    # 未コミットの変更と未追跡ファイルを確認
    result = run_git(
        ["status", "--porcelain", "--untracked-files=all"],
        path,
    )

    if result.returncode != 0:
        return "要確認（Git状態の取得失敗）"

    if result.stdout.strip():
        return "変更あり（保護）"

    # AI作業ブランチ以外は対象外
    if not branch.startswith("refs/heads/agent/task-"):
        return "対象外（AI作業ブランチではない）"

    # 元のリポジトリのHEADを取得
    base_result = run_git(
        ["rev-parse", "HEAD"],
        main_path,
    )

    if base_result.returncode != 0:
        return "要確認（元ブランチの取得失敗）"

    base_commit = base_result.stdout.strip()

    # AIブランチだけに存在するコミットを確認
    log_result = run_git(
        ["log", "--oneline", f"{base_commit}..HEAD"],
        path,
    )

    if log_result.returncode != 0:
        return "要確認（コミット比較失敗）"

    if log_result.stdout.strip():
        return "未統合コミットあり（保護）"

    return "整理候補（変更なし・未統合コミットなし）"


def main():
    parser = argparse.ArgumentParser(
        description="Git worktreeの安全な状態確認"
    )

    parser.add_argument(
        "--repo",
        required=True,
        help="対象Gitリポジトリ",
    )

    args = parser.parse_args()

    repo_path = Path(args.repo).expanduser().resolve()

    if not repo_path.is_dir():
        print("指定されたフォルダが存在しません")
        return

    # Gitリポジトリか確認
    root_result = run_git(
        ["rev-parse", "--show-toplevel"],
        repo_path,
    )

    if root_result.returncode != 0:
        print("Gitリポジトリではありません")
        return

    main_path = Path(root_result.stdout.strip()).resolve()

    print("=== Worktree 状態一覧 ===")

    try:
        worktrees = list_worktrees(main_path)

    except RuntimeError as error:
        print(f"取得エラー: {error}")
        return

    for index, worktree in enumerate(worktrees, start=1):
        status = inspect_worktree(
            worktree,
            main_path,
        )

        print(f"\n[{index}] {worktree['path']}")
        print(
            f"ブランチ: "
            f"{worktree.get('branch', '(不明)')}"
        )
        print(f"状態: {status}")

    print("\n=== 確認完了 ===")
    print("このプログラムはworktreeを削除しません。")


if __name__ == "__main__":
    main()
