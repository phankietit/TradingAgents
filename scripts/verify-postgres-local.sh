#!/usr/bin/env bash
# Isolated local QA only. Never accepts an existing database or container.
set -euo pipefail

if [[ "${TA_ALLOW_TEST_DB_RESET:-}" != "1" ]]; then
  echo 'Set TA_ALLOW_TEST_DB_RESET=1 to acknowledge creation/removal of a disposable test database.' >&2
  exit 2
fi
command -v docker >/dev/null
docker image inspect postgres:16-alpine >/dev/null
task_id="ta-research-qa-$(date +%s)-$$"
task_container="${task_id}"
task_created=0
cleanup() {
  if [[ "$task_created" == 1 ]]; then
    task_owner=$(docker inspect --format '{{index .Config.Labels "tradingagents.qa.owner"}}' "$task_container" 2>/dev/null || true)
    if [[ "$task_owner" == "$task_id" ]]; then
      docker stop --time 5 "$task_container" >/dev/null
      docker rm "$task_container" >/dev/null
      echo 'Removed only this task-owned disposable PostgreSQL container.'
    else
      echo 'Cleanup withheld: ownership label could not be verified.' >&2
    fi
  fi
}
trap cleanup EXIT
task_password=$(openssl rand -hex 24)
docker run -d --name "$task_container" --label "tradingagents.qa.owner=$task_id" \
  --memory 512m --cpus 1 --tmpfs /var/lib/postgresql/data:rw,size=256m \
  -p 127.0.0.1::5432 -e POSTGRES_USER=ta_qa -e POSTGRES_DB=ta_qa \
  -e "POSTGRES_PASSWORD=$task_password" postgres:16-alpine >/dev/null
task_created=1
task_ready=0
for _ in {1..30}; do
  if docker exec "$task_container" pg_isready -U ta_qa -d ta_qa >/dev/null 2>&1; then
    task_ready=1
    break
  fi
  sleep 1
done
[[ "$task_ready" == 1 ]] || { echo 'Disposable PostgreSQL did not become ready.' >&2; exit 1; }
task_port=$(docker inspect --format '{{(index (index .NetworkSettings.Ports "5432/tcp") 0).HostPort}}' "$task_container")
[[ "$task_port" =~ ^[0-9]+$ ]] || exit 1
export TEST_POSTGRES_URL="postgresql+psycopg://ta_qa:${task_password}@127.0.0.1:${task_port}/ta_qa"
bash scripts/verify-local.sh --postgres
