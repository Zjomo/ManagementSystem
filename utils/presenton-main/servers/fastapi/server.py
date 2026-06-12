import uvicorn
import argparse
import os
from api.main import app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the FastAPI server")
    parser.add_argument(
        "--port", type=int, required=True, help="Port number to run the server on"
    )
    parser.add_argument(
        "--reload", type=str, default="false", help="Reload the server on code changes"
    )
    args = parser.parse_args()
    reload = args.reload == "true"
    host = "127.0.0.1"

    # Always bind absolute asset generation to the active runtime port.
    os.environ["FASTAPI_PUBLIC_URL"] = f"http://{host}:{args.port}"

    # Default USER_CONFIG_PATH when not explicitly set.
    if not os.environ.get("USER_CONFIG_PATH"):
        if os.environ.get("APP_DATA_DIRECTORY"):
            os.environ["USER_CONFIG_PATH"] = os.path.join(
                os.environ["APP_DATA_DIRECTORY"], "userConfig.json"
            )
        else:
            # Fallback: relative to this script's location.
            _script_dir = os.path.dirname(os.path.abspath(__file__))
            _default_app_data = os.path.abspath(
                os.path.join(_script_dir, "..", "..", "app_data")
            )
            os.environ["USER_CONFIG_PATH"] = os.path.join(
                _default_app_data, "userConfig.json"
            )
            os.environ.setdefault("APP_DATA_DIRECTORY", _default_app_data)
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=args.port,
        log_level="info",
        reload=reload,
    )