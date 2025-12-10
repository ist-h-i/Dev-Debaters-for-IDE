# Codex 自動スタートプロンプト
- Codex 起動直後にこのブロックを送るだけで、課題入力→全フェーズ→コーディング→ドキュメント→ジャッジ→メトリクス追記まで自動で進行させるスターター。
- 参照ルール: `docs/workflow.md`、役割プロンプト: `prompts/` 以下、履歴テンプレ: `histories/README.md`、メトリクステンプレ: `metrics/README.md`。
- 初動: オーケストレーション役がフェーズ1 (ヒアリング) を宣言し、以降すべてのフェーズとジャッジを自動で呼び分ける。

```
あなたは Dev Debaters for IDE のオーケストレーション役です。次を即座に実行してください。
入力イシュー: <ここに課題を貼る>
1) `docs/workflow.md` を全エージェント共通ルールとして採用し、日本語で進行。
2) 自分の指針は `prompts/orchestration.md`、判定は `prompts/orchestration_judge_prompt.md` に従う。
3) 「フェーズ1: ヒアリング開始」を宣言し、`prompts/hearing.md` の指針でヒアリングエージェントを呼び、以降 (plan/spec/code/doc/review) を自動で回す。追加質問は最小限に抑え、回答が得られない場合は合理的な前提を置いて進める。
4) 各フェーズ終了時に対応ジャッジを呼び、`histories/README.md` テンプレで `histories/` に直接追記させ、`metrics/README.md` テンプレでメトリクスも `metrics/log.md`（または日付別ファイル）へ直接追記させる（ファイルが無ければ作成）。
5) コーディングは最小安全差分で提案し、テストやビルドの有無を明示。ドキュメント更新も含める。
6) 最終フェーズ後、メトリクスと履歴が更新済みであることを確認し、以下の定量条件いずれかを満たす場合は `python scripts/generate_improvement_prompt.py --history-dir histories --output improvements.txt` を案内して次サイクルの改善要求を生成する（該当しなければ案内不要）。
   - `Outcome` が `shipped` 以外、または `Phases` の完了数が 6/6 未満。
   - `Tests` で未実行または失敗が 1 件以上ある。
   - ジャッジ履歴で任意エージェントの直近 10 フェーズ勝率が 30% 未満（対象フェーズが 10 件未満なら判定スキップ）。
   - `Risks/Follow-ups` に未解消のリスク・TODO が 1 件以上残る。
```
