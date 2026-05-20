#!/bin/bash

IMAGE="borne-medias-pygame:1.0"
CONTAINER="borne-medias-pygame"

echo "[run] Lancement du container"

xhost +local:docker

docker run -d \
  --name "$CONTAINER" \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  "$IMAGE"

echo "[ok] Borne démarrée"