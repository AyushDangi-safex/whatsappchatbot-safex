import os
import uvicorn
from src.main import app    # <-- point this at the file where your FastAPI app lives

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",                 # <module path>:<app instance>
        host="0.0.0.0",                 # bind to all interfaces
        port=int(os.environ.get("PORT", 8000)),  # read PORT env var (default 8000 locally)
        log_level="info"
    )
