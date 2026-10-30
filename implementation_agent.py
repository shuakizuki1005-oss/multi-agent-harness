import shutil
import subprocess

def implement_with_claude(task, cwd):
    claude_path = shutil.which("claude.cmd")

    if claude_path is None:
        print("Claude Codeが見つかりません")
        return False

    prompt = f"""
    次のタスクを実装してください

    {task}

    制約:
    - 作業ディレクトリ内だけを編集する
    - 外部サービスにアクセスしない
    - ファイル削除は禁止
    - Git commitやpushは禁止
    - 実装完了後に変更内容を説明する
    """

    try:
        result = subprocess.run(
            [
                claude_path,
                "--print",
                "--permission-mode",
                "acceptEdits"
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
        print("実装処理がタイムアウトしました")
        return False
    
    except OSError as error:
        print(f"Claude Codeの起動エラー: {error}")
        return False

    print("Claude終了コード:", result.returncode)

    if result.returncode != 0:
        print(result.stderr)
        return False
    
    print(result.stdout)
    return True