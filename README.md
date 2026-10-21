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
- only talks to endpoints you explicitly configure: the **BYD cloud** for the native BYD
  view and, optionally, your own **Home Assistant**, **evcc**, and devices on the private LAN.

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

## Your car in 3D

Instead of a silhouette the cockpit shows your model in 3D: the same models as in Panoptes, in your paint colour
(colour buttons below the car). The model (~1 MB) is downloaded once from the community server, checked by checksum
and stored on your computer. Your own photo takes precedence. Models partly by Nazh Design (CC BY 4.0), partly built by the Panoptes project (CC0); details under "About".

## Where does the data come from? You choose

Right in the second step of the wizard, the cockpit asks where to get your car's values from:

- **BYD account:** via the BYD cloud, with a separate second account (see above). Easiest for most people.
- **Home Assistant:** your car is already there, e.g. via a BYD integration or Panoptes. Enter the address and an
  access token and press "Find my car". The cockpit suggests charge level, range, odometer, charging and location
  itself; you only confirm. It only reads, and then **never** additionally asks the BYD cloud (two pollers on one
  account disturb each other, error 6024).
- **Panoptes in the car:** directly from the Panoptes app on the infotainment system (see below).

With Home Assistant or Panoptes a BYD account is only **optional**, for remote commands such as pre-conditioning.

## Home Assistant (optional)

Enable it under "Extras" in the wizard. Your car then appears in Home Assistant on its own
(MQTT discovery) — with all values and buttons. Needs an MQTT broker (usually the Mosquitto
add-on in HA). If you have a PV system in HA, you can show your solar output next to state
of charge and electricity price — **read-only**.

## Chargers, solar systems and other vehicles (optional)

The cockpit reads the vendor-neutral local API provided by [evcc](https://evcc.io/).
This makes every charger, grid/solar/battery meter and vehicle configured in evcc
available independent of brand—for example go-e, BYD, VW or Audi.

**Control (only if you want it):** by default the cockpit only reads. Per charge point you can tap
"Allow control". The cockpit may then change exactly two things via evcc: the **charge mode**
(off / now / min+PV / PV) and the **charge limit**. After every change it reads back from evcc and shows
whether it was applied. Everything else (phases, current, protection) stays with evcc. go-e and Shelly
are only ever read directly, never switched.

Hardware without a built-in evcc adapter can be configured as a **user-defined device**
using local HTTP, MQTT or Modbus. This is also the honest route for Tuya-based devices:
they need a documented local interface or a local bridge such as Home Assistant/MQTT.
A proprietary cloud-only product cannot safely be claimed as universally supported.

Enter the private IPv4 address and port (normally 7070) of the evcc server in the
cockpit. For safety, only RFC 1918 addresses (`10/8`, `172.16/12`, `192.168/16`) are
accepted and HTTP redirects are not followed.

Vehicle profiles are stored in `~/.evcockpit/vehicles.json`. The local
`POST /vehicles/profiles` API accepts `{"profiles": [...]}`; credentials are discarded
and never stored in these profiles.

## Data directly from Panoptes in the car (optional)

If the Panoptes app (formerly SurfMate) runs in the car, the cockpit reads charge level, mileage, location,
gear, lock state and outside temperature directly from it (home network or Tailscale, port 8180) — every
minute, without loading the BYD cloud. Enter the car address and the pairing code from the app in the
wizard; "Test connection" shows right away whether it works. If the car is off or unreachable, the cockpit
asks the BYD cloud as before. **Controls (climate, lock, charging) still go through the BYD cloud.**

**Remote commands only when the car is switched off:** before every command the cockpit freshly checks
(via Panoptes or the BYD cloud) that the car is off. If it is on, not in P, or its state is unclear, the
command is not sent. Reason: a cloud command can switch off a car that is running.

## BYD community route planner (optional)

Members of the [BYD community map](https://byd.serveone.at) get a personal route-planner link
(`byd.serveone.at/ev/#z=…`). Pasted into the setup wizard:

- **Charge level to the planner:** the planner then knows your car's starting charge level. Only the latest
  value is sent, no location, and only while the car is awake.
- **Learn real consumption** (separate tick): your trips stay on your computer. After each trip without
  charging the cockpit only asks the planner for its model value (distance, duration, outside temperature;
  nothing is stored there), computes your correction factor and sends **only that single number**.
- If **Panoptes is paired in the car**, Panoptes reports charge level and factor itself and the cockpit
  sends nothing (one source per car). Every report carries a random vehicle id, never the VIN.
- The cockpit shows a **"Plan a route"** button: it opens the same planner as `byd.serveone.at/ev/` with your
  login right inside the cockpit. Routes, vehicles and "Send to car" are the same as there. The start page shows
  the route that is ready (distance, charging stops, arrival) and the **feedback from the car** ("arrived in the
  car", "navigation running"). The route reaches the car via Panoptes; without Panoptes via the planner's phone
  link. The link key stays on your computer and is never part of the page.
- **💳 My charging cards:** under "Route planner" you tick which charging cards you have. The list is stored by
  the planner (only which cards, no charging sessions) and applies on `/ev/` too. Chargers on the map then show
  your card's price, and the planner prefers matching charging stops.

**Map:** by default the cockpit shows the same map as the planner and the Panoptes app (served by the community
server, byd.serveone.at); until that server delivers it completely, OpenStreetMap. Untick "Community map style"
for OpenStreetMap always. The map libraries (MapLibre, PMTiles) ship in the package, no CDN.
With "Chargers" ticked, the community map shows **live occupancy** (currently Austria, Switzerland and Germany, via the planner; source and licence are shown at the bottom of the map): free
normal, occupied **red**, out of order grey, status unknown grey with "?" (source shown at the bottom of the map). Only the map centre rounded to ~5 km is sent to the planner by POST
(no access log), at most every 2 minutes per area.

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

- Native vehicle control is **tested on a single BYD**. Other vehicles are displayed
  read-only through evcc; available data depends on the corresponding adapter. Feedback ([issues](../../issues))
  very welcome.
- Controlling charge points via evcc (mode, charge limit) has so far only been tested against a simulated
  evcc, not yet on a real charger.
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
