from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    display_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: object) -> str:
        return str(value).strip().lower()

    @field_validator("display_name", mode="before")
    @classmethod
    def normalize_display_name(cls, value: object) -> str:
        return " ".join(str(value).split())


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    display_name: str | None = Field(default=None, min_length=2, max_length=120)
    current_password: str | None = Field(default=None, min_length=1, max_length=128)
    new_password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_optional_username(cls, value: object) -> str | None:
        if value is None:
            return None
        return str(value).strip().lower()

    @field_validator("display_name", mode="before")
    @classmethod
    def normalize_optional_display_name(cls, value: object) -> str | None:
        if value is None:
            return None
        return " ".join(str(value).split())


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    display_name: str

    model_config = {"from_attributes": True}
