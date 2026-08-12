import time
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from typing import Dict, List

# Global in-memory dictionary tracking client_ip -> list of timestamps
_requests_history: Dict[str, List[float]] = defaultdict(list)

def reset_rate_limits():
    """Resets all in-memory rate-limiter history (used for unit testing)."""
    _requests_history.clear()

class LoginRateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Middleware enforcing rate limiting on sensitive authentication endpoints
    to prevent brute-force password guessing attacks.
    """
    def __init__(self, app, max_requests: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        # Enforce rate limit specifically on POST /api/auth/login
        if request.url.path == "/api/auth/login" and request.method == "POST":
            client_ip = request.client.host if request.client else "127.0.0.1"
            now = time.time()

            # Clean timestamps older than window_seconds
            timestamps = [t for t in _requests_history[client_ip] if now - t < self.window_seconds]
            _requests_history[client_ip] = timestamps

            if len(timestamps) >= self.max_requests:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": f"Too many authentication attempts. Rate limit exceeded ({self.max_requests} attempts per minute). Please try again later."}
                )

            _requests_history[client_ip].append(now)

        response = await call_next(request)
        return response
