from __future__ import annotations

from .config import KNOWLEDGE_DIR, KNOWLEDGE_ROUTES


def read_file(name: str) -> str:
    path = KNOWLEDGE_DIR / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def system_prompt() -> str:
    return read_file("SYSTEM.md")


def all_knowledge() -> str:
    parts = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        parts.append(f"\n\n# FILE {path.name}\n\n{path.read_text(encoding='utf-8')}")
    return "".join(parts)


def retrieve(query: str, subtest: str | None = None, budget_chars: int = 14000) -> str:
    names: list[str] = []
    if subtest and subtest in KNOWLEDGE_ROUTES:
        names.extend(KNOWLEDGE_ROUTES[subtest])
    q = (query or "").lower()
    mapping = [
        (("iam", "policy", "role", "s3", "ec2", "vpc basics", "security group"), "AWS_CORE.md"),
        (("route53", "load balancer", "elb", "alb", "nlb", "autoscal", "well-architected", "multi-az", "vpc peering"), "AWS_ARCHITECTURE.md"),
        (("hcl", "provider", "resource block", "variable", "output", "state file", "terraform init", "terraform plan"), "TERRAFORM_FUNDAMENTALS.md"),
        (("module", "workspace", "remote state", "drift", "import", "terraform cloud", "backend"), "TERRAFORM_ADVANCED.md"),
        (("pod", "deployment", "namespace", "configmap", "secret", "replicaset", "kubectl get"), "K8S_CORE.md"),
        (("ingress", "service mesh", "rbac", "helm", "pvc", "storageclass", "hpa", "network policy", "troubleshoot"), "K8S_OPERATIONS.md"),
        (("certification", "exam", "passing score", "study plan", "career"), "OVERVIEW.md"),
        (("track", "platform engineer", "cloud architect", "devops"), "DEVOPS_TRACKS.md"),
    ]
    for keys, fname in mapping:
        if any(k in q for k in keys) and fname not in names:
            names.append(fname)
    if not names:
        names = ["DEVOPS_TRACKS.md", "OVERVIEW.md"]
    if "OVERVIEW.md" not in names:
        names.append("OVERVIEW.md")
    chunks = []
    used = 0
    for name in names:
        text = read_file(name)
        if not text:
            continue
        piece = f"\n\n# FILE {name}\n\n{text}"
        if used + len(piece) > budget_chars:
            remain = budget_chars - used
            if remain > 400:
                chunks.append(piece[:remain])
            break
        chunks.append(piece)
        used += len(piece)
    return "".join(chunks)
