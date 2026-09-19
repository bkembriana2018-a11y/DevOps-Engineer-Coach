# Kubernetes Operations

Running Kubernetes day-to-day: getting traffic in, storage attached, access controlled, and broken things debugged. This is the heart of CKA-style content — mostly hands-on, not conceptual trivia.

## Ingress

A **Service** of type LoadBalancer gets expensive fast if you provision one per application. **Ingress** lets one entry point (backed by an Ingress Controller like NGINX, or a cloud-native one like AWS Load Balancer Controller) route HTTP(S) traffic to many Services by hostname/path:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
spec:
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web
                port: { number: 80 }
```

An Ingress resource does nothing by itself — it requires an Ingress Controller running in the cluster to actually watch and act on it.

## NetworkPolicy

By default, every Pod can talk to every other Pod in the cluster — flat networking. A **NetworkPolicy** restricts that, but only if the cluster's CNI plugin (Calico, Cilium, etc.) supports enforcement — some CNIs silently ignore NetworkPolicy objects. Policies are additive/allow-based and default-deny once any policy selects a Pod for a given direction:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: deny-from-other-ns }
spec:
  podSelector: {}
  policyTypes: [Ingress]
  ingress:
    - from:
        - podSelector: {}
```

## Storage: PV, PVC, StorageClass

- **PersistentVolume (PV)** — a piece of real storage in the cluster (an EBS volume, an NFS share, etc.), provisioned either statically by an admin or dynamically.
- **PersistentVolumeClaim (PVC)** — a request for storage by a Pod's owner, specifying size and access mode. Kubernetes binds a PVC to a matching PV.
- **StorageClass** — describes a "class" of storage (e.g., `gp3` EBS) and enables **dynamic provisioning**: instead of an admin pre-creating PVs, a PVC referencing a StorageClass triggers automatic PV creation on demand.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: data }
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: gp3
  resources:
    requests: { storage: 10Gi }
```

## RBAC

Kubernetes' own access control, layered on top of (not a replacement for) cloud IAM. Core objects: a **Role** (or **ClusterRole** for cluster-wide) defines a set of permitted verbs on resources; a **RoleBinding** (or **ClusterRoleBinding**) grants that role to a user, group, or ServiceAccount.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { namespace: dev, name: pod-reader }
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
```

A **ServiceAccount** is how a Pod itself authenticates to the API server — analogous to an IAM role for a workload rather than a human.

## Helm

The most common package manager for Kubernetes: a **chart** is a templated bundle of manifests with configurable `values.yaml`. `helm install`, `helm upgrade`, and `helm rollback` manage a chart as one versioned "release" instead of applying loose YAML files by hand — this is how most teams install third-party software (ingress controllers, monitoring stacks) into a cluster.

## Autoscaling

- **Horizontal Pod Autoscaler (HPA)** — scales the number of Pod replicas based on observed metrics (CPU, memory, or custom metrics).
- **Cluster Autoscaler** — scales the number of *nodes* when Pods can't be scheduled due to insufficient capacity (or scales nodes down when they're underused).

These operate independently and are often used together: HPA adds Pods, Cluster Autoscaler adds nodes when there's nowhere left to put those new Pods.

## Troubleshooting checklist (the CKA mindset)

1. `kubectl get pods -o wide` — is it even scheduled? What node?
2. `kubectl describe pod <name>` — check Events at the bottom first; most scheduling/pull/probe failures show up there.
3. `kubectl logs <pod> [-c <container>] [--previous]` — `--previous` matters if the container already restarted/crashed.
4. `kubectl get events --sort-by=.lastTimestamp` — cluster-wide recent events, useful when you don't even know which resource is the problem.

## Common exam/interview traps

- Assuming NetworkPolicy is enforced regardless of CNI — it depends entirely on the CNI plugin.
- Forgetting Ingress requires a controller to do anything.
- Confusing HPA (more Pods) with Cluster Autoscaler (more nodes) — they solve different bottlenecks.
- Not knowing `kubectl describe` surfaces the "why" that `kubectl get` doesn't.
