import requests
import yaml

url = "https://www.api-football.com/public/doc/openapi.yaml"
yaml_path = "./docs/api/api_football_openapi.yaml"
md_path = "./docs/api/api_football_doc.md"

response = requests.get(url)
with open(yaml_path, "wb") as f:
    f.write(response.content)

with open(yaml_path, "r", encoding="utf-8") as f:
    spec = yaml.safe_load(f)

with open(md_path, "w", encoding="utf-8") as md:
    md.write(f"# {spec.get('info', {}).get('title', 'API-Football')}\n\n")
    md.write(f"**Descrição:** {spec.get('info', {}).get('description', '')}\n\n")
    md.write("## Endpoints\n\n")
    for path, methods in spec.get("paths", {}).items():
        md.write(f"### `{path}`\n")
        for method, details in methods.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch", "options", "head"]:
                continue
            md.write(f"- **{method.upper()}**: {details.get('summary', '')}\n")
            if "description" in details:
                md.write(f"  - {details['description']}\n")
        md.write("\n")