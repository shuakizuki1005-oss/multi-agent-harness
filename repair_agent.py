
def create_repair_prompt(task, test_output, review):
    prompt = f"""
以下の実装に問題があります。

元のタスク:
{task}

テスト結果:
{test_output}

Codexのレビュー:
{review}

修正方針:
1. テスト失敗の原因を特定する
2. 必要最小限のコードを修正する
3. 元のタスクの仕様を維持する
4. 関係のないファイルは変更しない
5. Git commitやpushは行わない

修正内容と理由を説明してください。
"""
    return prompt

from implementation_agent import implement_with_claude

def repair_code(task, test_output, review, repo_path):
    prompt = create_repair_prompt(
        task=task,
        test_output=test_output,
        review=review
    )

    return implement_with_claude(
        task=prompt,
        cwd=repo_path
    )