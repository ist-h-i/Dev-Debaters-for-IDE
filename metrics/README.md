# Metrics ログ運用
- 1 サイクルにつき 1 エントリを追記（追記のみ）。
- ファイルは `metrics/log.md` にまとめて追記するか、必要なら `metrics/YYYYMMDD_<issue>.md` で分割してもよい。
- ジャッジはフェーズ完了時に最新エントリをファイルへ直接追記する（なければ作成）。

```
## Issue: <短いタイトルまたはリンク>
- Date: YYYY-MM-DD
- Phases: hearing / orchestration / spec / plan / code / doc / review (完了したものだけ残す)
- Outcome: shipped / blocked / retry
- Tests: <実行したテストと結果の箇条書き>
- Artifacts: <変更ファイルや主要成果物の一覧>
- Risks/Follow-ups: <残リスクや次サイクルで見る点>
```
