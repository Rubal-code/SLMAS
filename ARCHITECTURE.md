SLMAS - Self-Learning AI Agent Architecture
=========================================

Last updated: 2026-09-04

Purpose
-------
This document describes the recommended architecture for a self-learning AI agent to be developed inside this repository. It covers: a high-level overview, components and responsibilities, dataflows and schemas, runtime sequences, learning loop, safety/governance, MVP vs production technology choices, deployment considerations, and next steps with an implementation checklist.

High-level goal
---------------
Build an agent that: accepts tasks, plans multi-step actions, executes via tools, logs outcomes, stores experiences in memory, and adapts behavior over time via retrieval and periodic learning updates.

Key design principles
---------------------
- Start with an MVP that is safe, auditable, and easy to run locally.
- Use retrieval-augmented generation (RAG) and example accumulation instead of online continuous fine-tuning.
- Keep model access isolated behind an adapter/service to allow provider swaps.
- Maintain an immutable audit trail for all external actions and learning artifacts.
- Gate all destructive or high-risk actions behind approval flows.

1. Logical component diagram
----------------------------
Client (UI/CLI) --> API Gateway --> Agent API (FastAPI)
Agent API --> Planner/Orchestrator --> Executor / Tool Adapter(s)
Planner <--> Memory & Retrieval (Vector DB + SQL)
Executor --> Tools (search, DB, shell, HTTP, code-runner)
Executor --> Observability -> Logs / Metrics
Executor --> Evaluator -> Experiences DB
Experiences DB -> Learning Pipeline -> (prompt/template updates or fine-tune dataset)
Admin UI -> Approve / Review -> Trigger model or prompt rollout

ASCII overview
--------------
Client -> /tasks -> FastAPI
FastAPI -> Planner (LLM + RAG)
Planner -> Plan saved to Postgres/SQLite
Executor runs steps -> Tool Adapters
Tool results + outcomes -> Experiences (Postgres) + Embeddings (Vector DB)
Background job: collect golden examples -> snapshot prompt templates or export fine-tune JSONL
Human review -> approve rollout -> update prompt_templates or trigger offline fine-tune

2. Components & responsibilities
--------------------------------
- API / Interface (FastAPI)
  - Endpoints: submit task, get status, submit feedback, admin triggers
  - Authentication, request validation, rate limiting

- Planner / Orchestrator
  - Decompose goals into steps using the LLM and retrieved similar plans
  - Create a plan (task graph) and manage step state
  - Retry policies and escalation rules

- Executor / Tool Adapter
  - Unified adapter interface for external capabilities (search, DB, HTTP, shell, repo)
  - Wraps each call with observability, permission checks, and input/output sanitation
  - Mark tools as `safe` or `destructive`; destructive tools require approval

- Model Service (LLM adapter)
  - Abstracts model provider (OpenAI-compatible or local model)
  - Handles prompt templating, RAG insertion, and caching of responses where applicable

- Memory & Retrieval
  - Short-term: session store (Redis) for current plan/step state
  - Long-term: Vector DB (Qdrant / Qdrant Docker for MVP) storing embeddings of interactions, plans, docs
  - Structured DB (Postgres or SQLite for MVP) storing interactions, plans, experiences, prompt templates

- Experiences DB
  - Records each action: inputs, outputs, tool, timestamps, success flag, evaluator score, user feedback
  - Links to vector DB entry ids

- Evaluator / Rewarder
  - Generates automatic signals (success/fail, heuristics) plus ingest user feedback
  - Stores scores and derives simple rewards used by the learning pipeline

- Learning Pipeline
  - Periodic batch job to collect high-quality examples and summarize failure patterns
  - Generates: prompt template updates, dataset snapshots (JSONL) for offline fine-tune, suggested rule updates
  - Requires human approval before production rollout

- Safety & Governance
  - Policy engine to block forbidden actions, redact PII, and gate high-risk tools
  - Audit logs for all external actions
  - Human-in-the-loop for approvals

- Observability & Ops
  - Structured logs, metrics (task success rate, latency, cost), error tracking (Sentry)
  - Experiment tracking for prompt/model variants (Langfuse or W&B)

3. Data model (MVP minimal schemas)
-----------------------------------
(Examples use SQL-style fields — implement in Postgres or SQLite.)

Table: plans
- id (uuid)
- goal_text (text)
- steps (json) -- list of step objects {id, action, status, metadata}
- status (text) -- pending/running/succeeded/failed
- created_at (timestamp)
- finished_at (timestamp nullable)

Table: interactions
- id (uuid)
- plan_id (uuid)
- session_id (text)
- user_id (text nullable)
- input_text (text)
- created_at (timestamp)

Table: experiences
- id (uuid)
- interaction_id (uuid nullable)
- action (json) -- the executed action and inputs
- tool (text)
- result (json)
- success (bool)
- score (float nullable)
- user_feedback (text nullable)
- embedding_id (text nullable) -- id in vector DB
- created_at (timestamp)

Table: prompt_templates
- id (uuid)
- name (text)
- template_text (text)
- version (int)
- created_at (timestamp)

Vector DB entries (Qdrant/Milvus/Pinecone style metadata)
- id
- vector
- metadata: {experience_id, text, tags, created_at}

4. Runtime sequence (example)
------------------------------
1. Client POST /tasks {goal_text}
2. FastAPI authenticates and creates a plan record.
3. Planner asks LLM to decompose goal; includes retrieved similar plans (via vector DB) in context.
4. Planner stores plan steps and returns task id.
5. Worker picks up pending plan step, Executor calls the designated Tool Adapter.
6. Tool Adapter runs action (e.g., fetch data, call API) and returns result.
7. Observers log inputs/outputs, Evaluator computes automatic score (success heuristics) and writes an experiences row.
8. If step succeeded, mark step completed and continue; else retry with additional context or escalate for human review.
9. After plan finishes, experiences are eligible for the Learning Pipeline.

5. Learning loop (MVP)
----------------------
- Pattern: batch, offline, human-reviewed updates.
- On a scheduled job (daily/weekly) the pipeline:
  - Selects experiences with high success and high score
  - Exports them as "golden examples" (input, plan, action, result)
  - Summarizes recurrent failures into rule-suggestions
  - Generates candidate prompt-template updates or a fine-tuning JSONL
  - Pushes candidate changes to staging for A/B test
  - Requires admin approval before production promotion

6. Safety & governance
----------------------
- All destructive-capability tools flagged as `destructive` and require explicit approval via Admin UI before first use.
- PII detection and redaction on stored experiences and exported datasets.
- Immutable audit logs: never delete raw interaction logs; apply retention policy to derived artifacts.
- Rate limit and cost guards on LLM calls; abort plans that exceed cost budgets without explicit override.
- Human-in-the-loop approvals and rollback capability for model/prompt rollouts.

7. Tech stack recommendations
-----------------------------
MVP (local-friendly, cheap to run):
- Backend: Python 3.11+ + FastAPI
- LLM adapter: OpenAI-compatible (environment variable for key) or a local Llama2 wrapper
- Vector DB: Qdrant (Docker) or SQLite-backed fallback with local embedding store (tiny-embeddings) for dev
- Structured DB: SQLite for MVP; Postgres for production
- Cache/session: Redis (optional) or simple in-memory session for MVP
- Background workers: Celery (with Redis broker) or RQ
- Container: Docker Compose for local dev
- Observability: stdout structured logs + Sentry optional

Production (scalable):
- Kubernetes (EKS/GKE/AKS)
- Model endpoints: managed LLM provider or dedicated inference cluster (Triton, Ray Serve)
- Vector DB: Pinecone or managed Weaviate
- DB: Postgres with replicas
- Message bus: Kafka for events
- Workflow: Temporal or Argo Workflows
- Secrets: HashiCorp Vault / cloud KMS
- Monitoring: Prometheus/Grafana; Langfuse for prompt experiment tracking

8. Minimal MVP scope for this repo
----------------------------------
- FastAPI server with endpoints: POST /tasks, GET /tasks/{id}, POST /feedback/{experience_id}
- Planner (LLM adapter) that uses RAG: retrieve similar plans and call LLM to decompose goal
- Executor with two sample tool adapters: `mock_search` and `mock_db` (safe by default)
- Persistence: SQLite (file) for plans, interactions, experiences; vector store: local Qdrant via Docker or fallback
- Background job: evaluate experiences and export golden examples to data/golden_examples.jsonl
- Admin static UI: list experiences, approve candidate prompt/template updates
- Safety hook: destructive tools disabled by default in config

9. Project layout (recommended files to add)
-------------------------------------------
- app/
  - main.py (FastAPI entry)
  - api/
    - tasks.py
    - admin.py
  - agent/
    - planner.py
    - executor.py
    - model_adapter.py
    - tools/
      - mock_search.py
      - mock_db.py
  - storage/
    - db.py (SQLAlchemy or sqlite helper)
    - vector_store.py (Qdrant adapter or fallback)
  - workers/
    - evaluator.py
    - learning_job.py
  - config.py
- data/
  - golden_examples.jsonl
- infra/
  - docker-compose.yml (qdrant, redis)
- tests/
  - test_planner.py
- README.md (run instructions)

10. Running the MVP locally (default choices)
--------------------------------------------
Defaults in this repo scaffolding will be:
- SQLite for structured persistence: file at ./data/agent.sqlite
- Local Qdrant in Docker (docker-compose in infra/) or a simple embedding fallback when Qdrant is not available
- LLM adapter: OpenAI-compatible (env OPENAI_API_KEY) or stub responses when no key is set

Quick dev steps (to be added to README when scaffolded):
1. Install Python 3.11+ and dependencies (pip install -r requirements.txt)
2. Start dev infra: docker-compose -f infra/docker-compose.yml up -d  (qdrant, redis)
3. Start FastAPI: uvicorn app.main:app --reload
4. Submit a task: POST http://localhost:8000/tasks {"goal_text":"Summarize latest support tickets"}
5. Observe plan execution in /tasks/{id}
6. Run background evaluator: python -m app.workers.evaluator

11. Security & privacy checklist (MVP)
-------------------------------------
- Do not log secrets or full PII in plaintext. Redact before storage when detected.
- Use environment variables for API keys.
- Enforce access control on admin endpoints.
- Maintain an audit trail and data retention policy.

12. Next steps / Implementation checklist (short)
------------------------------------------------
- [ ] Create a Git branch: feature/agent-mvp
- [ ] Scaffold files and modules listed in Project layout
- [ ] Implement model adapter and planner skeleton
- [ ] Implement storage adapters (SQLite + Qdrant fallback)
- [ ] Implement two mock tools (mock_search, mock_db)
- [ ] Implement background evaluator + learning_job export
- [ ] Add infra/docker-compose for Qdrant + Redis
- [ ] Add simple Admin UI page and approval flow
- [ ] Write README with run instructions and environment variables

13. Decisions for this project (defaults)
-----------------------------------------
- Persistence: SQLite (local) — change to Postgres for production
- Vector DB: Qdrant Docker for local dev; Pinecone/Weaviate for production
- LLM: OpenAI-compatible adapter (env var for key) with pluggable interface for local models

14. Contacts & governance
-------------------------
- All model or prompt changes must be reviewed by repository maintainers before production use.
- Keep a changelog for prompt_template updates and learning run outputs (data/golden_examples.jsonl snapshots).

Appendix A: Small example prompt-template (RAG)
---------------------------------------------
Template name: plan-decomposition-v1

You are an agent that decomposes user goals into an ordered list of actionable steps. Use the context below: similar past plans and recent step history.

Context:
{retrieved_examples}

Goal:
{goal_text}

Output format (JSON):
[{"id": "step-1", "action": "...", "tool": "mock_search", "metadata": {}}, ...]

Appendix B: Where this file lives
---------------------------------
- Project root: D:/SLMAS
- This file: D:/SLMAS/ARCHITECTURE.md

---

If you want, the next action is to scaffold the MVP files described above. Confirm whether to proceed with the scaffold and whether to keep defaults (SQLite + local Qdrant + OpenAI-compatible LLM adapter) or change them now.