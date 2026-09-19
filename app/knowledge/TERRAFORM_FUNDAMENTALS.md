# Terraform Fundamentals

Terraform is HashiCorp's infrastructure-as-code tool: you declare the desired end state in HCL (HashiCorp Configuration Language), and Terraform figures out what API calls turn the current state into that end state.

## The core workflow

```bash
terraform init      # downloads providers, sets up the backend
terraform plan       # shows what WOULD change, makes no changes
terraform apply      # makes the changes (prompts for confirmation)
terraform destroy    # tears down everything Terraform manages here
```

`init` must be re-run any time you add/change a provider or backend config. `plan` is safe to run as often as you want — it's read-only against real infrastructure (it does talk to the provider APIs to refresh state, but makes no changes).

## Providers, resources, and data sources

A **provider** is a plugin that knows how to talk to an API (AWS, Kubernetes, GitHub, etc.):

```hcl
provider "aws" {
  region = "us-east-1"
}
```

A **resource** block declares something Terraform should create and manage:

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0123456789abcdef0"
  instance_type = "t3.micro"
  tags = {
    Name = "web-server"
  }
}
```

A **data source** reads existing information without managing it:

```hcl
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}
```

Reference a resource or data source elsewhere as `<type>.<name>.<attribute>`, e.g. `aws_instance.web.id` or `data.aws_ami.amazon_linux.id`.

## Variables and outputs

```hcl
variable "instance_type" {
  type    = string
  default = "t3.micro"
}

output "instance_ip" {
  value = aws_instance.web.public_ip
}
```

Variables can be set via `-var`, a `.tfvars` file, environment variables (`TF_VAR_instance_type`), or the default. Precedence, highest to lowest: command-line `-var`/`-var-file` > `*.auto.tfvars` > `terraform.tfvars` > environment variables > default in the variable block.

## State

Terraform tracks everything it manages in a **state file** (`terraform.tfstate`), a JSON mapping of your config to real resource IDs. This is how it knows what to change on the next apply and how to destroy things later. State can contain secrets (e.g., a generated DB password) in plain text — never commit it to source control.

- **Local state** (the default) lives on disk — fine for solo experiments, dangerous for teams (no locking, easy to lose).
- **Remote state** (S3 + DynamoDB for locking, Terraform Cloud, etc.) is the real answer for any team or production use — it's shared, versioned, and lockable so two people can't apply at once.

## The dependency graph

Terraform builds a DAG (directed acyclic graph) from your resource references and applies in the correct order automatically — you generally don't need to declare order explicitly. When there's no implicit reference but an order still matters, use `depends_on`:

```hcl
resource "aws_s3_bucket" "logs" {
  # ...
  depends_on = [aws_iam_role_policy.log_writer]
}
```

## Common exam/interview traps

- Confusing `plan` (dry run) with `apply` (actually makes changes) — a surprising number of incident post-mortems are "someone ran apply thinking it was plan."
- Forgetting that `terraform destroy` on a misconfigured working directory can delete real production resources — always check `terraform plan -destroy` or your target scope first.
- Hardcoding values that should be variables, making the module unreusable.
- Not understanding that HCL is declarative — you describe the end state, you don't write imperative steps.
