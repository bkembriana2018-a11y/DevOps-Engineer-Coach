# Tracks: how this app prioritizes your studying

Your "goal" on the dashboard doesn't unlock or hide anything — every topic is always available. It just changes which weak spots the "What to do next" list surfaces first.

## Full-stack DevOps (default)

Balanced across AWS, Terraform, and Kubernetes. Good default if you're early in your career or the job you want is a generalist "DevOps Engineer" role that touches all three roughly equally. Priority order: AWS Core → Terraform Fundamentals → Kubernetes Core → AWS Architecture → Terraform Modules & Workflows → Kubernetes Operations.

## Platform Engineer

Weights Kubernetes and Terraform higher than AWS. This matches roles titled "Platform Engineer" or "Infrastructure Engineer" where the job is building the internal platform other engineers deploy onto — usually Kubernetes-centric with Terraform as the provisioning layer, and cloud-provider specifics are a smaller (but still real) slice. Priority order: Kubernetes Core → Terraform Fundamentals → Kubernetes Operations → Terraform Modules & Workflows → AWS Core → AWS Architecture.

## Cloud Architect

Weights AWS higher — architecture patterns, networking, and the well-architected framework — while still expecting Terraform for provisioning and baseline Kubernetes literacy. Matches "Cloud Architect" or "Solutions Architect" roles where the deliverable is often a design document and a Terraform module, not necessarily day-to-day cluster operations. Priority order: AWS Core → AWS Architecture → Terraform Fundamentals → Kubernetes Core → Terraform Modules & Workflows → Kubernetes Operations.

## A practical note on breadth vs. depth

Real job postings for any of these titles are inconsistent — a "Platform Engineer" job at one company is a "DevOps Engineer" job at another with nearly the same responsibilities. Don't over-index on picking the "correct" track. All three domains show up in most infrastructure interviews at some point; use the track setting to decide where you drill first, not to decide what you can skip entirely.
