from typing import List, Tuple
from .schema import DomainConfig

def check_url_collisions(configs: List[DomainConfig]) -> List[str]:
    """Check if multiple configurations attempt to bind to the same URL."""
    url_to_project = {}
    collisions = []
    for config in configs:
        for url in config.urls:
            if url in url_to_project:
                collisions.append(
                    f"Collision detected: URL '{url}' is defined in both '{url_to_project[url]}' and '{config.project}'."
                )
            else:
                url_to_project[url] = config.project
    return collisions
