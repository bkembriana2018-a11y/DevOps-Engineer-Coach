# AWS Core Services

The services that show up in almost every AWS question and almost every real architecture: IAM, EC2, S3, and VPC basics.

## IAM (Identity and Access Management)

IAM is global, not regional. Core objects:

- **Users** — a person or service with long-term credentials. Avoid long-term access keys where possible; prefer roles.
- **Groups** — a way to attach policies to a set of users at once. Groups cannot be nested.
- **Roles** — an identity that anything can assume temporarily (an EC2 instance, a Lambda function, a user from another account). Roles issue short-lived credentials via STS. This is the AWS-recommended way to give an EC2 instance or Lambda permissions — never bake an access key into an AMI or function code.
- **Policies** — JSON documents that grant or deny permissions. A minimal policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": ["arn:aws:s3:::my-bucket", "arn:aws:s3:::my-bucket/*"]
    }
  ]
}
```

Key exam gotcha: an explicit `Deny` always wins over an `Allow`, no matter which policy it's in or how many `Allow`s exist elsewhere. By default, everything is denied unless explicitly allowed.

**Principle of least privilege**: grant only what's needed. IAM Access Analyzer and the policy simulator exist specifically to catch over-broad grants.

## EC2 (Elastic Compute Cloud)

Virtual machines ("instances") launched from an AMI (Amazon Machine Image). Key knobs:

- **Instance types** are named `family.size` (e.g. `t3.micro`, `m5.large`, `c6g.xlarge`). The letter families roughly mean: `t` = burstable/general low-cost, `m` = general purpose, `c` = compute-optimized, `r` = memory-optimized, `g`/`p` = GPU.
- **Security groups** are stateful virtual firewalls attached to instances/ENIs — if you allow inbound traffic on a port, the matching outbound response is automatically allowed. They only support `Allow` rules, never `Deny`.
- **EBS** (Elastic Block Store) is the durable, network-attached disk an EC2 instance boots from and can attach more of. It persists independently of the instance's lifecycle (unless "delete on termination" is set).
- **Instance store** is directly-attached, ephemeral disk — faster, but gone the moment the instance stops or terminates. Never put anything there you can't afford to lose.
- **Auto Scaling Groups (ASG)** keep a target number of instances running, replacing unhealthy ones and scaling in/out based on policies (target tracking, step scaling, or scheduled).

## S3 (Simple Storage Service)

Object storage, not a filesystem. Objects live in buckets; bucket names are globally unique across all of AWS.

- **Storage classes** trade retrieval speed/cost for storage cost: Standard → Standard-IA → One Zone-IA → Glacier Instant Retrieval → Glacier Flexible Retrieval → Glacier Deep Archive. Lifecycle rules can automatically transition objects between classes as they age.
- **Versioning** keeps every version of an object once enabled — it cannot be fully disabled again, only suspended. This is how you protect against accidental overwrite/delete (paired with MFA Delete for extra protection).
- **Bucket policies** (resource-based) vs **IAM policies** (identity-based) can both grant S3 access — when they conflict, the same explicit-deny-wins rule from IAM applies across the union of all applicable policies.
- S3 is regional but has a global namespace and effectively unlimited scale — there's no need to "shard" a bucket for scale the way you might a database.

## VPC basics (deep dive is in AWS Architecture)

A **VPC** (Virtual Private Cloud) is your isolated network inside a region. Minimum vocabulary:

- **Subnet** — a slice of the VPC's IP range, tied to one Availability Zone. "Public" just means its route table sends `0.0.0.0/0` to an Internet Gateway; there's no separate "public subnet" resource type.
- **Route table** — controls where traffic from a subnet goes.
- **Internet Gateway (IGW)** — attached to the VPC, lets public subnets reach the internet.
- **NAT Gateway** — sits in a public subnet, lets private-subnet resources initiate outbound internet traffic without being reachable from it.

## Common exam traps

- Confusing security groups (stateful, instance-level, allow-only) with Network ACLs (stateless, subnet-level, allow AND deny, rules evaluated in number order).
- Assuming S3 is regionally replicated by default — it isn't, unless you set up Cross-Region Replication.
- Forgetting that IAM is global while almost everything else (VPC, EC2, most S3 operations) is regional.
