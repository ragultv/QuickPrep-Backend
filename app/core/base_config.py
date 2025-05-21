import json
from datetime import datetime, timezone

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

# Custom JSON encoder to handle datetime with explicit UTC 'Z'
class UTCJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            # Format as ISO 8601 with 'Z' for UTC
            # Ensure the datetime object is timezone-aware (UTC)
            if obj.tzinfo is None:
                obj = obj.replace(tzinfo=timezone.utc)
            elif obj.tzinfo != timezone.utc:
                obj = obj.astimezone(timezone.utc)
            return obj.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        return super().default(obj)

# Middleware to replace the default JSON response class
class CustomJsonResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if isinstance(response, JSONResponse):
            # Re-encode the content using our custom encoder
            content = jsonable_encoder(response.body, custom_encoder={datetime: lambda dt: dt.isoformat(timespec='milliseconds').replace('+00:00', 'Z') if dt else None})
            # Note: This simple approach might need refinement depending on how complex response.body is.
            # A more robust way involves replacing FastAPI's default response class or json encoder globally.
            # For now, we'll try this simple re-encoding.
            # This middleware approach is basic and might not cover all response types perfectly.
            # A better approach involves configuring FastAPI's default JSON encoder.
            pass # Placeholder - Middleware needs refinement or global config change

        return response

# Global Pydantic config (alternative to middleware)
# This is generally the preferred way
class BaseConfig(BaseModel):
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z') if dt else None
        }

# --- How to apply the global config ---
# 1. Make your Pydantic response models inherit from a base model with this config.
#    Example in schemas/quiz_session.py:
#    from ..core.config import BaseConfig # Assuming you put BaseConfig in core/config.py
#    class QuizSessionResponse(BaseConfig):
#        id: UUID
#        ...
#
# 2. Or, configure FastAPI's default JSON encoder (more advanced, in main.py):
#    from fastapi.responses import ORJSONResponse
#    app = FastAPI(default_response_class=ORJSONResponse) # Example using ORJSON
#    (Requires installing orjson and potentially custom encoder setup)

# --- Applying Fix by modifying Pydantic Base Models --- 
# (Simpler approach for now: Modify schemas to use BaseConfig)
# We will edit the schema files to inherit from BaseConfig. 