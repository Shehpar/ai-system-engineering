# AI-Based Anomaly Detection for IT Infrastructure
**Course:** AI Systems Engineering (2025-26)  
**Professor:** Roberto Pietrantuono  
**Student Project Type:** Innovation-driven (INN)

## 📌 Project Overview
This project implements an end-to-end AI system for monitoring cloud infrastructure. It detects anomalies in system metrics (CPU, Memory, Disk) using an **Isolation Forest** model to prevent potential system failures.



## 🛠️ System Architecture & Life Cycle
In line with the AISE course syllabus, this project covers the full system life cycle:
1. [cite_start]**Requirements:** Identifying the need for proactive failure detection in IT clusters[cite: 130].
2. [cite_start]**Design:** A microservice-oriented architecture using Docker[cite: 15, 16].
3. [cite_start]**Development:** Data simulation, feature engineering (StandardScaler), and model persistence[cite: 13, 14].
4. [cite_start]**Testing:** Quality assurance through Precision, Recall, and F1-Score metrics[cite: 22, 72].
5. [cite_start]**Operations:** Continuous monitoring via a Grafana dashboard[cite: 70].

## 📂 Repository Structure
- `src/`: Python scripts for data generation, training, and inference.
- `models/`: Serialized model artifacts (.pkl).
- `data/`: Raw and processed simulated datasets.
- `docker/`: Containerization files (Dockerfile, docker-compose).
- `dashboard/`: Grafana dashboard configurations.
- `results/`: Evaluation reports and performance metrics.

## 🚀 Getting Started (Deployment)
[cite_start]This project is fully containerized for reproducibility[cite: 148].

### Prerequisites
- Docker and Docker Compose installed.

### Execution
1. Clone the repository.
2. Run the system:
   ```bash
   docker-compose -f docker/docker-compose.yml up --build