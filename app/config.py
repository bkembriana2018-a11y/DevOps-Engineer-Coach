import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = APP_DIR / "knowledge"
QUESTIONS_PATH = APP_DIR / "questions" / "bank.json"
WEB_DIR = ROOT / "web"
DATA_DIR = ROOT / "data"
PROGRESS_PATH = DATA_DIR / "progress.json"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = "llama3.1"

# "Subtests" here are study topics, each backed by its own knowledge file and
# question-bank slice. items/minutes/pace describe this app's own drill
# length -- not an official exam's timing.
SUBTESTS = {
    "aws_core": {"label": "AWS Core Services", "code": "AWS-C", "items": 20, "minutes": 30, "pace": 90},
    "aws_architecture": {"label": "AWS Architecture & Networking", "code": "AWS-A", "items": 20, "minutes": 30, "pace": 90},
    "terraform_fundamentals": {"label": "Terraform Fundamentals", "code": "TF-F", "items": 20, "minutes": 25, "pace": 75},
    "terraform_advanced": {"label": "Terraform Modules & Workflows", "code": "TF-A", "items": 20, "minutes": 25, "pace": 75},
    "k8s_core": {"label": "Kubernetes Core Objects", "code": "K8S-C", "items": 20, "minutes": 30, "pace": 90},
    "k8s_operations": {"label": "Kubernetes Operations", "code": "K8S-O", "items": 20, "minutes": 30, "pace": 90},
}

COMPOSITES = {
    "aws": ["aws_core", "aws_architecture"],
    "terraform": ["terraform_fundamentals", "terraform_advanced"],
    "kubernetes": ["k8s_core", "k8s_operations"],
    "cloud_native": [
        "aws_core",
        "aws_architecture",
        "terraform_fundamentals",
        "terraform_advanced",
        "k8s_core",
        "k8s_operations",
    ],
}

TRACK_FOCUS = {
    "full_stack_devops": ["aws", "terraform", "kubernetes"],
    "platform_engineer": ["kubernetes", "terraform", "aws"],
    "cloud_architect": ["aws", "terraform", "kubernetes"],
}

TRACK_SUBTEST_PRIORITY = {
    "full_stack_devops": [
        "aws_core", "terraform_fundamentals", "k8s_core",
        "aws_architecture", "terraform_advanced", "k8s_operations",
    ],
    "platform_engineer": [
        "k8s_core", "terraform_fundamentals", "k8s_operations",
        "terraform_advanced", "aws_core", "aws_architecture",
    ],
    "cloud_architect": [
        "aws_core", "aws_architecture", "terraform_fundamentals",
        "k8s_core", "terraform_advanced", "k8s_operations",
    ],
}

# These are the certifying bodies' commonly published passing bars, expressed
# as an approximate percent-correct for this app's practice grading -- real
# exams use scaled scoring (AWS, Terraform) or proctored hands-on tasks (CKA),
# not a raw percentage. Treat as a study bar, not a score predictor.
FLOORS = {"aws": 72, "terraform": 70, "kubernetes": 66, "cloud_native": None}
COMPETITIVE = {"aws": 85, "terraform": 85, "kubernetes": 80, "cloud_native": 80}

DEFAULT_TRACK = "full_stack_devops"

KNOWLEDGE_ROUTES = {
    "aws_core": ["AWS_CORE.md"],
    "aws_architecture": ["AWS_ARCHITECTURE.md", "AWS_CORE.md"],
    "terraform_fundamentals": ["TERRAFORM_FUNDAMENTALS.md"],
    "terraform_advanced": ["TERRAFORM_ADVANCED.md", "TERRAFORM_FUNDAMENTALS.md"],
    "k8s_core": ["K8S_CORE.md"],
    "k8s_operations": ["K8S_OPERATIONS.md", "K8S_CORE.md"],
    "overview": ["OVERVIEW.md", "DEVOPS_TRACKS.md"],
    "aws": ["AWS_CORE.md", "AWS_ARCHITECTURE.md"],
    "terraform": ["TERRAFORM_FUNDAMENTALS.md", "TERRAFORM_ADVANCED.md"],
    "kubernetes": ["K8S_CORE.md", "K8S_OPERATIONS.md"],
    "full_stack_devops": ["DEVOPS_TRACKS.md", "OVERVIEW.md"],
    "platform_engineer": ["DEVOPS_TRACKS.md", "K8S_CORE.md", "TERRAFORM_FUNDAMENTALS.md"],
    "cloud_architect": ["DEVOPS_TRACKS.md", "AWS_CORE.md", "AWS_ARCHITECTURE.md"],
}
