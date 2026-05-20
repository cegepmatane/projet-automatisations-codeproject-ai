#!/bin/bash

IMAGE="borne-medias-pygame:1.0"
CONTAINER="borne-medias-pygame"

echo "[run] Lancement du container"

# Vérifie si xhost existe
if command -v xhost >/dev/null 2>&1; then
  xhost +local:docker
else
  echo "[warn] xhost introuvable (installe x11-xserver-utils)"
fi

docker run -d \
  --name "$CONTAINER" \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  "$IMAGE"

echo "[ok] Borne démarrée"