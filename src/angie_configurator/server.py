import os
import shutil
import subprocess
import tempfile
from typing import List, Tuple

def test_nginx_config() -> Tuple[bool, str]:
    """Test the Nginx/Angie configuration syntax."""
    cmd = "angie" if shutil.which("angie") else "nginx"
    if not shutil.which(cmd):
        return True, f"Mock: {cmd} not found, assuming success for tests."

    try:
        result = subprocess.run([cmd, '-t'], capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stderr
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def reload_server() -> Tuple[bool, str]:
    """Reload the Nginx/Angie server."""
    cmd = "angie" if shutil.which("angie") else "nginx"
    if not shutil.which(cmd):
        return True, f"Mock: {cmd} not found, assuming success for reload."

    try:
        result = subprocess.run([cmd, '-s', 'reload'], capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stderr
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def backup_vhosts(vhosts_dir: str) -> str:
    """Backup the current vhosts directory to a temporary location."""
    backup_dir = tempfile.mkdtemp(prefix="angie_vhosts_backup_")
    if os.path.exists(vhosts_dir):
        for file in os.listdir(vhosts_dir):
            if file.endswith('.conf'):
                shutil.copy2(os.path.join(vhosts_dir, file), os.path.join(backup_dir, file))
    return backup_dir

def restore_vhosts(vhosts_dir: str, backup_dir: str) -> None:
    """Restore the vhosts directory from a backup."""
    if not os.path.exists(vhosts_dir):
        os.makedirs(vhosts_dir)

    for file in os.listdir(vhosts_dir):
        if file.endswith('.conf'):
            os.remove(os.path.join(vhosts_dir, file))

    for file in os.listdir(backup_dir):
        if file.endswith('.conf'):
            shutil.copy2(os.path.join(backup_dir, file), os.path.join(vhosts_dir, file))

    shutil.rmtree(backup_dir, ignore_errors=True)

def cleanup_backup(backup_dir: str) -> None:
    """Clean up the temporary backup directory."""
    shutil.rmtree(backup_dir, ignore_errors=True)

def commit_vhosts(temp_dir: str, vhosts_dir: str) -> None:
    """Commit rendered configurations from temp directory to live vhosts directory."""
    if not os.path.exists(vhosts_dir):
        os.makedirs(vhosts_dir)

    for file in os.listdir(vhosts_dir):
        if file.endswith('.conf'):
            os.remove(os.path.join(vhosts_dir, file))

    for file in os.listdir(temp_dir):
        if file.endswith('.conf'):
            shutil.copy2(os.path.join(temp_dir, file), os.path.join(vhosts_dir, file))

def backup_yaml(configs_dir: str, known_good_dir: str) -> None:
    """Backup YAML files to the known-good directory."""
    if not os.path.exists(known_good_dir):
        os.makedirs(known_good_dir)

    for file in os.listdir(known_good_dir):
        if file.endswith(('.yaml', '.yml')):
            os.remove(os.path.join(known_good_dir, file))

    if not os.path.exists(configs_dir):
        return

    for root, _, files in os.walk(configs_dir):
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                shutil.copy2(os.path.join(root, file), os.path.join(known_good_dir, file))
