import sys
import time
import subprocess
from threading import Timer, Lock
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

# Get script name from command line arguments or default to run.py
SCRIPT_FILENAME = sys.argv[1] if len(sys.argv) > 1 else "run.py"

class ReloadableRunner:
    def __init__(self, script_name):
        self.script_name = script_name
        self.proc = None
        self.reload_timer = None
        self.lock = Lock()
        self.is_shutting_down = False

    def start_process(self):
        """Spawns the child process if it's not already running."""
        with self.lock:
            if self.is_shutting_down:
                return

            # If there's an existing process, kill it first
            self._kill_process_unsafe()

            print(f"[Supervisor] Starting {self.script_name}...")
            try:
                # Use sys.executable to run with the exact same virtualenv/interpreter
                self.proc = subprocess.Popen([sys.executable, self.script_name])
            except Exception as e:
                print(f"[Supervisor] Failed to start {self.script_name}: {e}")

    def _kill_process_unsafe(self):
        """Kills the active process (internal helper, assumes lock is acquired)."""
        if self.proc is not None:
            try:
                if self.proc.poll() is None:
                    print(f"[Supervisor] Stopping current process (PID: {self.proc.pid})...")
                    self.proc.kill()
                    self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("[Supervisor] Process did not terminate in time. Forcing termination...")
            except Exception as e:
                print(f"[Supervisor] Error killing process: {e}")
            finally:
                self.proc = None

    def handle_file_modified(self, event):
        """Fires when watched files change. Debounces and schedules reload."""
        print(f"[Supervisor] File change detected: {event.src_path}")
        
        with self.lock:
            if self.is_shutting_down:
                return

            # Cancel any pending reload timer
            if self.reload_timer is not None:
                self.reload_timer.cancel()

            # Schedule reload. We kill the process and start the new one
            # only AFTER the debounce period (1 second) has passed.
            # This ensures we don't kill the bot prematurely and gives
            # the editor time to finish writing all files.
            self.reload_timer = Timer(1.0, self.start_process)
            self.reload_timer.start()

    def check_and_recover(self):
        """Checks if the process has crashed/exited and restarts it if necessary."""
        with self.lock:
            if self.is_shutting_down:
                return

            # If there is a pending reload timer, don't auto-recover yet
            if self.reload_timer is not None and self.reload_timer.is_alive():
                return

            if self.proc is not None:
                exit_code = self.proc.poll()
                if exit_code is not None:
                    print(f"[Supervisor] Process exited unexpectedly with code {exit_code}.")
                    self.proc = None
                    # Restart the process after a brief pause
                    # (using Timer to avoid blocking the main thread)
                    self.reload_timer = Timer(2.0, self.start_process)
                    self.reload_timer.start()

    def shutdown(self):
        """Gracefully shuts down the runner and terminates the child process."""
        print("[Supervisor] Shutting down supervisor...")
        with self.lock:
            self.is_shutting_down = True
            if self.reload_timer is not None:
                self.reload_timer.cancel()
            self._kill_process_unsafe()


if __name__ == "__main__":
    runner = ReloadableRunner(SCRIPT_FILENAME)
    
    # Start the initial process
    runner.start_process()

    # Configure the file watcher
    # Match any *.py files but ignore reloadable.py and virtual environments
    event_handler = PatternMatchingEventHandler(
        patterns=["*.py"],
        ignore_patterns=["*reloadable.py", "*.venv*", "*venv*"],
        case_sensitive=False
    )
    event_handler.on_modified = runner.handle_file_modified

    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=True)
    observer.start()

    print("[Supervisor] Watching for file changes (ignoring reloadable.py and venvs)...")

    try:
        while observer.is_alive():
            # Periodically check if the child process has crashed
            runner.check_and_recover()
            time.sleep(1)
    except KeyboardInterrupt:
        print("[Supervisor] Received keyboard interrupt.")
    finally:
        observer.stop()
        runner.shutdown()
        observer.join()
