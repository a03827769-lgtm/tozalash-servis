from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
import re
import logging

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """
        Task 35: SQLi/XSS Guard Middleware.
        Basic WAF to block obvious malicious payloads in URLs/Headers.
        """
        path = request.url.path
        query = request.url.query

        # Simple regex for common SQLi / XSS patterns
        dangerous_patterns = [
            r"(?i)(<script>|%3Cscript%3E)",
            r"(?i)(union\s+select|drop\s+table)",
            r"(?i)(javascript:)",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, path) or re.search(pattern, query):
                logger.warning(f"Blocked malicious request from {request.client.host}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Forbidden: Security policy violation."},
                )

        response = await call_next(request)
        return response


class PIIRedactionFilter(logging.Filter):
    """
    Task 32: PII Redaction.
    Masks sensitive data (phones, emails, credit cards) in application logs.
    """

    def __init__(self):
        super().__init__()
        self.pii_patterns = [
            # Phone number (uzb style)
            (r"\+998\d{9}", "+998********"),
            # Basic email regex
            (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "***@***.***"),
            # Credit Card (16 digits)
            (r"\b(?:\d[ -]*?){13,16}\b", "****-****-****-****"),
        ]

    def filter(self, record):
        message = record.getMessage()
        for pattern, mask in self.pii_patterns:
            message = re.sub(pattern, mask, message)
        # Update the log record message (this is a bit hacky for standard logging,
        # but works as a demonstration filter. Using loguru we'd use a patcher).
        record.msg = message
        record.args = ()
        return True
