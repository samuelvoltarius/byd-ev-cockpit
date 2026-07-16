# EV-Cockpit

*🇬🇧 English · [🇩🇪 Deutsch](README.de.md)*

**A small dashboard for your BYD — runs on your own computer. Your car data stays
with you and is sent to no one.**

State of charge with an honest range estimate (calculated from your *actual* consumption,
not the flattering factory figure), pre-conditioning, battery preheat, seat heating, find
car, tyre-pressure warning, chargers on a map, electricity price — and optionally wired
into your Home Assistant. A wizard walks you through the setup in five steps.

> The interface is **bilingual — English and German**. It follows your browser's language
> automatically, and there's a 🌐 toggle in the corner to switch anytime.

Built and tested on exactly **one** car (a BYD Dolphin Surf). For other models the tool
asks your car what it can do and shows only that. If something doesn't work as expected,
please [open an issue](../../issues) — it helps everyone else.

---

## "Does my data really stay with me?" — that's why the code is open

This tool asks for your BYD cloud login. That's a matter of trust, and "trust me" isn't
enough. So the **full source is here in the open**: you (or someone you trust) can read
that the program

- stores your credentials **locally only** (`~/.evcockpit/` on your machine),
- sends **nothing** to the author or any website,
- talks to exactly **two** endpoints: the **BYD cloud** (your car) and — only if you turn
  it on — **your own Home Assistant**.

There is exactly **one** optional, **off-by-default** exception: an anonymous install ping
(only "someone installed it" + model, **no** IP, **no** vehicle, **no** identifier) that
you can allow with a checkbox in the wizard. Search the code for `PING_URL` — nothing more
than that leaves your machine.

**Please create a second BYD account for this tool** and add it to the car as a secondary
user in the BYD app. That way you don't hand over your main credentials, and you can revoke
access at any time.

---

## Getting started

### Windows
1. Download the ready-made package: **[Releases](../../releases)** → `ev-cockpit-windows.zip`
2. Unzip, double-click `Start.bat`.
3. Your browser opens on its own. If not: <http://127.0.0.1:8099>

Python is bundled in the Windows package — you don't install anything.

### Linux / macOS / Raspberry Pi
```bash
git clone https://github.com/samuelvoltarius/byd-ev-cockpit.git
cd byd-ev-cockpit
./start.sh
```
On first run `start.sh` creates its own environment in the folder (`.venv/`) and installs
the BYD library into it — your system stays untouched. If the venv package is missing on
Debian/Ubuntu/Raspberry Pi, the script tells you the exact `apt` command.

Then open <http://127.0.0.1:8099> in your browser.

---

## Home Assistant (optional)

Enable it under "Extras" in the wizard. Your car then appears in Home Assistant on its own
(MQTT discovery) — with all values and buttons. Needs an MQTT broker (usually the Mosquitto
add-on in HA). If you have a PV system in HA, you can show your solar output next to state
of charge and electricity price — **read-only**.

## Two cars

Start a second instance with its own config folder and port:
```bash
EVCOCKPIT_CFGDIR=~/.evcockpit-second EVCOCKPIT_PORT=8100 ./start.sh
```

## Settings (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `EVCOCKPIT_PORT` | `8099` | Port of the cockpit |
| `EVCOCKPIT_BIND` | `127.0.0.1` | Your machine only. For LAN access set to `0.0.0.0`. |
| `EVCOCKPIT_CFGDIR` | `~/.evcockpit` | Where config and credentials live |

---

## Requirements

- A BYD with cloud connectivity (a BYD app account).
- Python 3.10+ (Linux/Mac); the Windows package bundles it.
- Stands on the shoulders of [**pyBYD**](https://pypi.org/project/pybyd/) — without that
  library this wouldn't exist.

## Limitations — honestly

- **Tested on a single car.** Other BYD models: untested. Feedback ([issues](../../issues))
  very welcome.
- The Dolphin Surf has **no cabin temperature sensor** — so no inside temperature and no
  thermostat. Climate is switched to a target temperature, not regulated.
- **There is deliberately no unlock button.** A button in a browser that opens your car
  would be a burglary tool for anyone with access to your computer. Locking is harmless and
  is included.
- If a command doesn't go through: wait a moment and try **once** more — not frantically
  several times, the BYD cloud doesn't like that.

## Liability

Free, non-commercial community project, built in spare time, **with no warranty whatsoever** —
see [LICENSE](LICENSE). Use at your own risk. Not an official BYD product and in no way
affiliated with BYD. "BYD" is a trademark of its respective owners.

## Questions & bugs

Please [open an issue](../../issues) — that's the best way to reach the maintainer, and it
helps everyone else too.
