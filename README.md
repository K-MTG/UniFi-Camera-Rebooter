# UniFi Camera Rebooter

Schedules daily reboots for UniFi cameras using a lightweight, thread-based scheduler. 
This was specifically designed for G4 Doorbell which can get sluggish over time without reboots.


Each camera gets its own scheduler thread that:

- Parses its `schedule:` list of `"HH:MM"` times
- Computes the next daily run time
- Sends the reboot command. 
- The script shuts down cleanly when Docker sends **SIGTERM**.

---

## ✨ Features

### 🔧 Camera Session Behavior
- Cookie-aware login (reads cookie expiry)
- Auto-relogin on:
  - expired session  
  - HTTP 401  
- Treats *TLS early disconnect on reboot* as **expected success**
- Per-camera session isolation

### 🕒 Scheduling Behavior
- Each camera has a dedicated scheduling thread
- Supports multiple fixed daily times per camera, e.g.:
```yaml
schedule:
  - "05:15"
  - "22:30"
```
- Times interpreted using the container’s local timezone
(e.g., if running on a host in America/Los_Angeles, the schedule is Pacific time)

### 🧵 Thread Model
- All scheduler threads are non-daemon
- Shutdown via Docker’s SIGTERM wakes sleeping threads immediately
- Clean exit once all threads finish

---

## 📁 Configuration
Example: config.yaml (reference `config.yaml.example`)
```yaml
cameras:
  - ip_address: 10.0.1.69
    username: ubnt
    password: 1234
    schedule:
      - "05:15"
      - "22:30"

  - ip_address: 10.0.1.70
    username: ubnt
    password: hunter2
    schedule:
      - "05:15"
```

### Notes
- Times are strings in 24-hour HH:MM format
- Must be valid local-time entries; seconds not supported (always :00)
- You can list as many times per camera as needed

---

## 🐳 Docker
Build and run using docker compose:
```bash
docker compose up --build -d
```

