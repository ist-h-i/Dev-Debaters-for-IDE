# config.template.py
# ------------------------------------------------------------
# テンプレ（コミットOK）
# 実運用はこのファイルを config.py にコピーして編集してください。
#
#   cp config.template.py config.py
#
# IMPORTANT:
# - config.py はトークンを含むためコミット禁止（.gitignoreへ）
# ------------------------------------------------------------

# GitLab base URL（例: "https://gitlab.com" / "https://gitlab.example.com"）
GITLAB_BASE_URL = "https://gitlab.com"

# Personal Access Token（scope: api 推奨）
GITLAB_TOKEN = ""

# 対象MR（複数OK）
# 形式: https://<host>/<group>/<subgroup>/<repo>/-/merge_requests/<iid>
MR_URLS = [
  # "https://gitlab.com/group/subgroup/repo/-/merge_requests/17",
]

# 出力ディレクトリ
OUT_DIR = "./out"
REVIEW_OUT_DIR = "./review_out"

# system note（自動生成メモ等）も含めるか
INCLUDE_SYSTEM_NOTES = False

# コーディングルール（JSON）ファイル
CODING_RULES_FILE = "./rules/coding_rules.json"

# MRレビュー用：コーディングガイドライン（Markdown）
GUIDELINES_MD_FILE = "./in/guidelines.md"
