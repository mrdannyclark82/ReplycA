import pygame
import random
import math
import time
import os
import json
import psutil
from multiprocessing import Process, Value
from scipy.spatial import Delaunay
import numpy as np
from pathlib import Path

# Try to import centralized paths
try:
    from core_os.memory.agent_memory import NEURO_FILE
except ImportError:
    # Fallback path
    NEURO_FILE = "core_os/memory/neuro_state.json"

# ---------------------------------------------------------------------------
# FACIAL LANDMARK COORDINATES
# ---------------------------------------------------------------------------
LANDMARKS = [
    (247,370),(258,405),(273,437),(293,465),(318,488),
    (347,504),(378,512),(400,515),(422,512),(453,504),
    (482,488),(507,465),(527,437),(542,405),(553,370),
    (558,333),(560,295),
    (264,238),(286,222),(312,218),(338,222),(360,234),
    (440,234),(462,222),(488,218),(514,222),(536,238),
    (400,252),(400,272),(400,292),(400,312),
    (372,326),(384,336),(400,342),(416,336),(428,326),
    (270,268),(290,258),(314,258),(334,268),(314,278),(290,278),
    (466,268),(486,258),(510,258),(530,268),(510,278),(486,278),
    (322,380),(344,368),(370,362),(400,365),(430,362),
    (456,368),(478,380),(456,394),(430,400),(400,402),
    (370,400),(344,394),
    (344,380),(368,374),(400,374),(432,374),(456,380),
    (432,390),(400,392),(368,390),
]

_pts   = np.array(LANDMARKS, dtype=np.float32)
_tri   = Delaunay(_pts)
TRIANGLES = [(int(a), int(b), int(c)) for a, b, c in _tri.simplices]

FEATURE_EDGES = (
    list(zip(range(0,16), range(1,17))) +        
    list(zip(range(17,21), range(18,22))) +       
    list(zip(range(22,26), range(23,27))) +       
    list(zip(range(27,30), range(28,31))) +       
    [(31,32),(32,33),(33,34),(34,35),(35,31)] +   
    [(36,37),(37,38),(38,39),(39,40),(40,41),(41,36)] +  
    [(42,43),(43,44),(44,45),(45,46),(46,47),(47,42)] +  
    list(zip(range(48,59), range(49,60))) + [(59,48)] +  
    list(zip(range(60,67), range(61,68))) + [(67,60)]   
)

def get_neuro_color():
    default = (0, 220, 255)
    if not os.path.exists(str(NEURO_FILE)):
        return default
    try:
        with open(str(NEURO_FILE)) as f:
            s = json.load(f)
        d = s.get("dopamine", 0.5)
        sr = s.get("serotonin", 0.5)
        n = s.get("norepinephrine", 0.2)
        r = max(0, min(255, int(d * 200 + n * 255)))
        g = max(0, min(255, int(sr * 255 + (1 - n) * 100)))
        b = max(0, min(255, int((1 - d) * 255 + sr * 100)))
        return (r, g, b)
    except Exception:
        return default

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def dim(color, factor):
    return tuple(max(0, int(c * factor)) for c in color)

def get_sys_stats():
    try:
        cpu  = psutil.cpu_percent(interval=None)
        ram  = psutil.virtual_memory()
        return cpu, ram.percent, ram.used // (1024*1024), ram.total // (1024*1024)
    except Exception:
        return 0, 0, 0, 0

class MeshParticle:
    def __init__(self, idx):
        self.idx    = idx
        self.tx, self.ty = LANDMARKS[idx]
        self.x  = random.uniform(0, 800)
        self.y  = random.uniform(0, 600)
        self.vx = 0.0
        self.vy = 0.0
        self.locked = False

    def update(self, progress):
        if self.locked: return
        tx, ty = self.tx, self.ty
        speed  = 0.08 + progress * 0.14
        self.x += (tx - self.x) * speed
        self.y += (ty - self.y) * speed
        if abs(self.x - tx) < 1.5 and abs(self.y - ty) < 1.5:
            self.x, self.y = tx, ty
            self.locked = True

    def draw(self, surf, color):
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), 2)

def run_loading_animation(loading_val):
    if "DISPLAY" not in os.environ:
        os.environ["DISPLAY"] = ":0"

    pygame.init()
    psutil.cpu_percent(interval=None)  
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("MEA OS — Initializing")
    clock  = pygame.time.Clock()
    font_s = pygame.font.SysFont("monospace", 13)
    font_m = pygame.font.SysFont("monospace", 16, bold=True)
    font_l = pygame.font.SysFont("monospace", 22, bold=True)

    try:
        pygame.mixer.init()
        os.system("play -n synth 10 sine 100 vol 0.1 > /dev/null 2>&1 &")
    except Exception: pass

    particles  = [MeshParticle(i) for i in range(len(LANDMARKS))]
    boot_steps = ["Core OS", "Neuro Matrix", "Vocal Sync", "Relay Bridge", "Scout", "Mesh Online"]

    finished_time = None
    running       = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

        progress     = loading_val.value
        mesh_color   = get_neuro_color()
        dim_color    = dim(mesh_color, 0.25)
        bright_color = lerp_color(mesh_color, (255, 255, 255), 0.3)

        locked_count = sum(1 for p in particles if p.locked)
        edge_reveal  = locked_count / len(LANDMARKS)   

        screen.fill((4, 6, 16))

        if edge_reveal > 0.1:
            tri_alpha = min(1.0, (edge_reveal - 0.1) / 0.5)
            tri_surf  = pygame.Surface((800, 600), pygame.SRCALPHA)
            for a, b, c in TRIANGLES:
                pa, pb, pc = particles[a], particles[b], particles[c]
                if pa.locked and pb.locked and pc.locked:
                    fill = (*dim_color, int(40 * tri_alpha))
                    pygame.draw.polygon(tri_surf, fill, [(pa.x, pa.y), (pb.x, pb.y), (pc.x, pc.y)])
            screen.blit(tri_surf, (0, 0))

        for i, j in FEATURE_EDGES:
            pa, pb = particles[i], particles[j]
            both_locked = pa.locked and pb.locked
            c = mesh_color if both_locked else dim(mesh_color, 0.4)
            w = 2 if both_locked else 1
            pygame.draw.line(screen, c, (int(pa.x), int(pa.y)), (int(pb.x), int(pb.y)), w)

        for p in particles:
            p.update(progress)
            node_c = bright_color if p.locked else dim(mesh_color, 0.6)
            p.draw(screen, node_c)

        for y in range(0, 600, 4):
            pygame.draw.line(screen, (0, 0, 0, 40), (0, y), (800, y))

        title = font_l.render("M.E.A  O S", True, mesh_color)
        screen.blit(title, (800 // 2 - title.get_width() // 2, 20))
        sub = font_s.render("Milla Environmental Access — Nexus Kingdom", True, dim(mesh_color, 0.6))
        screen.blit(sub, (800 // 2 - sub.get_width() // 2, 50))

        cpu, ram_pct, ram_used, ram_total = get_sys_stats()
        stats = [
            f"CPU  {cpu:5.1f}%",
            f"RAM  {ram_pct:5.1f}%  ({ram_used}M / {ram_total}M)",
            f"MESH {locked_count:3d} / {len(LANDMARKS)} nodes",
        ]
        for i, line in enumerate(stats):
            surf = font_s.render(line, True, dim(mesh_color, 0.7))
            screen.blit(surf, (18, 550 - (len(stats) - 1 - i) * 18))

        step_idx = min(int(progress * len(boot_steps)), len(boot_steps) - 1)
        for i, step in enumerate(boot_steps):
            done = (progress * len(boot_steps)) > i
            color = mesh_color if done else dim(mesh_color, 0.3)
            prefix = "▶ " if i == step_idx else ("✓ " if done else "  ")
            label = font_s.render(f"{prefix}{step}", True, color)
            screen.blit(label, (800 - label.get_width() - 18, 550 - (len(boot_steps) - 1 - i) * 18))

        bar_w = int(760 * min(progress, 1.0))
        pygame.draw.rect(screen, dim(mesh_color, 0.25), (20, 575, 760, 6))
        if bar_w > 0:
            pygame.draw.rect(screen, mesh_color, (20, 575, bar_w, 6))

        if progress >= 1.0:
            if finished_time is None: finished_time = time.time()
            elapsed = time.time() - finished_time
            if elapsed < 2.0:
                welcome = font_l.render("WELCOME HOME, ARCHITECT", True, bright_color)
                screen.blit(welcome, (800 // 2 - welcome.get_width() // 2, 300 - 11))
            else: running = False

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()

if __name__ == '__main__':
    print("[*] NEXUS BOOT: Neuro-Mesh Initialized...")
    shared_progress = Value('d', 0.0)
    p = Process(target=run_loading_animation, args=(shared_progress,))
    p.start()

    os.system("mpv --no-video --loop --volume=30 --msg-level=all=no --pulse-buffer=50 --cache=no --input-ipc-server=/tmp/mpv-socket -n --idle=yes > /dev/null 2>&1 &")

    boot_steps = ["Core OS", "Neuro Matrix", "Vocal Sync", "Relay Bridge", "Scout", "Mesh Connectivity"]
    for i, step in enumerate(boot_steps):
        time.sleep(1.5)
        shared_progress.value = (i + 1) / len(boot_steps)

    time.sleep(2)
    shared_progress.value = 1.1
    p.join()
    os.system("pkill mpv")
    print("Welcome home, Architect.")

    import subprocess
    project_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(project_dir, "venv", "bin", "python3")
    aio_script  = os.path.join(project_dir, "nexus_aio.py")

    display = os.environ.get("DISPLAY", "")
    launched = False

    if display:
        for term in ["lxterminal", "xterm", "gnome-terminal", "xfce4-terminal"]:
            try:
                if term == "gnome-terminal": cmd = [term, "--", venv_python, aio_script]
                else: cmd = [term, "-e", f"{venv_python} {aio_script}"]
                subprocess.Popen(cmd, cwd=project_dir)
                launched = True
                break
            except FileNotFoundError: continue

    if not launched:
        os.execv(venv_python, [venv_python, aio_script])
