docker compose down -v --remove-orphans
docker compose build
docker compose up -d --force-recreate crypto-node
docker compose logs -f