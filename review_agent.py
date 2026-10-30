
from codex_agent import ask_codex


def review_code(task, test_output, test_passed, repo_path):
    prompt = f"""
以下の実装をレビューしてください。

元のタスク:
{task}

テスト成功:
{test_passed}

テスト出力:
{test_output}

このリポジトリの変更ファイルを確認し、
次の項目を評価してください。

1. 要件を満たしているか
2. バグがないか
3. セキュリティ上の問題がないか
4. 修正が必要か

注意:
- ファイルは変更しない
- テスト成功だけを理由に承認しない
- 変更が確認できなければ承認しない
- 最後の行を必ず以下のどちらかにする

VERDICT: PASS
VERDICT: REVISE
"""

    review = ask_codex(
        prompt=prompt,
        cwd=repo_path
    )

    if not review:
        return False, "レビュー結果を取得できませんでした"

    lines = review.strip().splitlines()
    verdict = lines[-1].strip() if lines else ""

    if verdict == "VERDICT: PASS":
        return True, review

    # 不明な判定も承認しない
    return False, review
