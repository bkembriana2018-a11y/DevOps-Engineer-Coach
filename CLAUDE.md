# Cloud Coach — Claude Code project notes

Local FastAPI + static UI study app for AWS, Terraform, and Kubernetes. Sibling app to `afoqt-coach-ai`, same architecture, different domain and port.

## Run

```bash
chmod +x run.sh
./run.sh
```

App: http://127.0.0.1:8766
Health: http://127.0.0.1:8766/api/health
Ollama (optional, shared with any other local app): http://127.0.0.1:11434

## Layout

- `app/main.py` — FastAPI
- `app/config.py` — the whole domain model: topics ("subtests"), composites (aws/terraform/kubernetes/cloud_native), tracks
- `app/knowledge/` — LLM grounding corpus. `SYSTEM.md` is the tutor contract.
- `app/questions/bank_*.json` — original practice items only. Never add real exam questions from any certifying body.
- `web/` — dashboard (same structure as afoqt-coach-ai, different color palette: teal/blue instead of rose)
- `data/progress.json` — created at runtime. Local only.

## Guardrails

- Never claim a practice question appeared on a real AWS/Terraform/CKA exam.
- Practice percent is not a scaled exam score — AWS and Terraform exams use scaled scoring, and CKA is graded on hands-on tasks, not multiple choice.
- Confirm current exam blueprints and passing scores against the certifying body (aws.amazon.com/certification, developer.hashicorp.com, kubernetes.io/training) rather than treating this app's numbers as permanent.
- Prefer installing with Homebrew + a project `.venv`. Do not use system Python packages if a venv works.
- Port 8766, not 8765 — reserved so this can run alongside afoqt-coach-ai without conflict.
