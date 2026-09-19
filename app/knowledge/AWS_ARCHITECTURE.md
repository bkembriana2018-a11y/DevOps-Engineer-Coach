# AWS Architecture & Networking

This is where the Solutions Architect exam actually lives: designing for availability, scale, and cost — not just knowing what a service does in isolation.

## VPC design in depth

A VPC spans a whole region and is carved into subnets, each pinned to one Availability Zone (AZ). Standard resilient design: at least two AZs, each with a public and a private subnet.

- **Public subnet**: route table has a `0.0.0.0/0 → Internet Gateway` route. Put load balancers and NAT Gateways here, not application servers, when you can avoid it.
- **Private subnet**: no direct route to an IGW. Application servers and databases typically live here, reaching the internet outbound (for patches, API calls) via a NAT Gateway in a public subnet.
- **NAT Gateway is AZ-scoped** — for true multi-AZ resilience you need one NAT Gateway per AZ, not one shared across the VPC (a single NAT Gateway is a single point of failure if its AZ goes down).
- **VPC Peering** connects two VPCs directly but is NOT transitive — if VPC A peers with B, and B peers with C, A cannot reach C through B. For many-VPC meshes, use a **Transit Gateway** instead.
- **VPC Endpoints** let resources reach AWS services (S3, DynamoDB, etc.) without traversing the public internet or needing a NAT Gateway — Gateway endpoints (free, S3/DynamoDB only) vs Interface endpoints (billed, PrivateLink-backed, most other services).

## Load balancing and scaling

- **Application Load Balancer (ALB)** — Layer 7, understands HTTP/HTTPS, routes by path/host, integrates with target groups (EC2, ECS, Lambda, IPs).
- **Network Load Balancer (NLB)** — Layer 4, ultra-low latency, static IP per AZ, used for extreme throughput or non-HTTP TCP/UDP traffic.
- Both are inherently multi-AZ when you enable multiple AZs on them; the ALB/NLB itself is a managed, highly available resource — you're not the one keeping it up.
- **Auto Scaling Groups** pair with a launch template and scaling policies. Target tracking (e.g., "keep average CPU at 50%") is the simplest and most commonly recommended policy type.
- **Route 53** is AWS's DNS service and also does health-check-based routing: failover, weighted, latency-based, and geolocation routing policies let you direct traffic across regions or endpoints without touching application code.

## Multi-AZ vs Multi-Region

- **Multi-AZ** protects against a data-center-level failure within one region — AZs are physically separate but low-latency-connected. This is the default resilience target for most workloads (e.g., RDS Multi-AZ keeps a synchronous standby in a second AZ).
- **Multi-Region** protects against a whole-region event and dramatically increases cost/complexity (data replication, DNS failover, sometimes duplicate infra). Only reach for it when the availability requirement genuinely demands it — it is not a default best practice, it's a deliberate, expensive tradeoff.

## The AWS Well-Architected Framework

Six pillars the exam expects you to recognize and apply to scenario questions:

1. **Operational Excellence** — run and monitor systems, improve processes continuously.
2. **Security** — protect data, systems, and assets (least privilege, defense in depth, encrypt in transit and at rest).
3. **Reliability** — recover from failure, scale to meet demand (this is where Multi-AZ, health checks, and auto-recovery live).
4. **Performance Efficiency** — use resources efficiently, keep up as technology and demand evolve.
5. **Cost Optimization** — avoid unnecessary spend (right-sizing, Reserved/Spot Instances, S3 lifecycle rules).
6. **Sustainability** — minimize environmental impact.

Scenario questions on the exam are often really asking "which pillar does this design violate?" — a design that's cheap but has a single point of failure violates Reliability; a design that's highly available but grants overly broad IAM permissions violates Security.

## Common exam traps

- Picking Multi-Region when the scenario only calls for Multi-AZ (over-engineering, and it's usually the "wrong but tempting" answer).
- Forgetting a NAT Gateway costs money per hour AND per GB processed — at high traffic, NAT Gateway costs can dwarf compute costs, which is why VPC Endpoints exist.
- Treating VPC Peering as transitive.
- Choosing an ALB when the scenario needs raw TCP/UDP throughput (should be NLB) or vice versa.
