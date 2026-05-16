import urllib.request
import json
import os
import logging

logger = logging.getLogger(__name__)

CLOUDFLARE_IPS_URL = "https://api.cloudflare.com/client/v4/ips"
CLOUDFLARE_IPS_FILE = "/etc/angie-configurator/cloudflare-ips.conf"

def fetch_cloudflare_ips():
    """Fetches Cloudflare IPs from the official API."""
    try:
        req = urllib.request.Request(CLOUDFLARE_IPS_URL)
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read())
            if data.get('success'):
                ipv4 = data['result'].get('ipv4_cidrs', [])
                ipv6 = data['result'].get('ipv6_cidrs', [])
                return ipv4 + ipv6
            else:
                logger.error("Failed to fetch Cloudflare IPs: API success=False")
                return []
    except Exception as e:
        logger.error(f"Error fetching Cloudflare IPs: {e}")
        return []

def update_cloudflare_ips():
    """
    Fetches the latest Cloudflare IPs and writes them to the configuration file.
    Returns True if the file was created or updated, False otherwise.
    """
    ips = fetch_cloudflare_ips()
    if not ips:
        logger.warning("No IPs fetched from Cloudflare. Skipping update.")
        return False

    new_content = "\n".join([f"allow {ip};" for ip in ips]) + "\n"

    try:
        # Check if file exists and has the same content
        if os.path.exists(CLOUDFLARE_IPS_FILE):
            with open(CLOUDFLARE_IPS_FILE, 'r') as f:
                current_content = f.read()
            if current_content == new_content:
                logger.info("Cloudflare IPs are up to date.")
                return False

        # Ensure directory exists
        os.makedirs(os.path.dirname(CLOUDFLARE_IPS_FILE), exist_ok=True)

        # Write new content
        with open(CLOUDFLARE_IPS_FILE, 'w') as f:
            f.write(new_content)

        logger.info(f"Successfully updated Cloudflare IPs in {CLOUDFLARE_IPS_FILE}.")
        return True
    except Exception as e:
        logger.error(f"Error writing Cloudflare IPs to {CLOUDFLARE_IPS_FILE}: {e}")
        return False
