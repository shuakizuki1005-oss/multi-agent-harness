
# Multi-Agent Harness

Claude CodeとCodex CLIを連携させ、コードの実装・テスト・レビュー・修正を支援するPythonのマルチエージェント・ハーネスです。

## 主な機能

- Claude Codeによるコード実装・修正
- Codex CLIによるコードレビュー
- pytestによる自動テスト
- Git worktreeによる作業環境の分離
- 最大3回の修正ループ
- JSON形式の実行ログ
- worktreeの状態確認

## 技術スタック

- Python
- Git
- Claude Code CLI
- Codex CLI
- pytest

## セットアップ

Python、Git、Claude Code CLI、Codex CLIが必要です。

仮想環境を作成します。

    python -m venv .venv

Windows PowerShellで仮想環境を有効化します。

    .\.venv\Scripts\Activate.ps1

pytestをインストールします。

    python -m pip install pytest

## 使い方

### 通常実行

    python main.py --repo "C:\path\to\repository" --task "新しい関数を追加する"

### 模擬実行

    python main.py --dry-run

### worktreeの状態確認

    python worktree_cleanup.py --repo "C:path\to\repository"

## 処理の流れ

1. Gitリポジトリの状態確認
2. 既存テストの実行
3. Git worktreeの作成
4. Claude Codeによる実装
5. ユーザーによる変更内容の確認
6. pytestによるテスト
7. Codex CLIによるレビュー
8. 必要に応じてClaude Codeが修正
9. JSONログの保存

## 注意事項

- 主にpytestを利用するPythonプロジェクト向けです。
- AIが変更したコードは実行前に確認してください。
- Git worktreeはセキュリティ上のサンドボックスではありません。
- 自動マージ・自動pushには対応していません。
- dry-runは模擬実行であり、実際の修正ループの統合テストではありません。

## 今後の改善

- 修正ループの統合テスト
- 安全な実行環境の構築
- 対応するテストフレームワークの追加
- webダッシュボード