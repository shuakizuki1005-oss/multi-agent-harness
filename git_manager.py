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