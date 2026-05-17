# Angie Configurator (Angie-Gen) User Guide

This guide serves as the single source of truth for configuring, templating, and managing the Angie Configurator (Angie-Gen).

## 1. Creating Configuration Files (YAML)

All domain configurations are written in YAML and must be placed in `/etc/angie-configurator/configs/`. Each domain should have its own file (e.g., `example.com.yaml`).

### Available Settings

The configuration uses a strict schema. Below are all available fields for a single domain file:

- **`project`** (`str`, Required): The primary identifier or name of the project (usually the main domain).
- **`urls`** (`List[str]`, Required): A list of domain names or server names this configuration applies to (e.g., `["example.com", "www.example.com"]`).
- **`ports`** (`List[int]`, Optional, Default: `[80, 443]`): The ports to listen on.
- **`template`** (`str`, Required): The name of the Jinja2 template to use (e.g., `"proxy"`, `"static"`, `"wordpress"`). The `.j2` extension is optional.
- **`ssl_cert`** (`str`, Optional): The name of the SSL certificate. The system will look for matching Let's Encrypt live certs or custom certs in `/etc/angie-configurator/certificates/`.
- **`maintenance`** (`bool`, Optional, Default: `false`): Toggles maintenance mode (HTTP 503).
- **`maint_page`** (`str`, Optional): The filename of a custom maintenance HTML page placed in `/etc/angie-configurator/maintenance/`.
- **`allowed_ips`** (`List[str]`, Optional): A list of IP addresses allowed to bypass restrictions or access the site.
- **`allow_cloudflare`** (`bool`, Optional, Default: `false`): If true, configures the server to allow Cloudflare IPs and handle real IP headers correctly.
- **`caching`** (`dict`, Optional): Settings related to server and client caching.
  - `server_cache` (`bool`, Default: `false`): Enables server-side caching.
  - `purge_endpoint` (`bool`, Default: `false`): Enables a cache purge endpoint.
  - `client_headers` (`bool`, Default: `false`): Adds client-side caching headers.
- **`proxy_config`** (`dict`, Optional): Configuration for reverse proxy setups.
  - `source_port` (`int`, Optional)
  - `dest_addr` (`str`, Optional): Destination address (e.g., `"127.0.0.1"`).
  - `dest_port` (`int`, Optional): Destination port (e.g., `3000`).
  - `raw_config` (`str`, Optional): Raw Nginx/Angie config block to append.
- **`locations`** (`dict`, Optional): Define custom location blocks, keyed by path (e.g., `/api`).
  - `proxy_config` (`dict`, Optional): Similar to the global `proxy_config` but applies only to this location.

---

## 2. Creating and Formatting Templates

Angie-Gen uses Jinja2 for rendering configuration files.

### Template Directories
Templates are loaded from two locations:
1. `/etc/angie-configurator/templates/` (System-wide templates)
2. `src/angie_configurator/templates/` (Built-in templates: `proxy.j2`, `static.j2`, `wordpress.j2`)

You can create custom templates in `/etc/angie-configurator/templates/`.

### Writing Custom Templates

When a template is rendered, it is provided with two main context variables:
- `config`: An instance of `DomainConfig` (the parsed YAML file).
- `ssl_paths`: A dictionary containing `fullchain` and `privkey` paths if `ssl_cert` is defined.

**Example: `custom_app.j2`**
```nginx
server {
    listen {{ config.ports[0] }};
    server_name {{ config.urls | join(' ') }};

    {% if ssl_paths %}
    listen 443 ssl;
    ssl_certificate {{ ssl_paths.fullchain }};
    ssl_certificate_key {{ ssl_paths.privkey }};
    {% endif %}

    location / {
        {% if config.proxy_config %}
        proxy_pass http://{{ config.proxy_config.dest_addr }}:{{ config.proxy_config.dest_port }};
        proxy_set_header Host $host;
        {% else %}
        root /var/www/{{ config.project }};
        {% endif %}
    }
}
```

To use this template, set `template: "custom_app"` in your YAML configuration.

---

## 3. Most Common Usecases

### A. Reverse Proxy (Node.js, Python, Docker)
Forward traffic to an application running on localhost.

```yaml
project: "myapp"
urls: ["app.example.com"]
template: "proxy"
ssl_cert: "app.example.com"
proxy_config:
  dest_addr: "127.0.0.1"
  dest_port: 8080
```

### B. Static Website
Serve HTML/CSS/JS files directly from the filesystem.

```yaml
project: "mywebsite"
urls: ["example.com", "www.example.com"]
template: "static"
ssl_cert: "example.com"
```
*(Note: Ensure your `static.j2` template specifies the `root` directive, typically pointing to `/var/www/{{ config.project }}`)*

### C. WordPress Site
Run a standard PHP-FPM WordPress installation.

```yaml
project: "myblog"
urls: ["blog.example.com"]
template: "wordpress"
ssl_cert: "blog.example.com"
```

---

## 4. Setting up Watchdog as a Service

To automatically rebuild configurations when YAML files change, you can run `angie-gen watch`. It's best to run this as a background service.

### Option A: systemd Service (Debian/Ubuntu/CentOS)

1. Create a new service file:
   ```bash
   sudo touch /etc/systemd/system/angie-gen.service
   # Open this file with your favorite editor
   ```

2. Add the following configuration (adjust the path to `angie-gen` if it's installed in a virtual environment):
   ```ini
   [Unit]
   Description=Angie Configurator Watchdog
   After=network.target

   [Service]
   Type=simple
   User=root
   ExecStart=/usr/local/bin/angie-gen watch
   Restart=on-failure
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable angie-gen
   sudo systemctl start angie-gen
   ```

### Option B: init.d / OpenRC Service (Alpine/Gentoo)

1. Create a script in `/etc/init.d/`:
   ```bash
   sudo touch /etc/init.d/angie-gen
   # Open this file with your favorite editor
   ```

2. Add the following OpenRC script:
   ```bash
   #!/sbin/openrc-run

   name="angie-gen-watchdog"
   description="Angie Configurator Watchdog"
   command="/usr/local/bin/angie-gen"
   command_args="watch"
   command_background="yes"
   pidfile="/run/${name}.pid"
   output_log="/var/log/angie-gen.log"
   error_log="/var/log/angie-gen.err"

   depend() {
       need net
       after firewall
   }
   ```

3. Make it executable, enable, and start:
   ```bash
   sudo chmod +x /etc/init.d/angie-gen
   sudo rc-update add angie-gen default
   sudo rc-service angie-gen start
   ```
