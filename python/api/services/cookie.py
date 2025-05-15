from random import random
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


# Set a sessionID cookie which will be used by nginx reverse proxy load balancer for sticky sessions
class SessionIDCookieMiddleware(BaseHTTPMiddleware):
  def __init__(self, app):
    super().__init__(app)

  async def dispatch(self, request: Request, call_next):
    response = await call_next(request)
  
    if "sessionID" not in request.cookies:
      session_id = str(int(random() * 10e12))
      response.set_cookie(key="sessionID", value=session_id, max_age=900, httponly=True)

    return response