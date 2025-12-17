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

# GitLab base URL（MR URL のホストと一致している必要があります）
# 例: "https://gitlab.com" または "https://gitlab.example.com"
GITLAB_BASE_URL = "https://gitlab.com"

# GitLab Personal Access Token（PAT）
GITLAB_TOKEN = ""

# 出力ディレクトリ
DEFAULT_OUT_DIR = "./out"

# 対象行（diffから復元）前後の行数
DEFAULT_CONTEXT_RADIUS = 3

# system note（自動生成メモ等）を含めるか
INCLUDE_SYSTEM_NOTES = False

# 一括エクスポートしたい MR URL を複数登録
# 形式: https://<host>/<group>/<subgroup>/<repo>/-/merge_requests/<iid>
MR_URLS = [
  "https://gitlab.com/group/subgroup/repo/-/merge_requests/17",
  # "https://gitlab.com/group/subgroup/repo/-/merge_requests/18",
]
