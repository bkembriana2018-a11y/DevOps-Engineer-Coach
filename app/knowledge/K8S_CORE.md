# Kubernetes Core Objects

Kubernetes orchestrates containers across a cluster of machines (nodes). The core objects below are the vocabulary everything else is built on.

## Pods

The smallest deployable unit — one or more containers that share network namespace (same IP, can talk via `localhost`) and can share storage volumes. You almost never create a bare Pod directly in production; something else (a Deployment, usually) manages Pods for you so they get recreated on failure.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
    - name: nginx
      image: nginx:1.27
      ports:
        - containerPort: 80
```

## Deployments and ReplicaSets

A **Deployment** describes a desired state for a set of identical Pods (image, replica count, update strategy) and manages a **ReplicaSet** underneath it, which in turn ensures the right number of Pods exist. You edit the Deployment; you almost never touch the ReplicaSet directly.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels: { app: web }
  template:
    metadata:
      labels: { app: web }
    spec:
      containers:
        - name: web
          image: myapp:1.2.0
```

Updating `image` and re-applying triggers a **rolling update** by default: new Pods come up, old ones terminate, gradually — zero downtime if `readinessProbe` is configured correctly. `kubectl rollout undo deployment/web` rolls back to the previous revision.

## Services

Pods are ephemeral and get new IPs when recreated — a **Service** gives a stable virtual IP and DNS name that load-balances across whatever Pods currently match its label selector.

- **ClusterIP** (default) — reachable only inside the cluster.
- **NodePort** — exposes the service on a static port on every node's IP; mostly used for quick testing, rarely for production traffic.
- **LoadBalancer** — asks the cloud provider (e.g., AWS via a Network Load Balancer through the AWS cloud controller) to provision an external load balancer pointing at the service.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  selector: { app: web }
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP
```

The selector-to-label matching is the whole mechanism — a Service has no idea which Deployment "owns" the Pods it routes to; it just matches labels.

## Namespaces

A way to partition a cluster into virtual clusters — separate teams, environments, or applications can live in `dev`, `staging`, `team-a`, etc. without name collisions. Most `kubectl` commands default to the `default` namespace unless you pass `-n <namespace>` or set a context default. Resource quotas and RBAC are commonly scoped per-namespace.

## ConfigMaps and Secrets

Both inject configuration into Pods without baking it into the container image — ConfigMaps for non-sensitive data, Secrets for sensitive data (API keys, passwords). Critically: **Secrets are base64-encoded, not encrypted, by default** — anyone with API access to read the Secret can trivially decode it. Encryption at rest for Secrets (etcd encryption) and tighter RBAC are separate things you must set up deliberately.

```yaml
apiVersion: v1
kind: ConfigMap
metadata: { name: app-config }
data:
  LOG_LEVEL: "info"
```

Both can be mounted as environment variables or as files inside a container.

## Common exam/interview traps

- Editing a ReplicaSet directly instead of the Deployment that owns it — your changes get overwritten on the next reconcile.
- Assuming Secrets are encrypted just because they're not stored as plain text — base64 is encoding, not encryption.
- Forgetting a Service does nothing without matching Pod labels — a classic "why can't I reach my app" bug is a typo in `selector` vs. the Pod template's `labels`.
- Not setting `readinessProbe`/`livenessProbe`, so a rolling update or a stuck container isn't handled the way you'd expect.
