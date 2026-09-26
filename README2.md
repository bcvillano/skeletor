# Skeletor

## Quickstart
### Setting Up Server
The recommended setup method for setting up the Skeletor server is using the provided Docker Compose files (docker-compose.yml for HTTP, or https/docker-compose.yml for HTTPS). This:
- Builds the Dockerfile to create the Docker image for the Skeletor server, using the .env file present in the same directory
- Sets up the backend Postgres database container
- Configures environment variables allowing communication between the Skeletor container and Postgres container
- For the docker-compose file in the https directory, also set up nginx reverse proxy for HTTPS, using the certificates in the https/certs directory
  
Alternatively, the server can be run standalone using skeletor.py, either with or without gunicorn.
If using a Postgres backend (recommended), then the DB_HOST,DB_PORT,DB_NAME,DB_USER and DB_PASSWORD environment variables must be set. If the DB_HOST variable is not set, Skeletor will default to instead use a SQLite database  

To 

### Setting Up Client