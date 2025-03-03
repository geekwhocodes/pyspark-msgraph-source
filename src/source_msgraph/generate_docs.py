import os
from urllib.parse import unquote
from source_msgraph.models import BaseResource
from source_msgraph.resources import RESOURCE_CONFIGS

def generate_markdown(resource: BaseResource) -> str:
    """
    Generates sophisticated markdown documentation for a given BaseResource.
    """
    md_content = [f"# {resource.name.capitalize()} Resource", ""]
    md_content.append(f"**Resource Name:** `{resource.name.lower()}`")
    
    
    md_content.append("\n## Overview")
    md_content.append(f"The `{resource.name}` resource provides a structured way to interact with Microsoft Graph API.")
    md_content.append("This resource supports operations such as retrieval and filtering of data.")
    
    md_content.append("\n## Resource Parameters")
    if len(resource.resource_params.keys()) > 0:
        md_content.append("| Parameter | Type | Required | Description |")
        md_content.append("|-----------|------|----------|-------------|")
        for param in resource.resource_params or {}:
            md_content.append(f"| `{unquote(param)}` | `str` | ✅ | Required path parameter for resource access. |")
    else:
        md_content.append(f"> No parameters required for `{resource.name.lower()}` resource.")


    md_content.append("\n## Query Parameters")
    if len(resource.query_params.keys()) > 0:
        md_content.append("| Parameter | Type | Required | Description |")
        md_content.append("|-----------|------|----------|-------------|")
        for param in resource.query_params or {}:
            md_content.append(f"| `{unquote(param)}` | `str` | ❌ | Optional query parameter to refine the API request. |")
    else:
        md_content.append(f">> No query parameters are required for `{resource.name.lower()}` resource.")

    md_content.append("---")
    
    md_content.append("Tip: Please refer [Microsoft Graph API]() documentation if you don't see a field. This can be resolved by provising `expand` option.")

    md_content.append("\n## Example Usage")
    md_content.append("```python")
    md_content.append("from source_msgraph.source import MSGraphDataSource")
    md_content.append("spark.dataSource.register(MSGraphDataSource)")
    md_content.append("")
    md_content.append("# Read data using Microsoft Graph")
    md_content.append("df = spark.read.format(\"msgraph\") ")
    md_content.append("    .option(\"tenant_id\", tenant_id)")
    md_content.append("    .option(\"client_id\", client_id)")
    md_content.append("    .option(\"client_secret\", client_secret)")
    md_content.append(f"    .option(\"resource\", \"{resource.name}\")")
    for param in resource.resource_params or {}:
        md_content.append(f"    .option(\"{param}\", \"<value>\")")
    for param in resource.query_params or {}:
        md_content.append(f"    .option(\"{param}\", \"<value>\")")
    md_content.append("    .schema(\"id string, eTag string\")")
    md_content.append("    .load()")
    md_content.append("")
    md_content.append("df.show()")
    md_content.append("```")
    
    return "\n".join(md_content)

def generate_docs(output_dir: str = "docs"):
    """
    Generates sophisticated markdown documentation for all configured resources.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for config in RESOURCE_CONFIGS:
        resource = BaseResource(
            name=config["name"],
            resource_name=config["resource_name"],
            request_builder_module=config["request_builder_module"]
        )
        
        md_content = generate_markdown(resource)
        file_path = os.path.join(output_dir, f"{resource.name}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"Generated documentation: {file_path}")

if __name__ == "__main__":
    generate_docs()