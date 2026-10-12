# Attendee Guide: From Zero to a Semantic Graph Layer for Your Agents

This guide takes you from an empty machine to a working pipeline:

```
Snowflake (INFORMATION_SCHEMA metadata)
        │  neocarta snowflake schema
        ▼
Neo4j semantic graph  ──(embeddings, optional)──▶  vector + full-text search
        │  neocarta-mcp
        ▼
Your AI agent (grounded in what your data is, means, and how it joins)
```

Only **metadata** (databases, schemas, tables, columns, keys, a few sample values) is copied into Neo4j. Your data stays in Snowflake.

During the workshop we demo with ready-made assets to keep the pace up. Everything here is what you need to rebuild it yourself, from scratch, afterwards.

**Time to complete:** about 45 minutes (most of it account setup).

**Two ways through the material.** The notebooks are the guided labs; the sections below (7.x) show the same steps as plain CLI commands.

| Lab | Notebook | What you do |
|---|---|---|
| 00 | `00_prerequisites_and_connectivity.ipynb` | Read-only environment, Neo4j, Snowflake and connector checks |
| 01 | `01_load_metadata_into_graph.ipynb` | Load Snowflake metadata into Neo4j (physical layer) |
| 02 | `02_load_semantic_layer.ipynb` | Add business meaning, joins and metrics from an OSI YAML file |
| 03 | `03_build_graph_stub_and_schema.ipynb` | Build a small supply chain graph and bridge it to the warehouse metadata |
| 04 | `04_agentic_workflow.ipynb` | Let an LLM agent answer a supplier-disruption question using the graph and the bridge |

---

## 0. What you need

| Need | Notes |
|---|---|
| A computer with a terminal | macOS, Linux, or Windows (use WSL2 or PowerShell; commands below are bash, Windows differences are noted) |
| Git | `git --version` |
| Python 3.11+ | `uv` can install it for you (step 1) |
| A Snowflake account | A [free trial](https://signup.snowflake.com/) works. It includes the `SNOWFLAKE_SAMPLE_DATA` database we use |
| A Neo4j database | Free [Aura](https://console.neo4j.io) instance **or** Neo4j Desktop / local server |
| An embeddings API key (optional) | e.g. OpenAI. Only needed for semantic (vector) search. Everything else works without it |

---

## 1. Set up the workspace and Python environment

### 1.1 Install `uv`

`uv` is the package manager and Python installer used throughout.

```sh
# macOS / Linux / WSL
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows PowerShell
# powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

uv --version
```

### 1.2 Clone this repo

```sh
git clone https://github.com/neo4j-field/graph-warehouse-semantic-workshop.git
cd graph-warehouse-semantic-workshop
```

You do **not** need to clone `neocarta` separately: `pyproject.toml` pins it to the exact version the labs were tested on and `uv` fetches it from GitHub. (If you want to read its source, connector READMEs or `examples/`, browse <https://github.com/neo4j-labs/neocarta> at the pinned commit, or see [Customizing for your environment](customizing_for_your_environment.md) to work from a local clone.)

### 1.3 Create the virtual environment and install

Dependencies (neocarta with the CLI, Snowflake and MCP extras, the agent stack, Jupyter, dev tools) are declared in `pyproject.toml`.

```sh
uv sync --extra dev                # creates .venv with Python >= 3.11 and installs everything
source .venv/bin/activate          # optional; `uv run <cmd>` works without it
```

Check it worked:

```sh
uv run neocarta --help
uv run neocarta snowflake schema --help
```

<details>
<summary>No <code>uv</code>? Plain pip fallback</summary>

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```
</details>

You do not need to activate the venv to run one-off commands: `uv run neocarta --help` works too.

---

## 2. Configure your environment file

```sh
cp .env.example .env
```

`.env` is gitignored. **Never commit it**: it will hold passwords and tokens. Open it in your editor and fill it in using sections 3 to 5 below. The values in the template (`xxxxxxxx`, `your-...`, `xy12345`) are placeholders.

The prerequisites notebook and `workshop-agent` read `.env` from the folder you run them in. The `neocarta` CLI and `neocarta-mcp` do **not**: they search for `.env` starting from neocarta's own installed package folder, so they never see this one. Tell uv to load it for every command in your shell session:

```sh
export UV_ENV_FILE=.env      # PowerShell: $env:UV_ENV_FILE=".env"
```

and run neocarta commands as `uv run neocarta ...` (or `uv run neocarta-mcp`) from this folder. Without that you'll see errors like `Missing required setting: --database`.

---

## 3. Neo4j: get your connection values

### Option A: Aura Free (recommended for a public workshop)

1. Sign in at <https://console.neo4j.io> and choose **Create instance** (Free).
2. **Download the credentials file or copy the password when prompted. It is shown only once.**
3. Wait until the instance status is **Running** (about a minute), then copy the **Connection URI**.

```bash
NEO4J_URI=neo4j+s://<dbid>.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<password from step 2>
NEO4J_DATABASE=neo4j          # Aura Free's database name is the instance id; use the value from the credentials file if different
```

### Option B: Neo4j Desktop / local server

Start the DBMS, then:

```bash
NEO4J_URI=neo4j://localhost:7687     # or bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<the password you set>
NEO4J_DATABASE=neo4j
```

**URI scheme cheat sheet** (a wrong scheme is the #1 connection error):

| Target | Scheme |
|---|---|
| Aura | `neo4j+s://` |
| Aura behind a TLS-inspecting corporate proxy | `neo4j+ssc://` |
| Local / self-hosted without TLS | `neo4j://` or `bolt://` |

---

## 4. Snowflake: find your values in the UI

All of these are in **Snowsight**, the Snowflake web UI. Open a SQL worksheet (**Projects > Worksheets > +**) to run the lookup queries below. Menu names move slightly between releases.

### 4.1 `SNOWFLAKE_ACCOUNT`

- **UI:** click your name (bottom-left) > **Account** > **View account details** > copy the **Account identifier**. It looks like `myorg-myaccount`.
- **SQL:**
  ```sql
  SELECT CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME();
  ```
- Both `<orgname>-<accountname>` and `<locator>.<region>` (e.g. `xy12345.us-east-1`) are accepted. Do **not** include `https://` or `.snowflakecomputing.com`.

### 4.2 `SNOWFLAKE_USER`

Your login name. Click your name (bottom-left): the username is shown under it. Or:

```sql
SELECT CURRENT_USER();
```

### 4.3 `SNOWFLAKE_ROLE`

The role neocarta will assume. Your current role is shown at the top of the worksheet (and under your name). Or:

```sql
SELECT CURRENT_ROLE();
SHOW GRANTS TO USER <your_user>;   -- roles you may use
```

- **Free trial:** your default is `ACCOUNTADMIN`. That works, but for a token we recommend a lower role such as `SYSADMIN` (`SNOWFLAKE_SAMPLE_DATA` is readable by all roles).
- **Your own data:** use a read-only role. Ingestion needs `USAGE` on the database and schema, and the ability to see the tables (metadata via `INFORMATION_SCHEMA` only shows objects the role has privileges on). Value sampling additionally needs `SELECT` (see 4.6).

### 4.4 `SNOWFLAKE_WAREHOUSE`

- **UI:** **Admin > Warehouses**. A trial account has `COMPUTE_WH`.
- **SQL:** `SHOW WAREHOUSES;`
- Your role needs `USAGE` on it. The smallest size (X-Small) is plenty: the metadata queries are tiny.

### 4.5 `SNOWFLAKE_DATABASE` and `SNOWFLAKE_SCHEMA`

| Scenario | Values |
|---|---|
| Public workshop | `SNOWFLAKE_SAMPLE_DATA` / `TPCH_SF1` |
| Your own data | `YOUR_DB` / `YOUR_SCHEMA` |

- Identifiers are resolved like Snowflake does: unquoted names are upper-cased, so `tpch_sf1` finds `TPCH_SF1`. For a mixed-case object created with double quotes, pass `'"MixedCase"'`.
- Browse them under **Data > Databases**, or `SHOW DATABASES; SHOW SCHEMAS IN DATABASE <db>;`
- **Missing `SNOWFLAKE_SAMPLE_DATA`?** (it can be absent on some accounts)
  ```sql
  CREATE DATABASE SNOWFLAKE_SAMPLE_DATA FROM SHARE SFC_SAMPLES.SAMPLE_DATA;
  ```

### 4.6 What neocarta reads, and why it matters

- **`REFERENCES` edges** (foreign-key joins in the graph) are created only from keys *declared* in Snowflake (primary / foreign key informational constraints). `TPCH_SF1` declares none, so expect **no `REFERENCES` edges** there. That is expected, not a bug. Many real schemas do declare them; check yours with `SHOW IMPORTED KEYS IN SCHEMA <db>.<schema>;`.
- **Value sampling** reads a few distinct example values per column, which needs `SELECT` on the tables. If your role cannot read table data (common in locked-down environments), run ingestion with `--value-sample-limit 0`: no table data is read at all.

### 4.7 Authentication: create a `SNOWFLAKE_TOKEN`

Snowflake blocks plain password logins from drivers on accounts with MFA enforced, and trials enforce it. The easiest workshop path is a **Programmatic Access Token (PAT)**.

> **The network policy catch.** Snowflake requires a *network policy* on the user before a PAT can be used. A fresh trial account has none, so the token is rejected with a network-policy error. The fix for a workshop is to create the token with a **temporary network-policy bypass**.

**In the UI:**

1. Click your name (bottom-left) > **Settings** > **Authentication**.
2. Under **Programmatic access tokens**, choose **Generate new token**.
3. Name it (e.g. `neocarta_workshop`).
4. Restrict it to a single role: choose the role from 4.3 (e.g. `SYSADMIN`).
5. Set the expiry to a few days.
6. Select the option to **temporarily bypass the network policy requirement**.
7. **Generate and copy the token immediately. It is shown only once.**

**Or in SQL** (equivalent, easier to script):

```sql
ALTER USER <your_user> ADD PROGRAMMATIC ACCESS TOKEN neocarta_workshop
  ROLE_RESTRICTION = 'SYSADMIN'
  DAYS_TO_EXPIRY = 7
  MINS_TO_BYPASS_NETWORK_POLICY_REQUIREMENT = 1440;   -- 24h bypass window
```

The token secret is returned in the result. Copy it now.

Put it in `.env`:

```bash
SNOWFLAKE_AUTHENTICATOR=PROGRAMMATIC_ACCESS_TOKEN
SNOWFLAKE_TOKEN=<token secret>
```

Notes:

- The bypass is **time-limited**. If the token stops working after the window, either regenerate it or have an admin attach a proper network policy to the user (the right answer for anything beyond a workshop).
- `SNOWFLAKE_ROLE` must be a role your token is allowed to use (the token's role restriction).

**Other auth options** (choose exactly one; neocarta's precedence is key-pair > authenticator > password):

| Method | `.env` | When |
|---|---|---|
| Password | `SNOWFLAKE_PASSWORD=...` (remove `SNOWFLAKE_AUTHENTICATOR` / `SNOWFLAKE_TOKEN`) | Accounts that allow programmatic password auth (no MFA) |
| Key-pair | `SNOWFLAKE_PRIVATE_KEY_PATH=/path/rsa_key.p8` (+ `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` if encrypted) | MFA-enforced accounts, production and service accounts |
| SSO browser | `SNOWFLAKE_AUTHENTICATOR=externalbrowser` | Enterprise SSO on a machine with a browser |

If you set both an authenticator and a password, the authenticator wins. Delete the one you don't want.

---

## 5. Optional: embeddings key

Embeddings add semantic (vector) search on table and column descriptions. Without them you still get the graph, catalog tools and full-text search.

```bash
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
```

Other providers work through LiteLLM (set that provider's key and model id). A key is needed both to generate embeddings and for the MCP server to embed search queries at runtime.

Can't reach OpenAI from your network? See [LLM Execution Environments & Fallbacks](#llm-execution-environments--fallbacks) for local Ollama and corporate-gateway options.

---

## LLM Execution Environments & Fallbacks

Neocarta routes embeddings through [LiteLLM](https://docs.litellm.ai/), so the provider is chosen by the model-id string plus provider environment variables in `.env`. `.env.example` has a block for each option below; enable **one**.

| Option | Use when |
|---|---|
| 1. Public API | You can reach `api.openai.com` (default) |
| 2. Ollama (local) | Public APIs are blocked, or you want an offline fallback |
| 3. Corporate gateway | Your org provides an OpenAI-compatible proxy |
| 3b. Gateway with custom headers | The gateway needs headers such as `Ocp-Apim-Subscription-Key` (e.g. Azure API Management) |

### Option 1b: Anthropic (Claude) for chat, Ollama for embeddings

Anthropic does not offer an embedding model, so use Claude for the agent and a local model for embeddings (start the Ollama container from Option 2 below, or skip chat models and pull only `nomic-embed-text`):

```bash
ANTHROPIC_API_KEY=your-anthropic-key
AGENT_MODEL=anthropic/claude-haiku-4-5
OLLAMA_API_BASE=http://localhost:11434
EMBEDDING_MODEL=ollama/nomic-embed-text
```

LiteLLM reads `ANTHROPIC_API_KEY` directly. Don't point `OPENAI_BASE_URL` at Anthropic, and note that `LLM_PROVIDER` and `EMBEDDING_BASE_URL` are not settings neocarta or LiteLLM read. Keep a single `EMBEDDING_MODEL` line in `.env`.

### Option 2: Local inference with Ollama

Recommended models: **Qwen 2.5 7B** for chat (it supports tool calling, which the agent needs) and **Nomic text embeddings** (small and fast). Qwen 2.5 7B wants roughly 8 GB of free RAM or VRAM; Nomic is well under 1 GB.

```sh
# Install Ollama from https://ollama.com/download, then:
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
ollama list                      # both models should appear
curl http://localhost:11434      # prints "Ollama is running"
```

**Or run it in Docker** (no local Ollama install; pulls both models into a volume):

```sh
docker compose -f docker/docker-compose.ollama.yml up -d
# NVIDIA GPU (needs the NVIDIA Container Toolkit): add the overlay
docker compose -f docker/docker-compose.ollama.yml -f docker/docker-compose.ollama.gpu.yml up -d
docker compose -f docker/docker-compose.ollama.yml logs -f ollama-pull   # wait for "success"
```

The first run downloads about 5 GB. Stop with `docker compose -f docker/docker-compose.ollama.yml down` (add `-v` to delete the models). Override models or port with `OLLAMA_CHAT_MODEL`, `OLLAMA_EMBED_MODEL`, `OLLAMA_PORT`.

In `.env`:

```bash
OLLAMA_API_BASE=http://localhost:11434
AGENT_MODEL=ollama/qwen2.5:7b
EMBEDDING_MODEL=ollama/nomic-embed-text
```

No API key is needed. Notes:

- `AGENT_MODEL` only affects the Text2SQL agent. The CLI and MCP server only use `EMBEDDING_MODEL`.
- Neocarta probes the embedding dimension on first use and sizes the vector index to match (Nomic is 768, OpenAI's small model 1536). Don't mix models: if you switch, re-run ingestion with embeddings (7.2) so the index is rebuilt consistently.
- Smaller local chat models call tools less reliably than hosted ones. If the agent misbehaves, retry with a larger tool-calling model.

### Option 3: Corporate gateway (standard OpenAI-compatible proxy)

```bash
OPENAI_BASE_URL=https://your-corporate-gateway.com/v1
OPENAI_API_KEY=your-internal-key
AGENT_MODEL=openai/your-internal-model-name
EMBEDDING_MODEL=openai/your-internal-embedding-model
```

The `openai/` prefix tells LiteLLM to speak the OpenAI protocol to whatever model name your gateway exposes.

### Option 3b: Gateway that requires custom HTTP headers

The `neocarta` CLI and MCP server do not expose a setting for extra headers, so environment variables alone can't do this for embeddings. The workshop agent (section 7.5) already reads `CORPORATE_GATEWAY_HEADERS` for its chat model, so only the embedding paths need a small local patch to a local `neocarta` checkout (see [Customizing for your environment](customizing_for_your_environment.md#working-from-a-local-neocarta-clone)). Put the headers in `.env`:

```bash
CORPORATE_GATEWAY_HEADERS='{"Ocp-Apim-Subscription-Key": "your-key", "X-Custom-Auth": "token"}'
```

Then give your AI coding assistant (Claude Code, Copilot CLI, etc.) this prompt. Start it from this repo's root; its `AGENTS.md` explains how to set up the local neocarta checkout first.

```plaintext
I am running the Neocarta workshop and need to route my LLM calls through a corporate API gateway that requires custom HTTP headers. Neocarta uses LiteLLM under the hood. 

Please review `neocarta/enrichment/embeddings/litellm_embeddings.py` and the MCP server setup code. Modify the instantiation of `LiteLLMEmbeddingsConnector` and the chat agent's `ChatLiteLLM` initialization to accept custom headers via `litellm_kwargs`. 

Specifically:
1. Read the environment variable `CORPORATE_GATEWAY_HEADERS` (expected as a JSON string) from `.env`.
2. Parse this JSON and inject it into the `extra_headers` or `headers` parameter within the `litellm_kwargs` dictionary passed to the embedding and chat clients.
3. Ensure the patch falls back gracefully if the variable is not present or invalid.
```

Where the assistant will need to look (all paths relative to your local `neocarta` checkout):

- `neocarta/_mcp/embeddings.py` (`create_embedder`, used by the MCP server)
- `neocarta/_cli/commands/_common.py` (builds the connector for CLI ingestion)
- `agent/agent.py` (`ChatLiteLLM`, only if you run neocarta's own BigQuery agent; the workshop agent in this repo needs no patch)

Once the checkout is installed editable (see the customization guide), the change takes effect immediately. Re-run `neocarta-mcp` or the CLI to test it, and don't commit the patch or your `.env`.

---

## 6. Verify everything: the prerequisites notebook

```sh
uv run jupyter lab 00_prerequisites_and_connectivity.ipynb
```

Run all cells. Every section prints ✅ or ❌ with a plain-English fix. It checks Python and packages, `.env` values and URI scheme, Neo4j login, Snowflake login, access to your target schema, and that the neocarta Snowflake connector can be constructed. **It writes nothing.**

Do not continue until the summary says you're ready.

---

## 7. Build the pipeline

> **Prefer a notebook?** `01_load_metadata_into_graph.ipynb` does 7.1 to 7.3 for you: it checks your embedding model, runs a dry run, ingests the metadata, verifies the graph and tries a semantic search. Open it with `uv run jupyter lab 01_load_metadata_into_graph.ipynb` after notebook 00 passes. The terminal commands below are the same steps.

### 7.1 Preview (no connections made)

```sh
uv run neocarta snowflake schema --dry-run
```

### 7.2 Ingest schema metadata into Neo4j

```sh
# Metadata only
uv run neocarta snowflake schema

# Locked-down role with no SELECT on tables: skip sample values
uv run neocarta snowflake schema --value-sample-limit 0

# With embeddings (needs OPENAI_API_KEY or another provider key)
uv run neocarta snowflake schema --embeddings
```

The values come from `.env`; any of them can be overridden with `--database` / `--schema`. Ingestion is **idempotent**: re-running updates rather than duplicates. One schema is ingested per run, so repeat the command for each schema you want.

> `SNOWFLAKE_VALUE_SAMPLE_LIMIT` in the template is read by the notebook only. For the CLI, use the `--value-sample-limit` flag.

Prefer Python? The same thing is in [`examples/snowflake_schema.py`](https://github.com/neo4j-labs/neocarta/blob/ba6bf79/examples/snowflake_schema.py), and the connector reference is the [Snowflake connector README](https://github.com/neo4j-labs/neocarta/blob/ba6bf79/neocarta/connectors/snowflake/README.md). Note that the example script uses password auth only; the CLI also supports tokens and key-pair.

### 7.3 Look at what you built

In Neo4j Browser (Aura: **Open > Query**) or the Query tool:

```cypher
// The shape of the semantic layer
MATCH (d:Database)-[:HAS_SCHEMA]->(s:Schema)-[:HAS_TABLE]->(t:Table)
RETURN d, s, t LIMIT 50;

// Columns of one table
MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)
WHERE toLower(t.name) = 'orders'
RETURN c.name, c.type, c.nullable, c.isPrimaryKey, c.isForeignKey;

// Join paths (only present if your Snowflake schema declares foreign keys)
MATCH (a:Column)-[:REFERENCES]->(b:Column)
RETURN a.id, b.id LIMIT 25;
```

Or query it from the shell with the same read-only tools your agent will use:

```sh
uv run neocarta tool list-schemas --json
uv run neocarta tool list-tables-by-schema --schema-name TPCH_SF1 --json
uv run neocarta tool get-context-by-table-full-text-search --text-content "customer orders" --json
# With embeddings:
uv run neocarta tool get-context-by-table-vector-search --text-content "customer orders" --max-tables 5 --json
```

### 7.4 Serve the graph to an agent (MCP)

```sh
uv run neocarta-mcp   # stdio MCP server; reads NEO4J_* / EMBEDDING_* from .env
```

To connect Claude Desktop (or any MCP client), add an entry like this. Point `command` at your venv so you use the install you just made:

```json
{
  "mcpServers": {
    "neocarta": {
      "command": "/path/to/graph-warehouse-semantic-workshop/.venv/bin/neocarta-mcp",
      "env": {
        "NEO4J_URI": "neo4j+s://<dbid>.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "<password>",
        "NEO4J_DATABASE": "neo4j",
        "OPENAI_API_KEY": "sk-...",
        "EMBEDDING_MODEL": "text-embedding-3-small"
      }
    }
  }
}
```

(Windows: `.venv\Scripts\neocarta-mcp.exe`.) The server registers the best retrieval tool your graph supports: hybrid if embeddings and full-text indexes exist, otherwise full-text or catalog tools.

The agent loop you've now enabled:

1. The user asks a business question.
2. The agent searches the graph for relevant tables and columns.
3. It follows `REFERENCES` edges to build correct joins.
4. It writes SQL and runs it against Snowflake with a query tool.

The graph supplies the *understanding* (what data exists, what it means, how it joins). A separate query tool executes the SQL.

### 7.5 Chat with a Snowflake agent

neocarta ships a Text2SQL agent (`agent/agent.py`, `run_agent.py`), but it is BigQuery-specific. This repo includes a Snowflake version in `workshop_agent/`, which runs from here.

```sh
uv run workshop-agent                                   # interactive chat
uv run workshop-agent "Which tables hold customer orders?"   # one question
uv run workshop-agent --debug "..."                     # full LiteLLM / MCP logging
```

What it does: starts `neocarta-mcp` (graph metadata tools), adds an `execute_sql` tool for Snowflake and read-only `execute_cypher` / `describe_graph_schema` tools for the supply chain graph, and runs a LangGraph agent on `AGENT_MODEL`. It reads the same `.env` (Snowflake auth, `AGENT_MODEL`, `OLLAMA_API_BASE`, `CORPORATE_GATEWAY_HEADERS`).

- **About `execute_sql`:** it is a small custom tool we wrote for convenience and simplicity (single read-only statement, `SELECT`/`WITH`/`SHOW`/`DESCRIBE`, results capped at `AGENT_ROW_LIMIT` rows, default 50). In production you would more likely use a **Snowflake-managed MCP server**, which gives more robust Snowflake support (governance, query handling, Cortex features). Also grant the agent's role only the access it needs; the keyword check is not a security boundary.
- **Model quality:** a 7B local model can follow the tool loop but is unreliable: it may skip the graph tools, guess table names or invent results. If answers look wrong, check the `🌿` tool-call lines, or use a hosted or larger tool-calling model via `AGENT_MODEL`.
- Embeddings for the MCP search tools must use the same `EMBEDDING_MODEL` you ingested with.

### 7.6 Add the business semantic layer

Module 01 loaded the *physical* layer (tables, columns, values). This step adds a *semantic* layer on top: business descriptions, synonyms, join relationships and metric definitions for the same tables. It is a hand-written [Open Semantic Interchange (OSI)](https://github.com/open-semantic-interchange/OSI) file, `datasets/tpch_semantic_model.yaml`, for the TPC-H sample data. No Snowflake access is needed for this step.

> **Prefer a notebook?** `02_load_semantic_layer.ipynb` does all of this and verifies the result. Run it after notebook 01 with `uv run jupyter lab 02_load_semantic_layer.ipynb`.

```sh
# Preview (no connections made)
UV_ENV_FILE=.env uv run neocarta osi ingest --spec-source datasets/tpch_semantic_model.yaml --dry-run

# Ingest (add --embeddings to embed the new nodes; use the same EMBEDDING_MODEL as 7.2)
UV_ENV_FILE=.env uv run neocarta osi ingest --spec-source datasets/tpch_semantic_model.yaml
```

What to expect:

- The semantic layer attaches to the **existing** `Table` and `Column` nodes (same node ids, because each dataset `source` is the 3-part name `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.<TABLE>`). They gain the labels `OsiTable` / `OsiColumn`; there are still 8 tables and 61 columns.
- Existing table and column names and descriptions are **kept**. The loader only sets properties when it creates a node, so the business meaning arrives as new linked nodes: `OsiSemanticModel`, `Metric` (with `Expression`), `Join`, `BusinessTerm`, and `REFERENCES` edges between columns. TPC-H declares no foreign keys, so these edges are what finally give the graph join paths.
- Re-running is idempotent.

```cypher
// Join paths supplied by the semantic layer
MATCH (a:Table)-[:HAS_COLUMN]->(ca:Column)-[:REFERENCES]->(cb:Column)<-[:HAS_COLUMN]-(b:Table)
RETURN a.name, ca.name, b.name, cb.name;

// Metric definitions
MATCH (m:Metric)-[:HAS_EXPRESSION]->(e:Expression)
RETURN m.name, m.description, e.expression;
```

---

### 7.7 Build the supply chain graph

Notebook `03_build_graph_stub_and_schema.ipynb` (run after 01 and 02) adds a small manufacturing graph (`FinishedGood` → `Assembly` → `Part` → `Supplier`) seeded with real TPC-H part and supplier keys, registers the graph's own schema as nodes (`GraphDatabase`, `GraphNodeSchema`, `GraphRelSchema`) and links those schema nodes to the `PART`, `PARTSUPP` and `SUPPLIER` tables and columns (`CORRELATES_TO`, `ENRICHED_BY`) and to business terms (`STANDARDIZES`). It ends by answering "which products does a supplier problem affect, and what stock exists?" by walking the graph and then running SQL built from the bridge. Run with `uv run jupyter lab 03_build_graph_stub_and_schema.ipynb`; it is idempotent.

### 7.8 Let an agent walk the golden thread

Notebook `04_agentic_workflow.ipynb` (run after 03) repeats the supplier-disruption question from 03, but an LLM agent answers it from one prompt: "Supplier#000000002 reports a delay: which finished goods are affected, and how much inventory do we hold of the affected parts?" The agent has to (1) traverse `Supplier <- Part <- FinishedGood` in Neo4j, (2) look up where *On-Hand Inventory* lives through the `ENRICHED_BY` bridge on the `Part` schema node (without being told `PARTSUPP` or `PS_AVAILQTY`), and (3) run the SQL against Snowflake.

```sh
uv run jupyter lab 04_agentic_workflow.ipynb
```

- **Read-only:** it writes nothing. Neo4j is queried in read transactions and Snowflake only accepts `SELECT`/`WITH`/`SHOW`/`DESCRIBE`.
- **Bring your own LLM:** the model is `AGENT_MODEL`, routed by LiteLLM (public API, Ollama or a gateway). The notebook ships with cleared outputs; the reference run used Claude Haiku 4.5.
- **Checks:** the notebook computes the expected answer itself, then checks the transcript, so a lucky guess of the TPC-H table names does not pass. Expect 3/3 on a capable hosted model. A small local model may fail the bridge check by writing Cypher with unnamed relationships; the tool-call lines (`🌿`) show where it went wrong.
- **Two readings of "inventory":** the notebook reports all stock of the affected parts (142,442) and the delayed supplier's own stock (26,012). The question asks for the former.
- **Tooling note:** the Neocarta MCP server only exposes catalog tools, so `workshop_agent/tools.py` adds `describe_graph_schema` and `execute_cypher`. In production, use the official Neo4j Cypher MCP server and a Snowflake-managed MCP server instead.

## 8. Going further (proof-of-value ideas)

- **Query history**: `neocarta snowflake logs` reads `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` into `Query` / `CTE` nodes linked to the tables and columns they touch, so the graph learns how your data is *really* used. Needs `IMPORTED PRIVILEGES` on the `SNOWFLAKE` database; the view can lag up to ~45 minutes.
- **Your own semantic layer**: copy `datasets/tpch_semantic_model.yaml`, describe your own tables, and load it with `neocarta osi ingest` (7.6). `neocarta osi export` writes a model back out of the graph as OSI YAML. For a business glossary, see the neocarta README (glossary connectors).
- **Your own schemas**: change `SNOWFLAKE_DATABASE` / `SNOWFLAKE_SCHEMA` and repeat 7.2.
- **Multiple sources**: other connectors (BigQuery, Databricks, JDBC, CSV) load into the same graph model, so one agent can route across databases.

---

## 9. Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| `Neo4j ... Unable to retrieve routing information` / `ServiceUnavailable` | Wrong URI scheme (see section 3 cheat sheet), instance paused or still starting, or VPN/proxy blocking port 7687 |
| `Neo4j ... Unauthorized` | Wrong password. Aura shows it only once; reset it in the console |
| Snowflake: `network policy ... is required` | PAT used without a network policy. Regenerate the token with the temporary bypass (4.7) or use password auth |
| Snowflake: `Incorrect username or password` / `Invalid access token` | Token expired, wrong user, or you pasted the token *name* instead of its secret |
| Snowflake: `Failed to connect ... account` | `SNOWFLAKE_ACCOUNT` has `https://` or `.snowflakecomputing.com`, or the wrong identifier format |
| Snowflake: `No active warehouse selected` | Set `SNOWFLAKE_WAREHOUSE` to one your role can `USE` |
| Notebook says no tables found | Wrong schema, wrong identifier case, or your role lacks `USAGE`/privileges on the database and schema |
| `SELECT` denied during ingest | Re-run with `--value-sample-limit 0` |
| No `REFERENCES` edges | Your schema declares no keys (expected for `TPCH_SF1`) |
| Vector search tools missing from the MCP server | Ingest was run without `--embeddings`, or no embedding key is set for the server |
| `neocarta: command not found` | Venv not active. Run `source .venv/bin/activate` or prefix with `uv run` |

---

## 10. Cleanup

```sql
-- Snowflake: revoke the token when you are done
ALTER USER <your_user> REMOVE PROGRAMMATIC ACCESS TOKEN neocarta_workshop;
```

```cypher
// Neo4j: wipe the graph (only on a throwaway workshop database!)
MATCH (n) DETACH DELETE n;
```

Delete `.env` when finished, or at least keep it out of version control and screenshots.
