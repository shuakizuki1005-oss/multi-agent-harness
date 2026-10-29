
import subprocess
import shutil


def ask_codex(prompt, cwd):
    codex_path = shutil.which("codex.cmd")

    if codex_path is None:
        print("エラー：Codex CLIが見つかりません")
        return None

    try:
        result = subprocess.run(
            [
                codex_path,
                "exec",
                "--sandbox",
                "read-only",
                "-"
            ],
            input=prompt,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            shell=False
        )

    except subprocess.TimeoutExpired:
        print("Codexがタイムアウトしました")
        return None

    print("Codex終了コード:", result.returncode)

    if result.returncode != 0:
        print("Codexでエラーが発生しました")
        print(result.stderr)
        return None

    return result.stdout.strip()
