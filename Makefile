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
