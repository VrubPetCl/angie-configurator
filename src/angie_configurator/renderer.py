import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .schema import DomainConfig
from .ssl_manager import get_ssl_paths

SYSTEM_TEMPLATE_DIR = "/etc/angie-configurator/templates"
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')

def setup_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader([SYSTEM_TEMPLATE_DIR, TEMPLATE_DIR]),
        autoescape=select_autoescape(['html', 'xml', 'j2'])
    )

def list_templates() -> list[str]:
    env = setup_jinja_env()
    return env.list_templates(filter_func=lambda x: x.endswith('.j2'))

def render_config(config: DomainConfig, env: Environment = None) -> str:
    """Render a single DomainConfig into a configuration string."""
    if env is None:
        env = setup_jinja_env()

    template_name = config.template
    if not template_name.endswith('.j2'):
        template_name += '.j2'

    template = env.get_template(template_name)

    ssl_paths = None
    if config.ssl_cert:
        ssl_paths = get_ssl_paths(config.ssl_cert)

    return template.render(config=config, ssl_paths=ssl_paths)

def render_to_temp_dir(configs: list[DomainConfig], temp_dir: str) -> dict[str, str]:
    """Render all configs to a temporary directory."""
    env = setup_jinja_env()
    rendered_files = {}
    for config in configs:
        rendered = render_config(config, env)
        out_path = os.path.join(temp_dir, f"{config.project}.conf")
        with open(out_path, 'w') as f:
            f.write(rendered)
        rendered_files[config.project] = out_path
    return rendered_files
