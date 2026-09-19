#!/usr/bin/env bash
# Double-click this file in Finder to install (first run only) and start Cloud Coach.
cd "$(dirname "$0")"
chmod +x run.sh

./run.sh &
SERVER_PID=$!

echo "Waiting for the app to come up..."
for i in $(seq 1 90); do
  if curl -s http://127.0.0.1:8766/api/health >/dev/null 2>&1; then
    open "http://127.0.0.1:8766"
    break
  fi
  sleep 0.5
done

echo ""
echo "Close this window (or press Ctrl+C) to stop Cloud Coach."
wait $SERVER_PID
