# ERP Agent app module
import dotenv
import logfire

# Load environment variables from .env at startup so they are available to logfire
dotenv.load_dotenv()

# Initialize logfire structured logging and telemetry.
# If authenticated (via CLI or `LOGFIRE_TOKEN` env var), it will stream traces to the cloud platform.
# Otherwise, it gracefully falls back to local-only console logging.
try:
    logfire.configure(
        advanced=logfire.AdvancedOptions(base_url="https://logfire-us.pydantic.dev")
    )
except Exception:
    logfire.configure(send_to_logfire=False)

