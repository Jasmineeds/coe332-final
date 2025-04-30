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
          image: ubuntu:22.04
          command: ['sh', '-c', 'echo "Hello, Kubernetes!" && sleep 3600']
