import os
import json
import subprocess
import sys

# dateutil is a third-party library, ensure it's installed in the venv
# pip install python-dateutil
import dateutil.parser
from datetime import datetime, timezone

from atlassian import Confluence

def main():
    """
    Main function to automate the export of all accessible Confluence spaces to Markdown.
    Reads configuration from config.json and generates a temporary config for the exporter tool.
    """
    # --- Read Main Configuration from config.json ---
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config.json")
        example_config_path = os.path.join(script_dir, "config.json.example")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        confluence_config = config['confluence']
        jira_config = config['jira']

        confluence_url = confluence_config['url']
        confluence_user = confluence_config['user']
        confluence_pat = confluence_config['pat']
        
        jira_url = jira_config['url']
        jira_user = jira_config['user']
        jira_pat = jira_config['pat']

        if "YOUR_CONFLUENCE_API_TOKEN_HERE" in confluence_pat or "YOUR_JIRA_API_TOKEN_HERE" in jira_pat:
            print(f"ERROR: Please edit the '{config_path}' file and replace the placeholder API tokens.")
            sys.exit(1)

    except FileNotFoundError:
        if os.path.exists(example_config_path):
            print(f"ERROR: Configuration file not found at '{config_path}'.")
            print(f"Please copy '{example_config_path}' to '{config_path}' and fill in your details.")
        else:
            print(f"ERROR: Configuration file not found at '{config_path}'. Please create it.")
        sys.exit(1)
    except (KeyError, json.JSONDecodeError) as e:
        print(f"ERROR: Configuration file '{config_path}' is invalid or missing keys. {e}")
        sys.exit(1)

    output_directory = "data_export"


    print("\n" + "="*50)
    print(f"Connecting to {confluence_url}...")
    
    # --- Get all spaces using atlassian-python-api ---
    print("Fetching list of all accessible spaces...")
    try:
        confluence = Confluence(url=confluence_url, token=confluence_pat)
        all_spaces_data = {} # Use a dict to handle duplicates automatically based on key
        start = 0
        limit = 50
        while True:
            print(f"Fetching spaces (page starting at {start})...")
            # Expand to get both name and key for each space
            spaces_page = confluence.get_all_spaces(start=start, limit=limit, expand='name,key')
            page_results = spaces_page.get('results', [])
            if not page_results:
                break
            # Store both key and name, using key to ensure uniqueness
            for space in page_results:
                if space['key'] not in all_spaces_data:
                    all_spaces_data[space['key']] = space['name']
            start += len(page_results)

        # Create a sorted list of space info
        spaces = sorted([{'key': k, 'name': v} for k, v in all_spaces_data.items()], key=lambda s: s['key'])
        print(f"Found a total of {len(spaces)} spaces.")

    except Exception as e:
        print(f"\nERROR: Failed to connect to Confluence or retrieve spaces: {e}")
        sys.exit(1)

    # --- Prepare directories and temporary config file ---
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    print(f"All exports will be saved in the '{output_directory}' directory.")

    # This is the config file that the confluence-markdown-exporter tool will read
    tool_config_path = os.path.join(output_directory, "cme_config.json")
    tool_config_data = {
        "auth": {
            "confluence": {
                "url": confluence_url,
                "username": confluence_user,
                "pat": confluence_pat
            },
            "jira": {
                "url": jira_url,
                "username": jira_user,
                "pat": jira_pat
            }
        }
    }
    with open(tool_config_path, 'w', encoding='utf-8') as f:
        json.dump(tool_config_data, f, indent=2, ensure_ascii=False)
    print(f"Generated temporary tool config at: {tool_config_path}")
    print("="*50 + "\n")

    # --- Loop through spaces and export ---
    for i, space_info in enumerate(spaces):
        space_key = space_info['key']
        space_name = space_info['name']

        # Sanitize space name to create directory path
        sanitized_space_name = "".join(c for c in space_name if c not in r'\/\\:*?"<>|')
        dir_name = f"{space_key}_{sanitized_space_name}"
        space_output_path = os.path.join(output_directory, dir_name)
        metadata_path = os.path.join(space_output_path, '.export_info')

        # --- Incremental Download Logic ---
        server_last_modified = None
        try:
            # Find the most recently modified page in the space to determine if the space is stale
            cql_query = f"space='{space_key}' order by lastmodified desc"
            latest_page = confluence.cql(cql_query, limit=1, expand="content.history.lastUpdated")
            if latest_page and latest_page.get('results'):
                server_mod_str = latest_page['results'][0]['content']['history']['lastUpdated']['when']
                server_last_modified = dateutil.parser.isoparse(server_mod_str)
        except Exception as e:
            print(f"WARNING: Could not fetch last modified date for space '{space_key}'. Full export will be attempted. Error: {e}")

        # If the directory doesn't exist, we must export
        if not os.path.isdir(space_output_path):
            print(f"[{i+1}/{len(spaces)}] New space found: '{space_key}'. Preparing for full export.")
        # If directory exists, check modification dates
        elif server_last_modified:
            local_last_exported = None
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        local_mod_str = f.read().strip()
                        if local_mod_str:
                            local_last_exported = dateutil.parser.isoparse(local_mod_str)
                except Exception as e:
                    print(f"WARNING: Could not read or parse local metadata for '{space_key}'. Full export will be attempted. Error: {e}")

            if local_last_exported and server_last_modified <= local_last_exported:
                print(f"[{i+1}/{len(spaces)}] Skipping space '{space_key}'. No new changes detected since last export on {local_last_exported.strftime('%Y-%m-%d')}.")
                print("-"*(len(dir_name) + 30) + "\\n")
                continue
            else:
                if local_last_exported:
                     print(f"[{i+1}/{len(spaces)}] Changes detected for space '{space_key}'. Server modified: {server_last_modified.strftime('%Y-%m-%d %H:%M')}, Last export: {local_last_exported.strftime('%Y-%m-%d %H:%M')}. Exporting.")
                else:
                     print(f"[{i+1}/{len(spaces)}] Found existing directory for '{space_key}' without metadata. Exporting to ensure it is up-to-date.")
        
        # --- Export Process ---
        print(f"[{i+1}/{len(spaces)}] Starting export for space: '{space_name} ({space_key})'")
        
        export_env = os.environ.copy()
        export_env["CME_CONFIG_PATH"] = os.path.abspath(tool_config_path)

        command = [
            sys.executable, # Use the same python interpreter that is running this script
            "-m",
            "confluence_markdown_exporter.main",
            "spaces",
            space_key,
            "--output-path",
            space_output_path,
        ]
        
        try:
            print(f"Running command: {' '.join(command)}")
            subprocess.run(command, check=True, env=export_env, text=True, encoding='utf-8', timeout=18000, capture_output=True)
            print(f"Successfully exported space '{space_key}' to '{dir_name}'.")

            # Write/update the metadata file with the server's last modified date
            if server_last_modified:
                if not os.path.exists(space_output_path):
                    os.makedirs(space_output_path)
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    f.write(server_last_modified.isoformat())
                print(f"Updated local export timestamp for '{space_key}'.")

        except subprocess.TimeoutExpired:
            print(f"TIMEOUT ERROR: Exporting space '{space_key}' took too long (more than 30 minutes) and was skipped.")
        except subprocess.CalledProcessError as e:
            error_output = e.stderr if e.stderr else e.stdout
            if error_output and "ValidationError: 1 validation error for Space homepage Input should be a valid integer" in error_output:
                print(f"WARNING: Space '{space_key}' skipped due to a bug in 'confluence-markdown-exporter': homepage field expects integer but received None (likely because the space has no explicit homepage). Please consider reporting this bug to the 'confluence-markdown-exporter' project.")
                continue # Skip to the next space
            else:
                print(f"ERROR: Failed to export space '{space_key}'. The command failed with exit code {e.returncode}.")
                print(f"Full error details: {error_output}") # Print full error for other issues.
        except Exception as e:
            print(f"An unexpected error occurred while exporting '{space_key}': {e}")

        print("-"*(len(dir_name) + 30) + "\\n")

    print("="*50)
    print("All export tasks are complete.")
    print(f"Check the '{output_directory}' directory for your files.")
    print("="*50)

if __name__ == "__main__":
    main()
