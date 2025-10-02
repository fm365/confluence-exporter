[中文说明](README_zh.md)

# Confluence Export Tool

This is a Python script designed to automate the export of all accessible Confluence spaces to Markdown format. It leverages the [confluence-markdown-exporter](https://github.com/Spenhouet/confluence-markdown-exporter) tool and adds the following features:

## Key Features

- **Full Space Export**: Automatically discovers and iterates through all Confluence spaces accessible to the user.
- **Incremental Updates**: When run repeatedly, it checks the last modified time of Confluence spaces against local export metadata, only downloading spaces that have been updated, significantly saving time.
- **Simple Configuration**: Manages all authentication information through a single `config.json` file.
- **Easy to Use**: No need to manually execute commands for each space.

## Prerequisites

- Python 3.8+
- Git

## Installation & Configuration

**1. Clone the repository**

```bash
git clone https://github.com/fm365/confluence-exporter.git
cd confluence-exporter
```

**2. Create and activate a Python virtual environment**

- **macOS / Linux**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- **Windows**
  ```bash
  python -m venv venv
  .\venv\Scripts\activate
  ```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure authentication**

You will need a Confluence API Token (PAT) for authentication.

a. Copy the example configuration file:

```bash
cp config.json.example config.json
```

b. Edit the `config.json` file and fill in your details:

```json
{
  "confluence": {
    "url": "https://your-domain.atlassian.net/wiki",
    "user": "your-email@example.com",
    "pat": "YOUR_CONFLUENCE_API_TOKEN_HERE"
  },
  "jira": {
    "url": "https://your-domain.atlassian.net",
    "user": "your-email@example.com",
    "pat": "YOUR_JIRA_API_TOKEN_HERE"
  }
}
```

- `url`: Your Confluence/Jira instance URL.
- `user`: Your login email.
- `pat`: Your Personal Access Token. You can create one [here](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/).

> **Note**: The `config.json` file is ignored by `.gitignore`, so your secrets will not be committed to the Git repository.

## How to Use

Once configured, simply run the main script:

```bash
python export_all_confluence_data.py
```

The script will perform the following actions:
1. Connect to Confluence and fetch a list of all spaces.
2. Create a folder named `data_export` in the project root directory.
3. Iterate through each space, checking if an update is needed.
4. For spaces requiring updates, it calls `confluence-markdown-exporter` to export them into separate folders within the `data_export` directory.
5. After successful export, it records the export timestamp for future incremental updates.

## License

This project is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).
