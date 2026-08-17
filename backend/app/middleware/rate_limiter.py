import time
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from typing import Dict, List

_requests_history: Dict[str, List[float]] = defaultdict(list)

def reset_rate_limits():
    _requests_history.clear()

class LoginRateLimitingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/api/auth/login" and request.method == "POST":
            x_forwarded_for = request.headers.get("x-forwarded-for")
            if x_forwarded_for:
                client_ip = x_forwarded_for.split(",")[0].strip()
            else:
                client_ip = request.client.host if request.client else "127.0.0.1"

            now = time.time()
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
