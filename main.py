import datetime
import signal
import threading
import time
import yaml
from pathlib import Path

from client.camera import Camera


# Global shutdown event used for all scheduler threads
shutdown_event = threading.Event()


# --------------------------------------------------------
# Utility functions
# --------------------------------------------------------

def parse_time_str(t: str):
    hour, minute = map(int, t.split(":"))
    return hour, minute


def next_run_time(hour: int, minute: int) -> datetime.datetime:
    now = datetime.datetime.now()
    run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if run <= now:
        run += datetime.timedelta(days=1)
    return run


def sleep_until(dt: datetime.datetime):
    """Interruptible sleep until datetime dt."""
    now = datetime.datetime.now()
    seconds = (dt - now).total_seconds()
    if seconds > 0:
        shutdown_event.wait(timeout=seconds)


# --------------------------------------------------------
# CameraScheduler Class
# --------------------------------------------------------

class CameraScheduler:
    def __init__(self, config: dict):
        self.ip = config["ip_address"]
        self.username = config["username"]
        self.password = config["password"]
        self.schedule_strings = config["schedule"]  # list of "HH:MM"

        # Pre-parse schedule times
        self.schedule_times = [parse_time_str(t) for t in self.schedule_strings]

        # Camera instance
        self.camera = Camera(self.ip, self.username, self.password)

        # Thread handle
        self.thread = threading.Thread(target=self.run, daemon=False)

    def start(self):
        print(f"[{self.ip}] Starting scheduler thread...")
        self.thread.start()

    def join(self):
        self.thread.join()

    def run(self):
        print(f"[{self.ip}] Scheduler thread started.")

        while not shutdown_event.is_set():
            # Determine the next run datetime
            next_times = [
                next_run_time(h, m)
                for (h, m) in self.schedule_times
            ]
            next_run = min(next_times)

            print(f"[{self.ip}] Next reboot scheduled at {next_run}")
            sleep_until(next_run)

            if shutdown_event.is_set():
                break

            # Perform the action
            self.execute_reboot()

        print(f"[{self.ip}] Scheduler thread exiting.")

    def execute_reboot(self):
        print(f"[{self.ip}] Executing reboot at {datetime.datetime.now()}...")
        try:
            self.camera.reboot()
            print(f"[{self.ip}] Reboot command sent.")
        except Exception as e:
            print(f"[{self.ip}] ERROR during reboot: {e}")


# --------------------------------------------------------
# Signal Handling
# --------------------------------------------------------

def handle_signal(signum, frame):
    print(f"Received signal {signum}. Initiating shutdown...")
    shutdown_event.set()


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


# --------------------------------------------------------
# Main Application
# --------------------------------------------------------

def _load_config():
    with open(Path("config.yaml"), "r") as f:
        return yaml.safe_load(f)


def main():
    cfg = _load_config()

    schedulers = [
        CameraScheduler(cam_cfg)
        for cam_cfg in cfg["cameras"]
    ]

    # Start all scheduler threads
    for s in schedulers:
        s.start()

    print("All scheduler threads started.")

    # Keep main alive until shutdown
    while not shutdown_event.is_set():
        time.sleep(0.5)

    print("Shutdown requested. Waiting for all threads...")

    for s in schedulers:
        s.join()

    print("Shutdown complete.")


if __name__ == "__main__":
    main()
