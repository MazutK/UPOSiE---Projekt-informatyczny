from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
)


@dataclass(frozen=True)
class Settings:
    cors_origins: tuple[str, ...] = field(default=DEFAULT_ORIGINS)

    @classmethod
    def from_env(cls) -> Settings:
        raw = os.environ.get("HEMS_CORS_ORIGINS")
        if not raw:
            return cls()
        origins = tuple(part.strip() for part in raw.split(",") if part.strip())
        return cls(cors_origins=origins or DEFAULT_ORIGINS)


settings = Settings.from_env()
