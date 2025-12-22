You will receive:
1) Existing coding rules JSON (authoritative baseline).
2) MR comments JSON (new findings).

Task:
- Extract reusable rules from comments.
- Merge into the rules JSON using deduplication.
- Increase importance for duplicates.
- Output the updated coding rules JSON only.

Notes:
- Ignore purely conversational comments with no reusable rule.
- When a comment is about a specific file, generalize to a reusable rule.
