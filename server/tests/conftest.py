import os

# `sado.main` builds an app on import; keep its stores off the developer's real database.
os.environ["SADO_MEMORY_DB_PATH"] = ":memory:"
os.environ["SADO_WARM_UP_VOICES"] = "false"
