---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker-deployment
  labels:
    app: worker-app
spec:
  replicas: 4
  selector:
    matchLabels:
      app: worker-app
  template:
    metadata:
      labels:
        app: worker-app
    spec:
      containers:
        - name: worker
          image: jasmineeds/tectonic-tantrums:v1.0.0
          env: 
            - name: REDIS_HOST
              value: redis-service
            - name: REDIS_PORT
              value: "6379"
            - name: PYTHONPATH
              value: src
          command: ["python3", "src/worker.py"]
