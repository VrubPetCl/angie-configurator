import os
from typing import Tuple, Optional

LETSENCRYPT_DIR = "/etc/letsencrypt/live"
MANUAL_CERTS_DIR = "/etc/angie-configurator/certificates"

def get_ssl_paths(ssl_cert_id: str) -> Optional[Tuple[str, str]]:
    """
    Resolve an ssl_cert ID to certificate and key paths.
    Checks Let's Encrypt live directory and manual certificates directory.
    Returns (cert_path, key_path) or None if not found.
    """
    if not ssl_cert_id:
        return None

    # Check Let's Encrypt
    le_cert_path = os.path.join(LETSENCRYPT_DIR, ssl_cert_id, "fullchain.pem")
    le_key_path = os.path.join(LETSENCRYPT_DIR, ssl_cert_id, "privkey.pem")

    if os.path.exists(le_cert_path) and os.path.exists(le_key_path):
        return (le_cert_path, le_key_path)

    # Check Manual Certificates mapping
    # Assuming manual certs are named like <id>.crt and <id>.key
    manual_cert_path = os.path.join(MANUAL_CERTS_DIR, f"{ssl_cert_id}.crt")
    manual_key_path = os.path.join(MANUAL_CERTS_DIR, f"{ssl_cert_id}.key")

    # We will assume if they requested it and it doesn't exist yet, we still
    # generate the config to point there. Nginx will fail the test if they don't exist.
    # However, for a robust configurator, we should point to the manual paths if we don't find it in LE.
    return (manual_cert_path, manual_key_path)
