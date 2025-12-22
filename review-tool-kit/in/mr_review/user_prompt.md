You will receive:
- MR JSON (diffs + comments + metadata)
- Coding guidelines (Markdown)
- Historical MR findings stock (JSON)

You must:
- Enforce the coding guidelines.
- Use the historical stock to detect recurring issues.
- If an issue matches historical stock, include a reference in 【詳細】 like: （Ref: <rule id>）

Output JSON schema:
{
  "mr_overall": {
    "status": "マージ可能 | 指摘あり | リファクタあり",
    "changes_summary": "string",
    "risk_impact": "string"
  },
  "inline_comments": [
    {
      "severity": "不具合 | リファクタ | 解説 | Good",
      "path": "string",
      "side": "new | old",
      "line": 123,
      "detail": "【詳細】... ",
      "fix_example": "【修正例】... ",
      "impact": "【影響範囲】... "
    }
  ]
}
