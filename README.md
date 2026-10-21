# Puidujaak — Solar Outdoor Camera System (Garage48)

Reolink Argus-style solar outdoor cameras + Raspberry Pi (neolink + Frigate) for event-based monitoring.

Built for outdoor use in Estonia (cold winters, low solar irradiance).

## What’s inside

- `docker-compose.yml` — runs neolink + Frigate together
- `configs/` — example configs for neolink and Frigate
- `scripts/frigate_to_sqlite.py` — push Frigate events into SQLite
- `docs/TESTING_CHECKLIST.md` — verification steps
- `3d/` — OpenSCAD models for outdoor mount + rain hood (+ solar bracket)

## Quick start

1. Buy a Reolink Argus 4 Pro + Solar Panel 2.
2. Note the camera UID from the Reolink app.
3. Copy the example configs and fill in password + UID.
4. On the Raspberry Pi:
   ```bash
   docker compose up -d
   ```
5. Follow `docs/TESTING_CHECKLIST.md`.

## Architecture

```
Argus camera (solar, event-based)
        ↓
     neolink (RTSP bridge)
        ↓
      Frigate (detection + clips)
        ↓
   Your database / software
```

Customer only needs the Reolink app. You own the data.

---
Created for Garage48 challenge.
