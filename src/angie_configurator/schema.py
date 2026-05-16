from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict

class CachingConfig(BaseModel):
    server_cache: bool = False
    purge_endpoint: bool = False
    client_headers: bool = False

class ProxyConfig(BaseModel):
    source_port: Optional[int] = None
    dest_addr: Optional[str] = None
    dest_port: Optional[int] = None
    raw_config: Optional[str] = None

class LocationConfig(BaseModel):
    proxy_config: Optional[ProxyConfig] = None

class DomainConfig(BaseModel):
    project: str
    urls: List[str]
    ports: List[int] = Field(default_factory=lambda: [80, 443])
    template: str
    ssl_cert: Optional[str] = None
    maintenance: bool = False
    maint_page: Optional[str] = None
    allowed_ips: Optional[List[str]] = None
    allow_cloudflare: bool = False
    caching: Optional[CachingConfig] = None
    proxy_config: Optional[ProxyConfig] = None
    locations: Optional[Dict[str, LocationConfig]] = None

    @field_validator('ports', mode='before')
    def default_ports(cls, v):
        if not v:
            return [80, 443]
        return v
