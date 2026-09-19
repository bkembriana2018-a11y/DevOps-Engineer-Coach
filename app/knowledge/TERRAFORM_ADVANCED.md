# Terraform Modules & Workflows

Once the fundamentals click, the Terraform Associate exam (and real jobs) shift focus to reuse, collaboration, and safely operating on shared state.

## Modules

A **module** is just a directory of `.tf` files. Every Terraform configuration is technically a module (the "root module"); a **child module** is one you call from elsewhere:

```hcl
module "vpc" {
  source = "./modules/vpc"
  cidr_block = "10.0.0.0/16"
}
```

`source` can be a local path, a Git URL, or a Terraform Registry reference like `terraform-aws-modules/vpc/aws`. Modules take **input variables** and expose **outputs**, exactly like the root module does — that's the whole reuse mechanism. Well-designed modules are opinionated but configurable: sensible defaults, but nothing hardcoded that should vary between environments.

## Workspaces

`terraform workspace` lets one configuration manage multiple, isolated instances of state (e.g., `dev`, `staging`, `prod`) without duplicating the `.tf` files:

```bash
terraform workspace new staging
terraform workspace select staging
terraform apply
```

Important nuance: workspaces share the same backend and configuration — they isolate *state*, not code. For environments that differ significantly (not just variable values but actual resource shape), separate root modules/directories per environment are usually the more maintainable answer than workspaces. Workspaces work best when environments are structurally identical and only differ by input values.

## Remote state and locking

Remote backends (S3+DynamoDB, Terraform Cloud, etc.) solve two problems: sharing state across a team, and locking it so two `apply` runs can't race each other and corrupt it. Reading another configuration's remote state (read-only) is done with a `terraform_remote_state` data source — a common way to pass a VPC ID from a "networking" root module into an "app" root module without hardcoding it.

## Drift and `terraform import`

**Drift** is when real infrastructure no longer matches state — someone changed something in the console, or an out-of-band process modified a resource. `terraform plan` surfaces drift by refreshing state and diffing against config. `terraform apply` will then try to reconcile it back to what the config says — which is why manual console changes to Terraform-managed resources are a common source of "surprise" applies.

`terraform import` brings an existing, unmanaged resource under Terraform's management by associating it with a resource block you've already written:

```bash
terraform import aws_s3_bucket.legacy my-existing-bucket-name
```

Import only writes state — you still have to write the matching `.tf` config yourself (or use tools like `terraform plan -generate-config-out` in newer versions to scaffold it).

## `terraform fmt`, `validate`, and `taint`

- `terraform fmt` — rewrites files to canonical style. Run it before every commit; CI often checks it.
- `terraform validate` — checks syntax and internal consistency without touching any backend or provider.
- `terraform taint` (older versions) / `terraform apply -replace=<address>` (current) — forces a specific resource to be destroyed and recreated on the next apply, useful when a resource is broken in a way Terraform itself won't detect (e.g., corrupted instance).

## Common exam/interview traps

- Thinking workspaces are a full substitute for separate environment directories when environments genuinely diverge in structure.
- Forgetting `terraform import` doesn't generate configuration for you (in most versions) — only state.
- Not locking remote state, leading to two engineers applying concurrently and corrupting it.
- Committing `.tfstate` (or a `.tfvars` file with secrets) to git.
