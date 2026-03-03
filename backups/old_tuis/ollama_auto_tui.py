import curses
import os
import signal
import subprocess
import threading
import time
from collections import deque
from typing import List, Optional


LOG_LIMIT = 500
POLL_INTERVAL = 0.05


class ProcessRunner:
    def __init__(self):
        self.proc: Optional[subprocess.Popen] = None
        self.lines: deque[str] = deque(maxlen=LOG_LIMIT)
        self.lock = threading.Lock()

    def start(self, args: List[str]) -> None:
        if self.proc and self.proc.poll() is None:
            self.lines.append("!! A run is already in progress. Stop it before starting another.")
            return
        self.lines.append(f">> Launching: {' '.join(args)}")
        self.proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        threading.Thread(target=self._pump_output, daemon=True).start()

    def _pump_output(self) -> None:
        assert self.proc and self.proc.stdout
        for line in self.proc.stdout:
            with self.lock:
                self.lines.append(line.rstrip("\n"))
        code = self.proc.wait()
        with self.lock:
            self.lines.append(f"<< Process exited with code {code}")

    def send(self, text: str) -> None:
        if not self.proc or self.proc.poll() is not None:
            self.lines.append("!! No running process to send input.")
            return
        assert self.proc.stdin
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()
        self.lines.append(f">> {text}")

    def stop(self) -> None:
        if not self.proc or self.proc.poll() is not None:
            self.lines.append("!! No running process to stop.")
            return
        self.proc.send_signal(signal.SIGINT)
        self.lines.append("<< Sent SIGINT to process.")

    def get_lines(self) -> List[str]:
        with self.lock:
            return list(self.lines)

    def status(self) -> str:
        if not self.proc:
            return "idle"
        code = self.proc.poll()
        if code is None:
            return "running"
        return f"exited ({code})"


def draw(stdscr, runner: ProcessRunner) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        status_line = (
            "[y] YOLO run  [r] Interactive run  [s] Send input  [k] Kill  [q] Quit  | "
            f"Status: {runner.status()}"
        )
        stdscr.addstr(0, 0, status_line[: width - 1])

        log_lines = runner.get_lines()
        start_row = 2
        max_rows = height - start_row - 1
        visible = log_lines[-max_rows:] if max_rows > 0 else []
        for idx, line in enumerate(visible):
            if start_row + idx >= height - 1:
                break
            stdscr.addstr(start_row + idx, 0, line[: width - 1])

        stdscr.refresh()
        time.sleep(POLL_INTERVAL)

        try:
            ch = stdscr.getch()
        except curses.error:
            ch = -1
        if ch == -1:
            continue
        if ch in (ord("q"), ord("Q")):
            break
        if ch in (ord("y"), ord("Y")):
            runner.start(["python", "-u", "milla_auto.py", "--yolo"])
        elif ch in (ord("r"), ord("R")):
            runner.start(["python", "-u", "milla_auto.py"])
        elif ch in (ord("k"), ord("K")):
            runner.stop()
        elif ch in (ord("s"), ord("S")):
            curses.curs_set(1)
            stdscr.addstr(height - 1, 0, "Send> ")
            stdscr.clrtoeol()
            curses.echo()
            try:
                input_str = stdscr.getstr(height - 1, 6, width - 7).decode("utf-8")
            except Exception:
                input_str = ""
            curses.noecho()
            curses.curs_set(0)
            if input_str:
                runner.send(input_str)


def main() -> None:
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    runner = ProcessRunner()
    curses.wrapper(draw, runner)


if __name__ == "__main__":
    main()
