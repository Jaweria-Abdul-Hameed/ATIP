"""Script to export OpenAPI specification to JSON."""

import json
from pathlib import Path
from atip_api.main import app

def export_openapi() -> None:
    openapi_schema = app.openapi()
    output_path = Path(__file__).parent / "openapi.json"
    output_path.write_text(json.dumps(openapi_schema, indent=2), encoding="utf-8")
    print(f"OpenAPI schema exported to {output_path} ({len(openapi_schema.get('paths', {}))} paths)")

if __name__ == "__main__":
    export_openapi()
