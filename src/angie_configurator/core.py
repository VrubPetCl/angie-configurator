import tempfile
import os
import logging
from typing import Tuple

from .config_loader import load_all_configs
from .validator import check_url_collisions
from .renderer import render_to_temp_dir
from .server import test_nginx_config, reload_server, commit_vhosts, backup_yaml, backup_vhosts, restore_vhosts, cleanup_backup

logger = logging.getLogger(__name__)

CONFIGS_DIR = "/etc/angie-configurator/configs"
KNOWN_GOOD_DIR = "/etc/angie-configurator/known-good"
VHOSTS_DIR = "/etc/angie-configurator/vhosts"

def rollback() -> None:
    """Revert the system state using known-good backups."""
    logger.info("Initiating rollback...")

    # 1. Clear configs dir
    if os.path.exists(CONFIGS_DIR):
        for file in os.listdir(CONFIGS_DIR):
            if file.endswith(('.yaml', '.yml')):
                os.remove(os.path.join(CONFIGS_DIR, file))

    # 2. Copy known-good to configs
    if os.path.exists(KNOWN_GOOD_DIR):
        for file in os.listdir(KNOWN_GOOD_DIR):
            if file.endswith(('.yaml', '.yml')):
                import shutil
                shutil.copy2(os.path.join(KNOWN_GOOD_DIR, file), os.path.join(CONFIGS_DIR, file))

    logger.info("Rollback complete. State reverted to known-good.")

def build_all() -> Tuple[bool, str]:
    """
    Orchestrate the build pipeline:
    1. Load configs
    2. Check collisions
    3. Render to temp
    4. Backup active vhosts
    5. Commit new vhosts and test
    6. If test fails, restore vhosts and rollback configs
    7. Commit or rollback
    """
    if not os.path.exists(CONFIGS_DIR):
        return False, f"Configurations directory not found: {CONFIGS_DIR}"

    # 1. Load configs
    configs, errors = load_all_configs(CONFIGS_DIR)
    if errors:
        error_msg = "Failed to load configurations:\n" + "\n".join(errors)
        logger.error(error_msg)
        return False, error_msg

    if not configs:
        return True, "No configurations found to build."

    # 2. Check collisions
    collisions = check_url_collisions(configs)
    if collisions:
        error_msg = "URL collisions detected:\n" + "\n".join(collisions)
        logger.error(error_msg)
        return False, error_msg

    # 3. Render to temp
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            render_to_temp_dir(configs, temp_dir)

            # 4. Backup active vhosts before applying changes
            vhosts_backup_dir = backup_vhosts(VHOSTS_DIR)

            # 5. Commit to vhosts temporarily to test
            commit_vhosts(temp_dir, VHOSTS_DIR)

            # Test configuration
            success, test_output = test_nginx_config()

            if not success:
                logger.error(f"Configuration test failed:\n{test_output}")
                # 6. Restore vhosts to prevent breaking server
                restore_vhosts(VHOSTS_DIR, vhosts_backup_dir)
                rollback()
                return False, f"Configuration test failed. Rolled back.\n{test_output}"

            # 7. Commit and Reload
            logger.info("Configuration test passed. Committing and reloading.")
            cleanup_backup(vhosts_backup_dir)
            backup_yaml(CONFIGS_DIR, KNOWN_GOOD_DIR)

            reload_success, reload_output = reload_server()
            if not reload_success:
                logger.error(f"Server reload failed:\n{reload_output}")
                return False, f"Server reload failed:\n{reload_output}"

            return True, "Build and reload successful."

        except Exception as e:
            logger.exception("Unexpected error during build process.")
            # Assume we need to restore vhosts if we have a backup and hit an exception
            if 'vhosts_backup_dir' in locals():
                restore_vhosts(VHOSTS_DIR, vhosts_backup_dir)
            rollback()
            return False, f"Unexpected error during build: {e}"
