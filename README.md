# Angie Configurator (Angie-Gen)

A Python-based management layer for the Angie (or Nginx) webserver. It uses individual YAML files per domain as the single source of truth, performs strict Pydantic validation, and features a robust atomic rollback mechanism to guarantee your webserver configuration is never broken.

## Features

- **YAML Source of Truth**: Manage domains declaratively.
- **Strict Validation**: Avoid overlapping URLs and syntax errors.
- **Atomic Rollbacks**: Automatically revert configurations if the new generated `angie.conf` fails `angie -t` tests.
- **Jinja2 Templates**: Out-of-the-box support for `proxy`, `static`, and `wordpress` setups.
- **SSL Management**: Maps Let's Encrypt live certs and manual certificates effortlessly.
- **Maintenance Mode**: Fast 503 toggles with custom HTML page support.
- **CLI Utility (`angie-gen`)**: Easy terminal commands to watch, build, and toggle maintenance.
- **Web UI Dashboard**: FastAPI + HTMX dashboard to visually review the state and toggle maintenance globally.

## Setup & Deployment

### Prerequisites

- Python 3.9+
- Angie or Nginx installed and accessible on your path.
- Root or `sudo` privileges to modify `/etc/` configurations.

### 1. Directory Structure

The system persists state in `/etc/angie-configurator/`. Create the required directories and adjust permissions so your user/group (or the user running the application) has access:

```bash
sudo mkdir -p /etc/angie-configurator/{configs,known-good,templates,certificates,maintenance,vhosts}
sudo chown -R $USER:$USER /etc/angie-configurator
```

*(Note: In a production environment, run the app as a dedicated user and restrict permissions accordingly.)*

Ensure you include your `vhosts` configurations inside your main Angie/Nginx configuration file (e.g., `/etc/angie/angie.conf` or `/etc/nginx/nginx.conf`):

```nginx
http {
    # ...
    include /etc/angie-configurator/vhosts/*.conf;
    # ...
}
```

### 2. Installation

Clone the repository and install it locally using `pip`:

```bash
git clone <repo_url>
cd <repo_directory>
pip install -e .
```

This will install the package along with its dependencies (`fastapi`, `uvicorn`, `jinja2`, `pydantic`, `pyyaml`, `watchdog`, `click`, `python-multipart`) and set up the `angie-gen` CLI command.

### 3. Example YAML Configuration

Place YAML configuration files inside `/etc/angie-configurator/configs/`. Each domain gets its own file (e.g., `example.com.yaml`).

```yaml
project: "example.com"
urls: ["example.com", "www.example.com"]
ports: [80, 443]
template: "proxy"
ssl_cert: "example.com"  # Resolves Let's Encrypt or manual certs
maintenance: false
maint_page: "maintenance.html"
caching:
  client_headers: true
proxy_config:
  dest_addr: "127.0.0.1"
  dest_port: 3000
```

## CLI Usage

The system exposes the `angie-gen` tool:

```bash
# Display the health status of Angie and a list of all managed domains
angie-gen status

# Force parse YAML files, validate, render, and rebuild vhosts configurations
angie-gen build

# Enable maintenance mode instantly for a specific domain and trigger a build
angie-gen maint example.com --on
angie-gen maint example.com --off

# Run a watchdog process in the background that rebuilds whenever YAML files in `configs/` change
angie-gen watch
```

## Dashboard Web UI

You can start the FastAPI dashboard to visually manage configurations and maintenance modes.

Run the dashboard server using Uvicorn:

```bash
uvicorn angie_configurator.app:app --host 0.0.0.0 --port 8000
```

Navigate to `http://localhost:8000` to view the dashboard and toggle states.
