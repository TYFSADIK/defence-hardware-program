# Defence Hardware Program (index)

Private research repo. The self-funded Canadian defence hardware program: passive radar, a hydrophone vessel monitor, a seismic mesh, GPS-denied rovers, a thermal SAR drone, and fleet updates. This repo is the **map**. Every build lives in its own private repository.

Full write-up (requirement sources: DDI, MINERVA, DRDC/NANOOK, NRC + DRDC counter-drone, airspace deconfliction): [`docs/project-page.md`](docs/project-page.md)

## How the builds connect

```
          SENSORS                                FUSION & DECISION                 TRUST LAYER
 sky-passive-radar-node ──┐
 acoustic-drone-detector ─┤                                                ┌─ decision-black-box
 water-...-vessel-monitor ┼── signed Detection ──> multi-domain-COP ──────┤   (every operator action)
 ground-seismic-mesh ─────┘   (interfaces/)         │       │              └─ secure-fleet-autonomy
                                                    │       └─ counter-drone-sensor-fusion        (MAVLink signing, IDS)
 thermal-sar-drone, lentus-drone-mapping ── map ────┘          └─ scored by counter-drone-scoring-harness
 gps-denied-navigation-rover, rover-drive-stack, gps-denied-cargo-ugv, seabed-survey-boat  (platforms)
 airspace-deconfliction-manager (who is flying where)
 cold-soak-battery-rig ──> data for arctic-isr-drone / every winter build
 secure-fleet-updates + ddil-proof-devops + zero-trust-air-gapped-supply-chain  (how code reaches the fleet)
 arctic-domain-awareness, sovereign-ai-enclave  (data and analysis)
```

## Repos

| Repo | Main language | Stage |
|---|---|---|
| [sky-passive-radar-node](https://github.com/TYFSADIK/sky-passive-radar-node) | Python (NumPy DSP) | In progress |
| [water-passive-acoustic-vessel-monitor](https://github.com/TYFSADIK/water-passive-acoustic-vessel-monitor) | Python | In progress |
| [ground-seismic-perimeter-mesh](https://github.com/TYFSADIK/ground-seismic-perimeter-mesh) | C++ (ESP32) + Python | In progress |
| [acoustic-drone-detector](https://github.com/TYFSADIK/acoustic-drone-detector) | Python | In progress |
| [thermal-sar-drone](https://github.com/TYFSADIK/thermal-sar-drone) | Python | Built |
| [gps-denied-navigation-rover](https://github.com/TYFSADIK/gps-denied-navigation-rover) | C++ (ROS 2) + Python | In progress |
| [rover-drive-stack](https://github.com/TYFSADIK/rover-drive-stack) (convoy) | C++ (ESP32) | In progress |
| [airspace-deconfliction-manager](https://github.com/TYFSADIK/airspace-deconfliction-manager) | Python | In progress |
| [cold-soak-battery-rig](https://github.com/TYFSADIK/cold-soak-battery-rig) | Python + C++ (ESP32) | In progress |
| [secure-fleet-updates](https://github.com/TYFSADIK/secure-fleet-updates) | Go | In progress |
| [multi-domain-common-operating-picture](https://github.com/TYFSADIK/multi-domain-common-operating-picture) | Python | In progress |
| [counter-drone-sensor-fusion](https://github.com/TYFSADIK/counter-drone-sensor-fusion) | Python | Simulation |
| [decision-black-box](https://github.com/TYFSADIK/decision-black-box) | Go | Simulation |
| [ddil-proof-devops](https://github.com/TYFSADIK/ddil-proof-devops) | Go | Simulation |
| [zero-trust-air-gapped-supply-chain](https://github.com/TYFSADIK/zero-trust-air-gapped-supply-chain) | Go | Simulation |
| [arctic-domain-awareness](https://github.com/TYFSADIK/arctic-domain-awareness) | Python | Simulation |
| [lentus-drone-mapping](https://github.com/TYFSADIK/lentus-drone-mapping) | Python | Simulation |
| [arctic-isr-drone](https://github.com/TYFSADIK/arctic-isr-drone) | Python | Planned 2027 |
| [gps-denied-cargo-ugv](https://github.com/TYFSADIK/gps-denied-cargo-ugv) | Python | Planned 2027 |
| [seabed-survey-boat](https://github.com/TYFSADIK/seabed-survey-boat) | Python | Planned 2027 |
| [counter-drone-scoring-harness](https://github.com/TYFSADIK/counter-drone-scoring-harness) | Python | Planned 2027 |
| [secure-fleet-autonomy](https://github.com/TYFSADIK/secure-fleet-autonomy) | Python | Planned 2027 |
| [sovereign-ai-enclave](https://github.com/TYFSADIK/sovereign-ai-enclave) | Python | Planned 2027 |

## Run every test suite

```bash
./scripts/setup-dev.sh                 # once
python -m program.status .. --md       # from this repo, with all repos cloned side by side
```
