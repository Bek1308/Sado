import os

# `sado.main` builds an app on import; keep it off the developer's real database and
# off the paid Model API, whatever the local .env says.
os.environ["SADO_MEMORY_DB_PATH"] = ":memory:"
os.environ["SADO_GUEST_DB_PATH"] = ":memory:"
os.environ["SADO_WARM_UP_VOICES"] = "false"
os.environ["SADO_META_API_KEY"] = ""
os.environ["SADO_BASETEN_API_KEY"] = ""
os.environ["SADO_DESKTOP_CONTROL"] = "false"
os.environ["SADO_FIREBASE_PROJECT_ID"] = ""
os.environ["SADO_OWNER_EMAILS"] = ""
