"""配置：FISHQZONE_ 前缀。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Config(BaseModel):
    fishqzone_enabled: bool = Field(default=True, description="启用说说功能")
    fishqzone_admin: str = Field(default="", description="允许发说说的 QQ 号，逗号分隔；空=谁都不许")
    fishqzone_dryrun: bool = Field(default=True, description="演练模式：只算 g_tk 不真发")
    fishqzone_timeout: float = Field(default=20.0, description="请求超时（秒）")