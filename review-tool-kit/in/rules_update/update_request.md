Return ONE JSON object, same schema as the existing coding rules JSON.
Keep existing fields, update:
- updated_at (ISO8601)
- rules list (merged)

Inputs follow.

--- Existing coding rules JSON ---
```json
{{CODING_RULES_JSON}}
```

--- New MR comments JSON ---
```json
{{MR_COMMENTS_JSON}}
```
