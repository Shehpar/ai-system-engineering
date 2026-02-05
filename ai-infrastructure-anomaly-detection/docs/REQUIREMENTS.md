# Requirements & Problem Statement

## Project Overview
**AI-Based Anomaly Detection for IT Infrastructure**  
**Course:** AI Systems Engineering (2025-26)  
**Type:** Innovation-Driven (INN)  
**Domain:** IT Infrastructure / Cloud Computing

## Problem Statement

### Context
Modern IT infrastructure (cloud clusters, data centers, server farms) generates continuous streams of system metrics (CPU, memory, network utilization). Manual monitoring is impractical; automated anomaly detection can:
- Prevent cascading failures by alerting operators early
- Reduce mean-time-to-recovery (MTTR)
- Identify performance degradation patterns

### Specific Problem
**Detect anomalous system behavior in real-time** using CPU, memory, and network metrics from a monitored server, to enable proactive remediation and prevent system failures.

### Success Criteria (KPIs)

| Metric | Target | Justification |
|--------|--------|--------------|
| **Detection Rate (Recall)** | ≥ 90% | Must catch anomalies before they cascade |
| **False Alarm Rate (1-Precision)** | ≤ 10% | Ops team fatigue; too many false alerts hurt adoption |
| **Prediction Latency** | < 5 seconds | Real-time alerting for on-call responders |
| **Model Retraining Interval** | ≤ 5 minutes | Adapt to gradual performance changes |
| **System Uptime (SLA)** | ≥ 99.5% | Monitoring system must be highly available |
| **Data Retention** | 30 days | Balance cost vs. historical context for drift detection |

## Stakeholders

### Primary Users
- **IT Operations Team**: Alerted on anomalies, makes remediation decisions
- **DevOps/SRE**: Tunes alerting thresholds, manages deployment

### Secondary Stakeholders
- **Cloud Infrastructure Owner**: Wants to minimize downtime/incidents
- **Management**: Concerned with cost and incident metrics

## Requirements

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| **FR1** | Ingest live metrics | Script connects to InfluxDB every 10s and retrieves CPU/mem/net |
| **FR2** | Train anomaly model | Offline training completes in <30s with ≥100 samples |
| **FR3** | Detect anomalies | Model predicts within 5s; output written to InfluxDB |
| **FR4** | Alert on anomaly | Grafana dashboard shows anomaly flag in real-time |
| **FR5** | Retrain model | Automatic retraining triggered by: (a) time-based (5 min), (b) drift detected |
| **FR6** | Persist predictions | All predictions logged to InfluxDB for audit/replay |
| **FR7** | Handle missing data | Script gracefully handles failed metric queries (retry, not crash) |

### Non-Functional Requirements

| ID | Category | Requirement | Target |
|----|----------|-------------|--------|
| **NFR1** | **Performance** | Prediction latency | < 5 sec |
| **NFR2** | **Performance** | Training time | < 30 sec |
| **NFR3** | **Reliability** | Availability | ≥ 99.5% |
| **NFR4** | **Maintainability** | Code documentation | README + Model Card |
| **NFR5** | **Scalability** | Max metrics rate | 100 metrics/min |
| **NFR6** | **Security** | Credentials | No hardcoded secrets; use env vars |
| **NFR7** | **Interpretability** | Explainability | Model card includes algorithm, params, limitations |

## Constraints

- **Technology**: Python 3.9+, Docker, InfluxDB, Grafana
- **Data**: Only 3 metrics (CPU, mem, net); no metadata (e.g., no user tagging of anomalies)
- **Infrastructure**: Single-node deployment; scaling beyond 1 cluster out of scope
- **Timeline**: Proof-of-concept; no SLA guarantee in production

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|-----------|
| **High false alarm rate** | Ops ignores alerts | Medium | Tune contamination parameter; perform robustness tests |
| **Data drift (distribution shift)** | Model accuracy degrades | High | Implement drift detection (KS-test); trigger retraining |
| **Monitoring downtime** | No anomaly alerts; cascading failures | Low | Add Docker healthchecks; use restart policy |
| **InfluxDB outage** | Cannot query metrics; model can't predict | Low | Retry logic with exponential backoff; log errors |
| **Model overfitting** | False negatives on novel anomalies | Medium | Use unsupervised learning (Isolation Forest); hold-out test set |

## Data

### Source
- **Site A**: Monitoring system (Python script, InfluxDB, Grafana)
- **Site B**: Monitored infrastructure (Flask app in Docker, Telegraf agent)

### Schema
| Field | Type | Unit | Range | Description |
|-------|------|------|-------|------------|
| `cpu_usage` | Float | % | [0, 100] | CPU utilization percentage |
| `memory_usage` | Float | % | [0, 100] | Memory (RAM) utilization percentage |
| `network_load` | Float | bytes/sec | [0, ∞) | Network received bytes per second |

### Data Quality Expectations
- **Freshness**: ≤ 1 min old
- **Completeness**: No nulls; if missing, skip that measurement cycle
- **Outliers**: Expected (e.g., periodic spikes during backup); model must be robust
- **Volume**: ~100–1000 samples/day depending on query interval

## Deployment Model

- **Type**: Containerized (Docker)
- **Orchestration**: Docker Compose (local dev/demo)
- **Environment**: Single server or cluster node
- **Rollout Strategy**: Manual (future: blue-green canary)

## Metrics & Monitoring

### Model Metrics
- **Precision, Recall, F1-Score** (offline test set)
- **ROC-AUC** (if ground truth available)
- **Prediction latency** (p50, p95)

### System Metrics
- **Uptime** (% operational)
- **Prediction rate** (anomalies/hour)
- **Retrain frequency** (actual vs. expected)
- **Data freshness lag** (seconds behind real-time)

## Definition of Done

✅ Requirements elicited with teacher  
✅ Offline training script with train/val/test split  
✅ Evaluation report (precision, recall, F1, robustness tests)  
✅ Data validation checks in place  
✅ Drift detection implemented  
✅ Model versioning and MLflow tracking  
✅ Docker deployment verified  
✅ Grafana dashboard showing predictions  
✅ Documentation (README, architecture, model card, deployment guide)  
✅ GitHub repository with clean commit history  

---

**Next Steps:**
1. Validate requirements with teacher
2. Run `train_model.py` on initial dataset
3. Run `evaluate_model.py` for robustness assessment
4. Deploy with Docker Compose
5. Monitor for 24–48 hours before concluding
