import subprocess
import sys
from pathlib import Path

def run_project_tests(repo_path):
    repo_path = Path(repo_path).resolve()

    if not repo_path.is_dir():
        return False, "プロジェクトが存在しません"
    
    tests_dir = repo_path / "tests"

    if not tests_dir.is_dir():
        return False, "testsフォルダが存在しません"

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-m",
                "pytest",
                str(tests_dir)
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            shell=False
        )

    except subprocess.TimeoutExpired:
        return False, "テストがタイムアウトしました"

    except OSError as error:
        return False, f"テスト実行エラー: {error}"

    output = (
        result.stdout
        + "\n"
        + result.stderr
    ).strip()

    return result.returncode == 0, output