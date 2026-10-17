"""Central configuration for the Brew Delice Café chatbot project."""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.environ.get("BREW_DB_PATH", os.path.join(BASE_DIR, "database", "chatbot.db"))
STATIC_DIR = os.path.join(BASE_DIR, "static")

HOST = os.environ.get("BREW_HOST", "127.0.0.1")
PORT = int(os.environ.get("BREW_PORT", "5000"))
DEBUG = os.environ.get("BREW_DEBUG", "0") == "1"

# Optional: protect /dashboard and enquiry APIs with HTTP Basic auth.
# Windows (cmd):  set BREW_ADMIN_PASSWORD=mysecret
# Leave empty for an open dashboard (fine for a local demo).
ADMIN_USER = os.environ.get("BREW_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("BREW_ADMIN_PASSWORD", "")

# NLP: minimum cosine similarity before a message is treated as understood.
NLP_THRESHOLD = 0.34
MAX_MESSAGE_LEN = 500
SESSION_TTL_SECONDS = 2 * 60 * 60
PROTOTYPE_NOTICE = ("Prototype / test data - generated while testing the chatbot. "
                    "These are NOT real customer or sales results.")
