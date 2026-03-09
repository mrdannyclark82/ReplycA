import argparse
import json
import time
from typing import List, Dict

import requests
from rich.console import Console
from rich.live import Live
from rich.table import Table


console = Console()


def parse_args():
    parser = argparse.ArgumentParser(description="Stream Milla events over SSE")
    parser.add_argument(
        "--endpoint",
        default="http://localhost:9000/events",
        help="SSE endpoint (default: http://localhost:9000/events)",
    )
    parser.add_argument("--last", type=int, default=0, help="Start from event id (default: 0)")
    parser.add_argument("--max-events", type=int, default=50, help="Events to keep in view")
    parser.add_argument("--retry", type=int, default=3, help="Seconds before reconnect on failure")
    return parser.parse_args()


def render(events: List[Dict]) -> Table:
    table = Table(title="Milla Stream", show_lines=False, expand=True)
    table.add_column("id", style="dim", width=6)
    table.add_column("role", style="cyan", width=12)
    table.add_column("source", style="magenta", width=10)
    table.add_column("content", style="white")

    for ev in events:
        table.add_row(
            str(ev.get("id", "")),
            ev.get("role", ""),
            ev.get("source", ""),
            ev.get("content", "")[:400],
        )
    return table


def main():
    args = parse_args()
    endpoint = args.endpoint
    last = args.last
    buffer: List[Dict] = []

    with Live(render(buffer), console=console, refresh_per_second=4) as live:
        while True:
            try:
                resp = requests.get(f"{endpoint}?last={last}", stream=True, timeout=30)
                resp.raise_for_status()
                data_lines = []
                for raw_line in resp.iter_lines(decode_unicode=True):
                    if raw_line is None:
                        continue
                    line = raw_line.strip()
                    if not line:
                        if not data_lines:
                            continue
                        id_val = None
                        content_line = None
                        for l in data_lines:
                            if l.startswith("id:"):
                                try:
                                    id_val = int(l.split(":", 1)[1].strip())
                                except Exception:
                                    id_val = None
                            if l.startswith("data:"):
                                content_line = l.split(":", 1)[1].strip()
                        if content_line:
                            try:
                                event_obj = json.loads(content_line)
                            except Exception:
                                event_obj = {"content": content_line}
                            if id_val is not None:
                                event_obj["id"] = id_val
                                last = id_val + 1
                            buffer.append(event_obj)
                            if len(buffer) > args.max_events:
                                buffer = buffer[-args.max_events :]
                            live.update(render(buffer))
                        data_lines = []
                        continue
                    data_lines.append(line)
            except Exception as e:
                console.log(f"[red]Stream error:[/red] {e}, retrying in {args.retry}s")
                time.sleep(args.retry)


if __name__ == "__main__":
    main()
