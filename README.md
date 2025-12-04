# Dev Debaters for IDE

VSCode のカスタムインストラクションで動かせるディベート型エージェントワークフローのテンプレート。

## 内容
- `docs/workflow.md`: デフォルトで AI に伝えるワークフロー指示。
- `prompts/`: ヒアリング/オーケストレーション/設計/コーディング/ドキュメントの各ジャッジプロンプト。
- `scripts/generate_improvement_prompt.py`: 各フェーズの履歴から改善要求プロンプトを生成するスクリプト。

## 使い方
1. `docs/workflow.md` を VSCode のカスタムインストラクションに貼り付ける。
2. 必要に応じて `prompts/` 以下のプロンプトを各ロールに読み込ませる。
3. 議論ログを `histories/` ディレクトリに保存し、スクリプトで改善要求を生成する。
