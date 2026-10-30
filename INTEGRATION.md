# Program Integration Guide: From Bench to Field

How all 23 builds physically and logically connect, and the order to build them in.
Every per-build `HARDWARE.md` assumes the shared infrastructure on this page already exists.

---

## 1. The physical picture

```
                                   HOMELAB / BASE STATION
   ┌──────────────────────────────────────────────────────────────────────────────────┐
   │  Broker Pi 5 (broker.lan, NVMe)          Homelab k8s cluster        Offline laptop │
   │   • Mosquitto (TLS, ACLs)                 • COP dashboard            • YubiKeys    │
   │   • COP tracker + evidence log            • Harbor registry          • release     │
   │   • chrony stratum-1  <── u-blox M9N PPS  • fleet server (OTA)         signing     │
   │   • decision-black-box (key in TPM)       • Grafana/Loki                           │
   └───────────────┬───────────────────────────────┬──────────────────────────────────┘
                   │ gigabit switch (VLANs)         │
     ┌─────────────┼────────────────┬──────────────┼─────────────────┬─────────────────┐
     │ VLAN 20 SENSORS              │ VLAN 30 FLEET (robots/drones)   │ VLAN 10 MGMT    │
     │                              │                                 │ (SSH, laptops)  │
 Sky node (mini PC)          Rover Pi 5 ×2  (Wi-Fi AP / mesh)          
  KrakenSDR + RTL-SDR        Drone companion Pi 5 (via ELRS + Wi-Fi)   
 Acoustic node (Pi 5)        Boat Pi (Wi-Fi / LTE + WireGuard)          
 Water node (Pi 5, solar) ── WireGuard over LTE/Wi-Fi when off-site     
 Seismic gateway Pi ── LoRa 915 MHz ── 5× ESP32 seismic nodes (solar)   
```

Rules:
1. **Sensors never talk to each other.** Everything goes node → MQTT → COP. A dead node can't take down another one.
2. **Field nodes reach home only through WireGuard.** The broker is never exposed to the internet.
3. **Motor power and logic power never share a rail** on any vehicle (see each rover/drone guide).
4. **Every node buffers locally** (SQLite or ring buffer) and replays when the link returns. Nothing assumes the network is up.

## 2. Network

| VLAN | Subnet (example) | Who | Allowed to reach |
|---|---|---|---|
| 10 MGMT | 10.10.10.0/24 | laptops, SSH | everything (admin) |
| 20 SENSORS | 10.10.20.0/24 | sky, acoustic, water, seismic gateway | broker.lan:8883 (MQTT/TLS), broker.lan:123 (NTP) only |
| 30 FLEET | 10.10.30.0/24 | rovers, drone companion, boat | broker.lan:8883, fleet server :443, Harbor :443 |
| WireGuard | 10.99.0.0/24 | off-site nodes | same rules as their home VLAN |

OpenWrt router: one firewall zone per VLAN, default **deny** between zones, with explicit allow rules above. Give each node a static DHCP lease by MAC so node IDs never move.

## 3. Time: the thing fusion depends on

```
u-blox M9N ── PPS → broker Pi GPIO18, NMEA → UART0 (38400)
broker Pi: gpsd + chrony with refclock PPS  →  stratum 1 for the LAN
every Pi / mini PC: chrony "server broker.lan iburst"  (check: chronyc tracking, offset < 1 ms)
ESP32 nodes: no RTC; gateway stamps receive time (UTC) and maps node uptime → UTC per node
```

`/boot/firmware/config.txt` on the broker: `enable_uart=1` and `dtoverlay=pps-gpio,gpiopin=18`.
`/etc/chrony/chrony.conf`:
```
refclock SHM 0 refid NMEA offset 0.2 noselect
refclock PPS /dev/pps0 lock NMEA refid PPS prefer
allow 10.10.0.0/16
```
The COP's `ClockMonitor` catches any node that drifts or jumps anyway (Run T5).

## 4. Coordinates: one site frame

All detections use **site ENU metres** (east, north) from one surveyed origin. This is what `Detection.e/.n` means.
1. Pick a fixed origin (a survey nail or a corner post). Average the M9N fix there for 30 min and record the lat/lon/alt in `site.json`.
2. Survey **every fixed sensor** the same way (10 min average each) and record it in `site.json`.
3. Each node converts its own measurement (a bearing, a bistatic range, a seismic cell) into site ENU before signing.
4. Vehicles publish ENU from their EKF, aligned at startup by driving over two surveyed points.

```json
{"origin": {"lat": 45.0000000, "lon": -75.0000000, "alt": 70.0},
 "nodes": {"acoustic-1": {"e": 12.4, "n": -3.1, "up": 2.0, "mic0_az_deg": 90.0},
           "seis-1": {"e": 80.0, "n": 15.0}, "sky-1": {"e": 0.0, "n": 0.0, "ref_az_deg": 212.0}}}
```

## 5. Messaging (MQTT topic map)

| Topic | Publisher | Payload | Consumer |
|---|---|---|---|
| `cop/detections/air/<node>` | sky, acoustic, thermal drone | signed `Detection` ([schema](interfaces/detection.schema.json)) | COP |
| `cop/detections/ground/<node>` | seismic gateway (one per node) | signed `Detection` | COP |
| `cop/detections/water/<node>` | water node | signed `Detection` | COP |
| `cop/air/tracks` | airspace manager | own drone tracks | COP (blue-force layer) |
| `fleet/<id>/telemetry` | rovers, drone, boat | position, battery, mode | COP, fleet server |
| `fleet/<id>/ota` | fleet server | campaign notices | OTA agent |
| `audit/decisions` | COP, airspace manager | operator actions | decision-black-box |

Mosquitto: TLS on 8883 only, a client certificate per node (CN = node id), and an ACL so a node can only **publish** to its own topic:
```
pattern write cop/detections/+/%c
pattern write fleet/%c/telemetry
user cop
topic read cop/#
```

## 6. Keys and trust

| Key | Lives in | Used for |
|---|---|---|
| Node Ed25519 key (one per node) | node, `chmod 600`, generated on the device | signing `Detection` messages, with the public key in the COP `registry.json` |
| MQTT client cert | node | TLS to the broker (a small CA: `step-ca` on the homelab) |
| Seismic mesh HMAC key | ESP32 `node_secrets.h` (never committed), gateway | LoRa packet authentication |
| MAVLink signing key | drone FC + GCS | `secure-fleet-autonomy` |
| Release signing key | **YubiKey**, offline laptop only | OTA manifests, firmware images, air-gap attestations |
| Black-box key | broker Pi TPM | audit log signatures and checkpoints |

Rotating a node: generate a new key on the node, update the registry, revoke the old certificate, and log both steps in decision-black-box.

## 7. Power

| Node | Supply | Budget note |
|---|---|---|
| Broker Pi, sky mini PC | mains + small UPS | graceful shutdown on UPS low (`nut`) |
| Acoustic / water / seismic gateway | official 27 W supply, or 12 V LiFePO4 + 30-50 W solar + MPPT + 5.1 V buck | size for **grey Canadian weeks**: 3 days with no sun |
| Seismic ESP32 nodes | 18650 + small panel + charge board | deep sleep when quiet |
| Rovers | Li-ion + BMS, **split motor and logic rails**, e-stop on the motor rail | |
| Drone | 4S LiPo, separate 5 V/5 A BEC for the Pi | never power the Pi from the FC USB |

## 8. Build order (what to do first)

| Step | Build | Why this order | Done when |
|---|---|---|---|
| 0 | Workshop, network, **broker Pi + PPS time**, MQTT with TLS | every later step depends on it | `chronyc tracking` < 1 ms; a test client publishes over TLS |
| 1 | **COP** (`multi-domain-common-operating-picture`) with the demo feeder | the place every sensor reports to | dashboard shows demo tracks |
| 2 | **decision-black-box** on the broker | audit from day one | `blackbox verify` OK |
| 3 | **Sky ADS-B truth** (RTL-SDR + readsb) | truth data piles up for weeks before radar exists | tar1090 map is live |
| 4 | Acoustic node, then water node, then seismic mesh | cheapest first, each emits `Detection` | each shows on the COP |
| 5 | KrakenSDR passive radar | hardest RF build, and ADS-B truth is ready to score it | Pd vs ADS-B reported |
| 6 | GPS-denied rover, then convoy | shared chassis, ROS 2 | drift and blackout runs done |
| 7 | Cold-soak rig | before any winter flight or drive | capacity vs temperature curves |
| 8 | Thermal SAR drone | needs Transport Canada certification | surveyed-volunteer detection test |
| 9 | Trust layer: secure-fleet-updates, secure-fleet-autonomy, DDIL, supply chain | once there's a fleet to protect | OTA campaign plus a rollback rehearsal |
| 10 | Fusion and scoring: counter-drone fusion and harness on **real** feeds | needs real detections | GOSPA on a recorded day |
| 2027 | Build guides: ISR drone, cargo UGV, seabed boat, enclave | | per guide |

## 9. End-to-end field exercise (the integration test)

1. **Setup:** sky node, acoustic node, and seismic mesh deployed and surveyed; COP and black box running; `chronyc` OK on every node.
2. **Event:** your own drone flies a planned route (logged ArduPilot `.bin` = truth). A volunteer walks the perimeter (phone GPS track = truth). A vehicle drives the access road.
3. **Expect on the COP:** one air track (radar plus acoustic bearing fused), one ground "footsteps" track, one vehicle track, each keeping a single ID.
4. **Operator:** classifies each track. Every click goes to decision-black-box.
5. **After:** replay the black box, score with `counter-drone-scoring-harness` against truth, and log Pd, false alarms per hour, time to detect, and position error per sensor.
6. **Chaos round:** pull the WAN, power-cycle the seismic gateway, and shift one node's clock. Then confirm replay, the skew alert, and that track continuity holds.

## 10. Legal and safety checklist (Canada)

- **Radio:** receive-only builds (sky, acoustic, water AIS) need no licence. LoRa 915 MHz must stay inside **ISED RSS-247** limits. Intercepting private communications is a Criminal Code offence, so record broadcast and AIS signals only.
- **Drones:** Transport Canada **Part IX**. Get the pilot certificate (basic or advanced) and register drones over 250 g. No flights over people without advanced operations. Get landowner permission.
- **Export controls:** passive radar processing (and possibly other sensor code) may be on the **Export Control List**. Keep those repos private and ask Global Affairs Canada before publishing anything.
- **Batteries:** charge LiPos in a bag on a non-flammable surface, keep an ABC extinguisher on the bench, and never leave a cold-soak run unattended.
- **People:** get consent from volunteers in thermal or acoustic test data, and delete raw data you don't need.
