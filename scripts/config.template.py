# config.template.py
# ------------------------------------------------------------
# このファイルはテンプレートです（コミットしてOK）
# 実運用では、このファイルを config.py にコピーして値を埋めてください。
#
#   cp config.template.py config.py
#
# IMPORTANT:
# - config.py は Personal Access Token を含むためコミット禁止
# - .gitignore に config.py を追加してください
# ------------------------------------------------------------

# GitLab base URL（self-managed なら自社の URL に変更）
GITLAB_BASE_URL = "https://gitlab.com"

# GitLab Personal Access Token（PAT）
# 例: "glpat-xxxxxxxxxxxxxxxx"
GITLAB_TOKEN = ""

# 出力ディレクトリ
DEFAULT_OUT_DIR = "./out"

# 対象行の前後何行を diff から復元して含めるか（best-effort）
DEFAULT_CONTEXT_RADIUS = 3

# system note（自動生成メモ等）を含めるか
INCLUDE_SYSTEM_NOTES = False
