from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import os
import yaml
from .core import build_all, CONFIGS_DIR
from .config_loader import load_all_configs

app = FastAPI(title="Angie Configurator")

def get_html_template(content: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Angie Configurator Dashboard</title>
        <script src="https://unpkg.com/htmx.org@1.9.10"></script>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 p-8">
        <div class="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-lg">
            <h1 class="text-3xl font-bold mb-6 text-gray-800">Angie Configurator Status</h1>
            {content}
        </div>
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    configs, errors = load_all_configs(CONFIGS_DIR)

    error_html = ""
    if errors:
        error_items = "".join([f"<li class='text-red-600'>{err}</li>" for err in errors])
        error_html = f"<div class='mb-4 p-4 bg-red-100 rounded'><ul>{error_items}</ul></div>"

    table_rows = ""
    for config in configs:
        maint_color = "bg-red-500" if config.maintenance else "bg-green-500"
        maint_text = "ON" if config.maintenance else "OFF"
        toggle_action = "off" if config.maintenance else "on"

        table_rows += f"""
        <tr class="border-b">
            <td class="py-2 px-4">{config.project}</td>
            <td class="py-2 px-4">{config.template}</td>
            <td class="py-2 px-4">
                <span class="px-2 py-1 rounded text-white {maint_color}">{maint_text}</span>
            </td>
            <td class="py-2 px-4">
                <button hx-post="/api/maint/{config.project}" hx-vals='{{"state": "{toggle_action}"}}'
                        hx-target="body" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded text-sm">
                    Toggle Maintenance
                </button>
            </td>
        </tr>
        """

    table_html = f"""
    <table class="w-full text-left border-collapse">
        <thead>
            <tr class="bg-gray-200">
                <th class="py-2 px-4 border-b">Domain (Project)</th>
                <th class="py-2 px-4 border-b">Template</th>
                <th class="py-2 px-4 border-b">Maintenance</th>
                <th class="py-2 px-4 border-b">Actions</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    """

    return HTMLResponse(get_html_template(error_html + table_html))

@app.get("/api/status")
async def api_status():
    configs, errors = load_all_configs(CONFIGS_DIR)
    return {
        "configs": [c.model_dump() for c in configs],
        "errors": errors
    }

@app.post("/api/maint/{domain}")
async def toggle_maintenance(domain: str, state: str = Form(...)):
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

    if target_file:
        with open(target_file, 'r') as f:
            data = yaml.safe_load(f)

        data['maintenance'] = (state.lower() == 'on')

        with open(target_file, 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False)

        build_all()

    # Redirect back to dashboard to refresh view (HTMX will handle it since we target body)
    return await dashboard()
