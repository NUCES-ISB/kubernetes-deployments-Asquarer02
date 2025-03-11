[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/97WR5HaV)

# Flask Application with PostgreSQL on Kubernetes

This repository contains Kubernetes manifests and application code to deploy a Flask web application with a PostgreSQL database on a Minikube cluster.

## Prerequisites

- Minikube installed
- kubectl installed
- Docker installed

## Setup Instructions

1. **Start Minikube**
   ```
   minikube start
   ```

2. **Create Kubernetes Resources**
   ```
   kubectl apply -f manifests/configmap/postgres-configmap.yaml
   kubectl apply -f manifests/secret/postgres-secret.yaml
   kubectl apply -f manifests/deployment/postgres-deployment.yaml
   kubectl apply -f manifests/service/postgres-service.yaml
   kubectl apply -f manifests/deployment/flask-deployment.yaml
   kubectl apply -f manifests/service/flask-service.yaml
   ```

3. **Access the Application**
   ```
   minikube service flask-service
   ```

## Verification

After accessing the application via the URL provided by Minikube, you should see:
- A welcome message on the homepage
- The ability to add and view messages in the database
- Database connection status

## Clean Up

To remove all resources:
```
kubectl delete -f manifests/service/flask-service.yaml
kubectl delete -f manifests/deployment/flask-deployment.yaml
kubectl delete -f manifests/service/postgres-service.yaml
kubectl delete -f manifests/deployment/postgres-deployment.yaml
kubectl delete -f manifests/secret/postgres-secret.yaml
kubectl delete -f manifests/configmap/postgres-configmap.yaml
```

To stop Minikube:
```
minikube stop
```
