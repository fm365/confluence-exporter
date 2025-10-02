[English Readme](README.md)

# Confluence 全量导出工具

这是一个 Python 脚本，用于自动化地将 Confluence 中所有可访问的空间（Space）备份导出为 Markdown 格式。它底层利用了 [confluence-markdown-exporter](https://github.com/confluence-publisher/confluence-markdown-exporter) 工具，并增加了以下功能：

## 主要功能

- **全量空间导出**：自动发现并遍历用户有权限访问的所有 Confluence 空间。
- **增量更新**：在重复运行时，通过对比 Confluence 空间的最后修改时间和本地备份的元数据，只下载有更新的空间，大大节省时间。
- **配置简单**：通过单个 `config.json` 文件管理所有认证信息。
- **易于使用**：无需手动为每个空间执行命令。

## 环境准备

- Python 3.8+
- Git

## 安装与配置

**1. 克隆仓库**

```bash
git clone <your-repository-url>
cd confluence-exporter
```

**2. 创建并激活 Python 虚拟环境**

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

**3. 安装依赖**

```bash
pip install -r requirements.txt
```

**4. 配置认证信息**

你需要一个 Confluence API 令牌（PAT）来进行身份验证。

a. 复制示例配置文件：

```bash
cp config.json.example config.json
```

b. 编辑 `config.json` 文件，填入你的信息：

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

- `url`: 你的 Confluence/Jira 实例地址。
- `user`: 你的登录邮箱。
- `pat`: 你的个人访问令牌。可以从 [这里](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/) 创建。

> **注意**: `config.json` 文件已被 `.gitignore` 忽略，所以你的密钥不会被提交到 Git 仓库中。

## 如何使用

完成配置后，直接运行主脚本即可：

```bash
python export_all_confluence_data.py
```

脚本会执行以下操作：
1. 连接到 Confluence 并获取所有空间的列表。
2. 在项目根目录下创建一个名为 `data_export` 的文件夹。
3. 遍历每一个空间，检查是否需要更新。
4. 对需要更新的空间，调用 `confluence-markdown-exporter` 将其导出到 `data_export` 目录下的独立文件夹中。
5. 导出成功后，记录本次导出时间，用于下次增量更新判断。

## 许可证

本项目采用 [MIT](https://choosealicense.com/licenses/mit/) 许可证。
