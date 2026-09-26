# JobOps MCP

Experiment with MCP server to provide requestor with agentic job application support.

JobOps MCP is a [Model Context Protocol](https://modelcontextprotocol.io) server that turns an AI agent into an assistant for running a job search: logging applications, tracking pipeline status, pulling in job postings from public career sites, and drafting tailored application documents — all backed by a local SQLite database. It started as a personal project to help streamline a job search and as a hands-on way to explore MCP server design, transport security, and cloud deployment.

## What it does

### Tools
| Tool | Description |
|---|---|
| `log_new_application(company, role, notes="")` | Log a new job application into the tracking database. |
| `get_pipeline(status="")` | List applications in the pipeline, optionally filtered by status (`Applied`, `Screen scheduled`, `Interviewing`, `Rejected`, `Offer`). |
| `update_application(app_id, new_status, notes="")` | Update an application's status and append notes. |
| `audit_stale_applications(days_stale=14)` | Flag applications with no status update in more than N days — a lightweight SLA audit over your own pipeline. |
| `fetch_job_posting(url)` | Fetch and extract the readable text of a public job posting (Greenhouse, Lever, Indeed, company career pages). Returned content is explicitly wrapped and labeled as untrusted external data. |
| `save_tailored_document(company, doc_type, content)` | Save a tailored document — cover letter, resume notes, interview prep summary — as a Markdown file under `output/`. |

### Resources
- `profile://master-resume` — exposes a candidate master-resume file (`profile_docs/master_resume.md`, created on first run) as context for the agent.

### Prompts
- `prepare_interview(company)` — a reusable prompt that has the agent cross-reference the master resume and past notes for a given company, then produce a short technical-fit summary and interview questions to ask.

## Getting started

### Requirements
- Python 3.12+
- (Optional) Docker, for containerized runs

### Install
```bash
pip install -r requirements.txt
```

### Run locally (stdio)
By default the server speaks stdio — the standard transport for a locally-launched MCP server:
```bash
python server.py
```
Point your MCP client (Claude Desktop, Claude Code, etc.) at this command directly, or use the included `run-inspector.ps1` to test it with the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

### Run with Docker
```bash
docker build -t jobops-mcp .
docker run -i --rm jobops-mcp
```

### Tests
```bash
pytest
```
Covers the SQLite layer, the job-posting scraper's SSRF/URL-safety checks (including redirect handling), and the HTTP transport's auth and host-validation logic.

## Remote / cloud hosting

The server can also run over **Streamable HTTP**, so it can be hosted on a remote machine instead of launched as a local subprocess. This is controlled entirely through environment variables — the default behavior above is unaffected unless you opt in.

| Variable | Required for HTTP? | Purpose |
|---|---|---|
| `MCP_TRANSPORT` | — | Set to `http` to enable Streamable HTTP. Defaults to `stdio`. |
| `MCP_HOST` | No | Bind address. Defaults to `0.0.0.0`. |
| `MCP_PORT` | No | Bind port. Defaults to `8000`. |
| `MCP_AUTH_TOKEN` | **Yes** | Shared-secret bearer token. The server refuses to start over HTTP without one. |
| `MCP_ALLOWED_HOST` | Only once hosted behind a real hostname | Allow-lists that hostname for the SDK's DNS-rebinding protection (which otherwise only trusts `localhost`/`127.0.0.1`). Leave unset for local testing. |

Example:
```bash
docker run -d -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e MCP_AUTH_TOKEN="$(openssl rand -hex 32)" \
  -e MCP_ALLOWED_HOST=your-hostname.example.com \
  jobops-mcp
```

### Connecting a remote client
- **Claude Code:** supports custom headers natively —
  ```bash
  claude mcp add --transport http jobops https://your-host/mcp --header "Authorization: Bearer <token>"
  ```
- **Claude Desktop:** its native remote-server support has no header field, so a bearer-token server like this one needs the [`mcp-remote`](https://www.npmjs.com/package/mcp-remote) bridge in `claude_desktop_config.json`, passing the token via `--header`. On Windows, install `mcp-remote` globally (`npm install -g mcp-remote`) rather than launching it through `npx` — a space in the default `C:\Program Files\nodejs` path can otherwise break how the command line gets assembled.

## Security notes

A few things worth knowing about how this is hardened, since the server is designed to be safely exposed beyond a single trusted local process:
- **Bearer-token auth** on the HTTP transport — the server won't start over HTTP without a token configured, and every request is checked before reaching any tool.
- **DNS-rebinding protection** via the MCP SDK's host-allowlisting, scoped to whatever hostname it's actually deployed behind.
- **SSRF protection** on `fetch_job_posting` — target URLs, and any redirects they issue, are resolved and rejected if any resolved address is private, loopback, link-local, or reserved, so the tool can't be used to reach internal network addresses or cloud metadata endpoints.
- **Path-traversal protection** on `save_tailored_document` — output filenames are sanitized and the resolved path is checked to stay inside the intended output directory.
- **Untrusted-content framing** — text scraped from external job postings is wrapped and explicitly labeled as untrusted data, with an instruction not to treat it as commands, to reduce prompt-injection risk from a malicious posting.

## Project structure
```
server.py       MCP server: tools, resources, prompts, transport/auth setup
db.py           SQLite persistence for the application pipeline
scraper.py      Job-posting fetcher with SSRF hardening
writer.py       Tailored-document writer with path-traversal hardening
tests/          pytest suite
Dockerfile      Container build
requirements.txt
run-inspector.ps1   Local MCP Inspector helper (PowerShell)
```
