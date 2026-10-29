import subprocess
from datetime import datetime

def run_git(args, repo_path):
    return subprocess.run(
        ["git", *args],
        cwd=repo_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        shell=False
    )

def prepare_branch(repo_path):
    #Gitの変更状態を確認
    result = run_git(["status", "--porcelain"], repo_path)

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    #未コミットの変更がある場合は停止
    if result.stdout.strip():
        raise RuntimeError(
            "未コミットの変更があります。"
            "コミットまたは退避してから実行してください。"
        )

    #現在のブランチを確認
    result = run_git(
        ["branch", "--show-current"],
        repo_path
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    original_branch = result.stdout.strip()

    #作業ブランチを作成
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    branch_name = f"agent/task-{timestamp}"

    result = run_git(
        ["switch", "-c", branch_name],
        repo_path
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return original_branch, branch_name

from pathlib import Path
from uuid import uuid4

def create_worktree(repo_path):
    repo_path = Path(repo_path).resolve()

    #未コミットの変更がないか確認
    status = run_git(["status", "--porcelain"], repo_path)

    if status.returncode != 0:
        raise RuntimeError(status.stderr)
    
    if status.stdout.strip():
        raise RuntimeError("未コミットの変更があります")

    #作業ごとに固有の名前を生成
    run_id = uuid4().hex[:8]
    branch_name = f"agent/task-{run_id}"

    #元のフォルダの外側に作業フォルダを作る
    worktree_path = (
        repo_path.parent / f"{repo_path.name}-agent-{run_id}"
    )

    result = run_git(
        [
            "worktree",
            "add",
            "-b",
            branch_name,
            str(worktree_path)
        ],
        repo_path
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return worktree_path, branch_name