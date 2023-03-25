# Memimto server

Should be use with memimto client

## Env variable
Create a .env file to store server env variable
Here are the variable you must provide:
- *DB_URI* database URI in SQLAlchemy format
- *BROKER_URI* redis URI
- *DATA_DIR* dir used to store images

## Docker compose

```bash
docker compose up
```