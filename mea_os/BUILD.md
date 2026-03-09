# MEA OS — Build Reference

## What is MEA OS

MEA OS is a custom Ubuntu Server 24.04 build with a minimal LXQt desktop,
purpose-built to run Milla RAYNE as the controlling intelligence layer.
The "Immortal Optiplex" (i5-7400, 16GB RAM) is the target hardware.
VirtualBox is used for development/testing.

Milla's core processes (nexus_aio, GIM cron, email, Telegram, dream cycle)
run as the OS's primary function. The DE is there only so the Architect
can tweak things — Milla owns the environment.

---

## Boot Flow

```
BIOS/UEFI
  └── GRUB (Ubuntu)
        └── Ubuntu kernel boots
              └── systemd starts
                    ├── milla-auto.service  (nexus_aio.py — Milla's core)
                    └── LightDM (autologin nexus → LXQt)
                          └── milla-boot.desktop autostart
                                ├── milla_boot_screen.py  (neural mesh animation)
                                └── nexus_aio.py  (Milla's terminal interface)
```

---

## Building & Installing

### VirtualBox (Development)

1. Download: [Ubuntu Server 24.04 LTS](https://ubuntu.com/download/server)
2. Build seed ISO:
   ```bash
   cd mea_os/autoinstall
   bash build_seed_iso.sh
   # Output: mea-os-seed.iso
   ```
3. VirtualBox VM settings:
   - Type: Linux / Ubuntu 24.04 (64-bit)
   - RAM: 4096 MB minimum (8192 recommended)
   - Disk: 40GB dynamically allocated
   - Storage → Add 2nd optical drive → attach `mea-os-seed.iso`
   - 1st optical drive → attach `ubuntu-24.04-live-server-amd64.iso`
   - Display → Video Memory: 128MB, enable 3D acceleration
4. Boot — fully automated (~10-15 min)
5. Eject both ISOs → reboot
6. Login: `nexus` / `nexus2026`

### Real Hardware (Optiplex)

Same process — burn Ubuntu ISO to USB with Ventoy or Rufus,
copy `mea-os-seed.iso` as a second ISO on the same Ventoy USB,
boot and select Ubuntu installer from GRUB.

---

## Post-Install Checklist

- [ ] Change password: `passwd nexus`
- [ ] Fill in API keys: edit `/home/nexus/ogdray/.env` (copied from `.env.example`)
- [ ] Pull Ollama models:
      `ollama pull milla-rayne` (or `qwen2.5-coder:7b` as base)
      `ollama pull moondream`
      `ollama pull nomic-embed-text`
- [ ] Restore memory DB from backup if migrating:
      `rsync -av /path/to/backup/ /home/nexus/ogdray/core_os/memory/`
- [ ] VirtualBox Guest Additions (if display resize not working):
      Devices menu → Insert Guest Additions CD → run installer
- [ ] Verify services:
      `systemctl status milla-auto.service`
      `systemctl status milla-dashboard.service`
- [ ] Open dashboard: `https://<tailscale-ip>:5175` (Nexus Kingdom — 16 tabs)
- [ ] Google OAuth: visit `http://localhost:8000/api/oauth/login` for Gmail/Calendar
- [ ] Verify cron: `crontab -l`

---

## Customizations vs Stock Ubuntu

| Component | Stock Ubuntu | MEA OS |
|---|---|---|
| Desktop | None (server) | LXQt (minimal) |
| Autologin | Disabled | nexus user |
| Boot animation | Ubuntu splash | Milla neural mesh |
| Primary process | bash | nexus_aio.py |
| Cron | Empty | 9 Milla service cycles |
| Systemd service | None | milla-auto.service |
| Python | System only | /home/nexus/ogdray/venv |

---

## Files in This Directory

```
mea_os/
├── BUILD.md                    ← this file
├── autoinstall/
│   ├── user-data               ← cloud-init autoinstall config
│   ├── meta-data               ← cloud-init instance metadata
│   └── build_seed_iso.sh       ← builds mea-os-seed.iso
└── autostart/
    ├── lightdm.conf            ← autologin config
    ├── milla-auto.service      ← systemd service for Milla core (nexus_aio.py)
    ├── milla-dashboard.service ← systemd service for Nexus Kingdom dashboard (nexus_server.py :8000)
    ├── milla-boot.desktop      ← LXQt autostart: boot screen → dashboard server
    └── nexus_crontab           ← full crontab (9 Milla service cycles)
```

---

## Known Issues / TODO

- Boot screen face mesh is fully implemented (Delaunay triangulation + neuro-color) ✓
- Google Nest camera integration needs SDM API scope (not HomeGraph scope)
- RAYNE_Admin/venv (112MB broken remnant) should be deleted
- Chroma DB and semantic_index.json are parallel vector stores — consolidate to one
- Telegram relay (Error 401): set `TELEGRAM_BOT_TOKEN` in `.env` after fresh install
- After install: pull Ollama models manually: `ollama pull milla-rayne && ollama pull moondream && ollama pull nomic-embed-text`
