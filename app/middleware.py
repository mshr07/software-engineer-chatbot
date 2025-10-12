from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from typing import Dict
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse of the API"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.clients: Dict[str, deque] = defaultdict(deque)
        self.chat_clients: Dict[str, deque] = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        current_time = time.time()
        
        # Different rate limits for different endpoints
        if "/api/chat/message" in str(request.url):
            # More restrictive rate limiting for chat messages
            return await self._apply_rate_limit(
                request, call_next, client_ip, current_time, 
                self.chat_clients, requests_per_minute=20
            )
        elif "/api/interview/generate" in str(request.url):
            # Rate limiting for interview question generation
            return await self._apply_rate_limit(
                request, call_next, client_ip, current_time, 
                self.clients, requests_per_minute=10
            )
        else:
            # Standard rate limiting for other endpoints
            return await self._apply_rate_limit(
                request, call_next, client_ip, current_time, 
                self.clients, requests_per_minute=self.requests_per_minute
            )
    
    async def _apply_rate_limit(
        self, 
        request: Request, 
        call_next, 
        client_ip: str, 
        current_time: float,
        client_dict: Dict[str, deque], 
        requests_per_minute: int
    ):
        # Clean old requests (older than 1 minute)
        client_requests = client_dict[client_ip]
        while client_requests and current_time - client_requests[0] > 60:
            client_requests.popleft()
        
        # Check if rate limit exceeded
        if len(client_requests) >= requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60
                }
            )
        
        # Add current request
        client_requests.append(current_time)
        
        # Process the request
        response = await call_next(request)
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'"
        )
        
        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log requests for monitoring and debugging"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f"Request: {request.method} {request.url} from {request.client.host}"
        )
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Response: {response.status_code} in {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url} "
                f"in {process_time:.3f}s - {str(e)}"
            )
            raise