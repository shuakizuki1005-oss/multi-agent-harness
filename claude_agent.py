import subprocess
import shutil


def ask_claude(prompt, cwd):
    claude_path = shutil.which("claude.cmd")

    if claude_path is None:
        claude_path = shutil.which("claude")

    if claude_path is None:
        print("エラー：Claude Codeが見つかりません")
        return None

    try:
        result = subprocess.run(
            [
                claude_path,
                "--print",
                "--disallowedTools",
                "Bash,Read,Write,Edit,Glob,Grep"
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
        print("Claude Codeがタイムアウトしました")
        return None

    except OSError as error:
        print(f"Claude Codeの起動に失敗しました: {error}")
        return None

    print("Claude終了コード:", result.returncode)

    if result.returncode != 0:
        print("Claude Codeでエラーが発生しました")
        print(result.stderr)
        return None

    return result.stdout.strip()