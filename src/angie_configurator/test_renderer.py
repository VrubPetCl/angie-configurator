import os
import tempfile
import pytest
from unittest.mock import patch
from jinja2 import Environment

from angie_configurator.renderer import setup_jinja_env, list_templates, TEMPLATE_DIR

def test_setup_jinja_env():
    with tempfile.TemporaryDirectory() as sys_dir:
        # Mock SYSTEM_TEMPLATE_DIR
        with patch('angie_configurator.renderer.SYSTEM_TEMPLATE_DIR', sys_dir):
            env = setup_jinja_env()
            assert isinstance(env, Environment)

            # The loader should be a list of paths: [SYSTEM_TEMPLATE_DIR, TEMPLATE_DIR]
            loader_paths = env.loader.searchpath
            assert loader_paths == [sys_dir, TEMPLATE_DIR]

def test_list_templates():
    with tempfile.TemporaryDirectory() as sys_dir:
        # Create a mock template in the system directory
        with open(os.path.join(sys_dir, 'custom_override.j2'), 'w') as f:
            f.write('custom')

        with patch('angie_configurator.renderer.SYSTEM_TEMPLATE_DIR', sys_dir):
            templates = list_templates()
            # It should include our custom override template
            assert 'custom_override.j2' in templates

            # It should also include the embedded ones
            assert 'proxy.j2' in templates

def test_template_override():
    with tempfile.TemporaryDirectory() as sys_dir:
        # Create a mock template that overrides an existing one
        with open(os.path.join(sys_dir, 'proxy.j2'), 'w') as f:
            f.write('overridden proxy')

        with patch('angie_configurator.renderer.SYSTEM_TEMPLATE_DIR', sys_dir):
            env = setup_jinja_env()
            template = env.get_template('proxy.j2')

            # Rendering it should return the overridden content
            assert template.render() == 'overridden proxy'
