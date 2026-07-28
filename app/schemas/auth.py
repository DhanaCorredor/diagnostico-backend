"""Authentication schemas."""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Body of POST /auth/login."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """Login response: the JWT token."""

    access_token: str
    token_type: str = "bearer"
