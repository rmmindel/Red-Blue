# Arena

A red-team / blue-team security learning game. Plant an attack against a
deliberately vulnerable target, then switch seats and defend against it.

## Safety - read before running

This project runs intentionally vulnerable services, for an isolated lab only.

- Everything runs on a no-egress Docker network (internal: true): the targets
  have no route to the internet.
- Ports are published to 127.0.0.1 only, so nothing off your machine can reach them.
- Run this on your own machine, for your own learning, only. Do not expose it,
  do not deploy it, and never point its tools at anything you do not own.

## Requirements

- Docker Desktop (Linux-container / WSL2 backend on Windows)

## Run

    docker compose build
    docker compose up -d

Then open http://127.0.0.1:8001 . Stop with: docker compose down
