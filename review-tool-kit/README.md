# AI GitLab Review Toolkit

GitLab の Merge Request（MR）を対象に、以下の2機能を提供します。

- 機能1：コーディングルール生成（MRコメントを学習素材にしてルールJSONを更新）
- 機能2：MRレビュー（MR差分＋コメントをAIに渡し、AIレビュー結果をGitLabへ投稿）

## 前提
- Python 3.10+ 推奨
- `pip install requests`
- GitLab Personal Access Token（scope: `api`）を用意

## セットアップ（テンプレ運用）
1. `config.template.py` を `config.py` にコピーして編集
   ```bash
   cp config.template.py config.py
   ```
2. `config.py` で以下を設定
   - `GITLAB_BASE_URL`
   - `GITLAB_TOKEN`
   - `MR_URLS`（複数可）
3. 依存導入
   ```bash
   pip install requests
   ```

## 出力ディレクトリ
- `./out/`：GitLabから取得したMR情報・コメント
  - `./out/comments/`：コメント取得結果（機能1入力）
  - `./out/mr/`：MR差分＋コメント（機能2入力）
- `./review_out/`：AIレビュー結果JSON（手動または別処理で生成）
- `./in/compiled/`：AI入力用に組み立てたプロンプト

---

# 機能1：コーディングルール生成

## 1-1. MRコメント取り込み
```bash
python scripts/gitlab_fetch_mr_comments.py
```
- `config.py` の `MR_URLS` を対象に、MRコメントを収集して `./out/comments/*.comments.json` を作成します。
- 単発で実行したい場合：
  ```bash
  python scripts/gitlab_fetch_mr_comments.py --mr-url "https://.../-/merge_requests/17"
  ```

## 1-2. ルール更新用プロンプト生成（AI入力）
既存ルールJSON（`rules/coding_rules.json`）と、取り込んだコメントJSONをマージするためのプロンプトを生成します。
- 重複ルールは importance(int) を +1 します（AI側に強制）。
```bash
python scripts/build_rules_update_prompt_pack.py --comments-json "./out/comments/<file>.comments.json"
```
生成物：
- `./in/compiled/<file>.rules_update.prompt.md`

## 1-3. AIの出力（想定）
AIには上記 `.prompt.md` を入力し、**更新後の `coding_rules.json` をJSONのみで出力**させます。
その出力で `rules/coding_rules.json` を置き換える運用を推奨します。

---

# 機能2：MRレビュー

## 2-1. MR全体取り込み（差分＋コメント）
```bash
python scripts/gitlab_export_mr.py
```
生成物：
- `./out/mr/<MR>__iid_<iid>.mr.json`

## 2-2. MRレビュー用プロンプト生成（AI入力）
以下の追加コンテキストをAIに渡せます：
- `./in/guidelines.md`（コーディングガイドライン）
- `./in/mr_findings_stock.json`（過去指摘ストック）

```bash
python scripts/build_mr_review_prompt_pack.py --mr-json "./out/mr/<MR>__iid_<iid>.mr.json"
```
生成物：
- `./in/compiled/<MR>__iid_<iid>.mr_review.prompt.md`

## 2-3. AIの出力（必須フォーマット：JSON）
AIは以下スキーマのJSON（review json）を出力します：
- `mr_overall`：MR全体コメント用
- `inline_comments`：コード変更箇所への指摘（path/line/side）
この出力は `./review_out/*.review.json` に保存してください。

## 2-4. AIレビュー結果をGitLabに送信
- MR全体：ノート（notes）として投稿
- インライン：position付き discussion として投稿

```bash
python scripts/gitlab_post_ai_review.py       --mr-url "https://.../-/merge_requests/17"       --review-json "./review_out/<file>.review.json"
```

dry-run（投稿せずに内容確認）：
```bash
python scripts/gitlab_post_ai_review.py --mr-url "..." --review-json "..." --dry-run
```

---

# GitLab CI について（設計ガイド）
- CI上では `GITLAB_TOKEN` を `CI/CD Variables` に置くのが安全です（masked/protected）。
- 本ツールはテンプレ運用（config.py）ですが、CIでは `config.py` をジョブ内で動的生成することを推奨します。
- AI呼び出し（LLM）自体は本キットには含めていません（社内LLM/Bedrock/OpenAI等に合わせて接続してください）。

---

# 補足：AIへのコメント形式（投稿本文）
インラインコメント：
```
【By AI reviewer】
【重要度（不具合 | リファクタ | 解説 | Good）】
【詳細】...
【修正例】...
【影響範囲】...
```

MR全体コメント：
```
【By AI reviewer】
【ステータス（マージ可能 | 指摘あり | リファクタあり）】
【変更内容】...
【影響範囲・リスク】...
```
