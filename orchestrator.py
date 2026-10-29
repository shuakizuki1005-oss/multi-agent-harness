
import json

from claude_agent import ask_claude
from codex_agent import ask_codex
from logger import save_log


MAX_REVIEWS = 3


def run_agents(task, repo_path):
    print("\n=== Claude: 初期計画 ===")

    plan = ask_claude(
        f"""
        以下の開発タスクの実装計画を作成してください。

        タスク: {task}

        不明な仕様は合理的な仮定を置き、明記してください。
        追加質問はせず、計画を完成させてください。
        ファイルは変更しないでください。
        """,
        cwd=repo_path
    )

    if not plan:
        print("初期計画の作成に失敗しました")
        return

    initial_plan = plan
    history = []
    status = "max_reviews_reached"

    for attempt in range(1, MAX_REVIEWS + 1):
        print(f"\n=== Codex: レビュー {attempt}/{MAX_REVIEWS} ===")

        review_prompt = f"""
        次の実装計画をレビューしてください。

        元のタスク:
        {task}

        実装計画:
        {plan}

        実現可能性・設計・テスト・セキュリティを確認してください。
        ファイルは変更しないでください。

        最後の行に、次のいずれかを厳密に記載してください。
        VERDICT: PASS
        VERDICT: REVISE
        """

        review = ask_codex(review_prompt, cwd=repo_path)

        if not review:
            status = "review_failed"
            break

        print(review)

        # 最終行だけを確認する
        lines = review.strip().splitlines()
        verdict_line = lines[-1].strip() if lines else ""

        history.append({
            "attempt": attempt,
            "plan": plan,
            "review": review,
            "verdict": verdict_line
        })

        if verdict_line == "VERDICT: PASS":
            status = "approved"
            print("\nレビュー合格！")
            break

        if verdict_line != "VERDICT: REVISE":
            status = "invalid_verdict"
            print("レビュー判定を読み取れませんでした")
            break

        if attempt == MAX_REVIEWS:
            print("\n最大レビュー回数に到達しました")
            break

        print("\n=== Claude: 計画改善 ===")

        improved_plan = ask_claude(
            f"""
            以下のレビューを反映して実装計画を改善してください。

            元のタスク:
            {task}

            現在の計画:
            {plan}

            Codexのレビュー:
            {review}

            修正済みの計画全体を出力してください。
            ファイルは変更しないでください。
            """,
            cwd=repo_path
        )

        if not improved_plan:
            status = "improvement_failed"
            break

        plan = improved_plan

    print("\n=== 最終計画 ===")
    print(plan)

    log_path = save_log(
        task=task,
        repo_path=repo_path,
        plan=initial_plan,
        history=history,
        status=status
    )

    print(f"\nログ保存先: {log_path}")
    print(f"終了ステータス: {status}")
