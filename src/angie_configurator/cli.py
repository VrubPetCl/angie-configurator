import click
import time
import os
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .core import build_all, CONFIGS_DIR
from .config_loader import load_all_configs
from .server import test_nginx_config

@click.group()
def cli():
    """Angie Configurator CLI"""
    pass

@cli.command()
def build():
    """Force validation and rebuild of all configurations."""
    click.echo("Starting build process...")
    success, message = build_all()
    if success:
        click.secho(message, fg="green")
    else:
        click.secho(f"Build failed:\n{message}", fg="red")

class ConfigEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(('.yaml', '.yml')):
            click.echo(f"File changed: {event.src_path}. Triggering build...")
            success, message = build_all()
            if success:
                click.secho(message, fg="green")
            else:
                click.secho(f"Build failed:\n{message}", fg="red")

@cli.command()
def watch():
    """Run background watchdog on configs/ directory."""
    if not os.path.exists(CONFIGS_DIR):
        click.secho(f"Configs directory not found: {CONFIGS_DIR}", fg="red")
        return

    event_handler = ConfigEventHandler()
    observer = Observer()
    observer.schedule(event_handler, CONFIGS_DIR, recursive=True)
    observer.start()
    click.echo(f"Watching {CONFIGS_DIR} for changes...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

@cli.command()
@click.argument('domain')
@click.option('--on/--off', 'maint_state', required=True, help="Turn maintenance mode on or off.")
def maint(domain: str, maint_state: bool):
    """Fast maintenance toggle for a specific domain."""
    configs, _ = load_all_configs(CONFIGS_DIR)

    target_file = None
    for root, _, files in os.walk(CONFIGS_DIR):
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    data = yaml.safe_load(f)
                    if data and data.get('project') == domain:
                        target_file = filepath
                        break
        if target_file:
            break

    if not target_file:
        click.secho(f"Domain {domain} not found in configurations.", fg="red")
        return

    with open(target_file, 'r') as f:
        data = yaml.safe_load(f)

    data['maintenance'] = maint_state

    with open(target_file, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False)

    click.echo(f"Maintenance mode for {domain} set to {maint_state}. Triggering build...")
    success, message = build_all()
    if success:
        click.secho(message, fg="green")
    else:
        click.secho(f"Build failed:\n{message}", fg="red")

@cli.command()
def status():
    """Outputs list of domains, template used, and current health state."""
    configs, errors = load_all_configs(CONFIGS_DIR)

    if errors:
        click.secho("Warning: Some configurations have errors:", fg="yellow")
        for error in errors:
            click.echo(error)

    click.echo("\n--- Server Health ---")
    health_success, health_msg = test_nginx_config()
    if health_success:
        click.secho("Angie State: HEALTHY", fg="green")
    else:
        click.secho(f"Angie State: ERROR\n{health_msg}", fg="red")

    click.echo("\n--- Domain Status ---")
    click.echo(f"{'Domain (Project)':<30} | {'Template':<15} | {'Maintenance'}")
    click.echo("-" * 65)
    for config in configs:
        maint_str = "ON" if config.maintenance else "OFF"
        click.echo(f"{config.project:<30} | {config.template:<15} | {maint_str}")
