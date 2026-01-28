# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the AI Infrastructure Anomaly Detection system to a Kubernetes cluster.

## Files

| File | Purpose |
|------|---------|
| `deployment.yaml` | Main application deployment (3-10 replicas) |
| `service.yaml` | LoadBalancer service (exposes app on port 80) |
| `hpa.yaml` | Horizontal Pod Autoscaler (auto-scaling based on CPU/Memory) |
| `configmap.yaml` | Configuration parameters (non-sensitive) |
| `secret.yaml` | Sensitive credentials (passwords, API keys) |
| `networkpolicy.yaml` | Network security policies (pod communication rules) |
| `pdb.yaml` | Pod Disruption Budget (high availability) |
| `pvc.yaml` | Persistent Volume Claims (storage for models and data) |

## Prerequisites

1. **Kubernetes Cluster**: v1.24+ (EKS, GKE, AKS, or local with minikube)
2. **kubectl**: Configured to connect to your cluster
3. **Container Registry**: Push Docker image to registry accessible by cluster
4. **Storage Class**: Ensure `standard` storage class exists (or modify `pvc.yaml`)

## Quick Start

### 1. Build and Push Docker Image

```bash
# Build image
docker build -t your-registry/ai-anomaly-detector:latest -f docker/Dockerfile .

# Push to registry
docker push your-registry/ai-anomaly-detector:latest
```

### 2. Update Image Reference

Edit `deployment.yaml` and update the image:

```yaml
containers:
- name: anomaly-detector
  image: your-registry/ai-anomaly-detector:latest  # <-- Update this
```

### 3. Create Secrets (Production)

**IMPORTANT**: Replace default passwords in production!

```bash
# Create secrets securely (recommended for production)
kubectl create secret generic anomaly-detector-secrets \
  --from-literal=influxdb_password='YOUR_STRONG_PASSWORD' \
  --from-literal=grafana_admin_password='YOUR_STRONG_PASSWORD' \
  --from-literal=mlflow_db_password='YOUR_STRONG_PASSWORD'

# Or use the provided secret.yaml for development
kubectl apply -f k8s/secret.yaml
```

### 4. Deploy All Resources

```bash
# Apply all Kubernetes manifests
kubectl apply -f k8s/

# Or apply individually in order
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/pdb.yaml
kubectl apply -f k8s/networkpolicy.yaml
```

### 5. Verify Deployment

```bash
# Check pods
kubectl get pods -l app=anomaly-detector

# Check service
kubectl get svc anomaly-detector-service

# Check HPA
kubectl get hpa ai-anomaly-detector-hpa

# Check logs
kubectl logs -l app=anomaly-detector --tail=100 -f
```

### 6. Access the Service

```bash
# Get external IP (for LoadBalancer)
kubectl get svc anomaly-detector-service

# Access the service
# http://<EXTERNAL-IP>:80
```

## Configuration

### Environment Variables

All configuration is managed through ConfigMap and Secrets:

**ConfigMap** (`configmap.yaml`):
- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `influxdb_host`: InfluxDB hostname
- `influxdb_port`: InfluxDB port
- `influxdb_database`: Database name
- `mlflow_tracking_uri`: MLflow server URL
- `model_update_interval`: Retraining interval (seconds)
- `drift_check_interval`: Drift detection interval (seconds)

**Secrets** (`secret.yaml`):
- `influxdb_password`: InfluxDB admin password
- `grafana_admin_password`: Grafana admin password
- `mlflow_db_password`: MLflow database password

### Modify Configuration

```bash
# Edit ConfigMap
kubectl edit configmap anomaly-detector-config

# Edit Secrets
kubectl edit secret anomaly-detector-secrets

# Restart pods to apply changes
kubectl rollout restart deployment ai-anomaly-detector
```

## Scaling

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment ai-anomaly-detector --replicas=5
```

### Auto-Scaling (HPA)

The HPA is already configured in `hpa.yaml`:
- **Min replicas**: 3
- **Max replicas**: 10
- **CPU threshold**: 70%
- **Memory threshold**: 80%

Monitor auto-scaling:

```bash
kubectl get hpa ai-anomaly-detector-hpa -w
```

## Rolling Updates

Update the application with zero downtime:

```bash
# Update image
kubectl set image deployment/ai-anomaly-detector \
  anomaly-detector=your-registry/ai-anomaly-detector:v2.0.0

# Check rollout status
kubectl rollout status deployment ai-anomaly-detector

# View rollout history
kubectl rollout history deployment ai-anomaly-detector
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment ai-anomaly-detector

# Rollback to specific revision
kubectl rollout undo deployment ai-anomaly-detector --to-revision=2
```

## Monitoring

### Pod Status

```bash
# Get all pods
kubectl get pods -l app=anomaly-detector

# Describe pod
kubectl describe pod <POD-NAME>

# Get pod logs
kubectl logs <POD-NAME> -f

# Execute commands in pod
kubectl exec -it <POD-NAME> -- /bin/bash
```

### Resource Usage

```bash
# Check resource usage
kubectl top pods -l app=anomaly-detector
kubectl top nodes

# Check HPA metrics
kubectl get hpa ai-anomaly-detector-hpa
```

### Events

```bash
# View cluster events
kubectl get events --sort-by='.lastTimestamp'

# View deployment events
kubectl describe deployment ai-anomaly-detector
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -l app=anomaly-detector

# Describe pod for events
kubectl describe pod <POD-NAME>

# Check logs
kubectl logs <POD-NAME>
```

Common issues:
- Image pull errors: Check image name and registry access
- CrashLoopBackOff: Check logs for application errors
- Pending: Check resources and PVC status

### Service Not Accessible

```bash
# Check service
kubectl get svc anomaly-detector-service

# Check endpoints
kubectl get endpoints anomaly-detector-service

# Port forward for local access
kubectl port-forward svc/anomaly-detector-service 8080:80
```

### PVC Not Binding

```bash
# Check PVC status
kubectl get pvc

# Describe PVC
kubectl describe pvc model-pvc

# Check storage class
kubectl get storageclass
```

If `standard` storage class doesn't exist, create it or modify `pvc.yaml` to use an available class.

## Security Best Practices

1. **Secrets Management**:
   - Never commit `secret.yaml` with real passwords to Git
   - Use external secret management (AWS Secrets Manager, HashiCorp Vault)
   - Rotate secrets regularly

2. **Network Policies**:
   - `networkpolicy.yaml` restricts pod-to-pod communication
   - Only allows necessary connections (InfluxDB, MLflow, Grafana)
   - Blocks all other traffic by default

3. **RBAC** (Not included - create if needed):
   ```bash
   # Create service account
   kubectl create serviceaccount anomaly-detector-sa
   
   # Create role and binding
   kubectl create role anomaly-detector-role --verb=get,list --resource=pods
   kubectl create rolebinding anomaly-detector-binding \
     --role=anomaly-detector-role \
     --serviceaccount=default:anomaly-detector-sa
   ```

4. **Resource Limits**:
   - CPU limits prevent resource exhaustion
   - Memory limits prevent OOM kills
   - Requests ensure scheduling on appropriate nodes

## High Availability

### Pod Disruption Budget

`pdb.yaml` ensures at least 2 pods are always available during:
- Node maintenance
- Cluster upgrades
- Voluntary evictions

### Multi-Zone Deployment

For production, deploy across multiple availability zones:

```yaml
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - anomaly-detector
        topologyKey: topology.kubernetes.io/zone
```

## Cleanup

Remove all resources:

```bash
# Delete all resources
kubectl delete -f k8s/

# Or delete individually
kubectl delete deployment ai-anomaly-detector
kubectl delete service anomaly-detector-service
kubectl delete hpa ai-anomaly-detector-hpa
kubectl delete configmap anomaly-detector-config
kubectl delete secret anomaly-detector-secrets
kubectl delete networkpolicy anomaly-detector-network-policy
kubectl delete pdb anomaly-detector-pdb
kubectl delete pvc model-pvc data-pvc
```

## Production Checklist

Before deploying to production:

- [ ] Update Docker image with production registry
- [ ] Create secrets securely (not using `secret.yaml`)
- [ ] Configure appropriate storage class and sizes
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure log aggregation (ELK, CloudWatch)
- [ ] Set up alerts for pod failures
- [ ] Configure backup for PVCs
- [ ] Test rolling updates and rollbacks
- [ ] Verify network policies
- [ ] Load test auto-scaling
- [ ] Document runbook for incidents

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
