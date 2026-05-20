#!/bin/bash

CONTAINER="borne-medias-pygame"

echo "[stop] Arrêt du container"

docker stop "$CONTAINER" 2>/dev/null || true
docker rm "$CONTAINER" 2>/dev/null || true

xhost -local:docker

echo "[ok] Borne arrêtée"