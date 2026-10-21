# Testing Checklist – Argus + neolink + Frigate

## 1. Camera side
- [ ] Camera powers on and connects to Wi-Fi in the Reolink app
- [ ] UID is visible in Device Info
- [ ] Motion detection works and creates clips on microSD
- [ ] Solar panel is connected and charging (check battery % in app)

## 2. neolink
- [ ] Container starts without errors (`docker logs neolink`)
- [ ] Web UI opens at http://<pi-ip>:8655
- [ ] Camera appears online
- [ ] RTSP stream plays in VLC: rtsp://<pi-ip>:8654/production1

## 3. Frigate
- [ ] Frigate web UI loads at http://<pi-ip>:5000
- [ ] Camera shows live view
- [ ] Detection boxes appear on motion
- [ ] Events are created and clips are saved

## 4. Database
- [ ] `python3 frigate_to_sqlite.py` runs without error
- [ ] Rows appear in events.db

## 5. Outdoor / Estonia
- [ ] Wi-Fi signal at mount location is strong enough
- [ ] Solar panel faces south and is steep (≥60°)
- [ ] Camera and mount are secure against wind
- [ ] Battery percentage is monitored for the first week
