# ====================
# Local Development
# ====================

# Build and run containers
up:
	docker compose up --build

# Stop and remove containers
down:
	docker-compose down

# Check running containers
ps:
	docker ps

# Load earthquake data
reload:
	curl -X POST http://localhost:5000/data

# Delete all earthquake data
clear:
	curl -X DELETE http://localhost:5000/data

# ====================
# Kubernetes deployment
# ====================

# Deploy to production
apply-prod:
	kubectl apply -f app-prod-deployment-flask.yml \
		-f app-prod-deployment-worker.yml \
		-f app-prod-pvc-redis.yml \
		-f app-prod-service-nodeport-flask.yml \
		-f pvc-basic.yaml \
		-f app-prod-deployment-redis.yml \
		-f app-prod-ingress-flask.yml \
		-f app-prod-service-flask.yml \
		-f app-prod-service-redis.yml

# Deploy to test environment
apply-test:
	kubectl apply -f app-test-deployment-flask.yml \
		-f app-test-deployment-redis.yml \
		-f app-test-deployment-worker.yml \
		-f app-test-service-flask.yml \
		-f app-test-service-nodeport-flask.yml \
		-f app-test-service-redis.yml \
		-f app-test-ingress-flask.yml \
		-f pvc-basic.yaml \
		-f app-test-pvc-redis.yml \
		-f app-test-job.yml