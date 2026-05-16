from datetime import date

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    date_of_birth: date
    language: str = Field(default="fr", min_length=2, max_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TwoFactorRequired(BaseModel):
    requires_2fa: bool = True
    challenge_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class TotpSetupResponse(BaseModel):
    secret: str
    otpauth_url: str
    qr_code_base64: str


class TotpVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class TwoFactorLoginVerify(BaseModel):
    challenge_token: str
    code: str = Field(min_length=6, max_length=6)


class TotpDisableRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)
