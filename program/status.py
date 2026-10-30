"""Program status: run every repo's test suite and print a table (markdown with --md).

    python -m program.status ~/Downloads/defence-projects [--md]
Each repo declares how it is tested by what it contains: go.mod -> go test; Makefile with a
'test' target -> make test; tests/ -> python -m unittest.
"""
import os
import subprocess
import sys
import time

REPOS = [
    # (repo, stage, area)
    ("sky-passive-radar-node", "In progress", "Flagship sensor: air"),
    ("water-passive-acoustic-vessel-monitor", "In progress", "Flagship sensor: water"),
    ("ground-seismic-perimeter-mesh", "In progress", "Flagship sensor: ground"),
    ("acoustic-drone-detector", "In progress", "Sensor: air"),
    ("thermal-sar-drone", "Built", "Robots & drones"),
    ("gps-denied-navigation-rover", "In progress", "Robots & drones"),
    ("rover-drive-stack", "In progress", "Robots & drones (convoy)"),
    ("airspace-deconfliction-manager", "In progress", "Airspace"),
    ("cold-soak-battery-rig", "In progress", "Cold & trust"),
    ("secure-fleet-updates", "In progress", "Cold & trust"),
    ("multi-domain-common-operating-picture", "In progress", "Ties it together"),
    ("counter-drone-sensor-fusion", "Simulation", "Software"),
    ("decision-black-box", "Simulation", "Software"),
    ("ddil-proof-devops", "Simulation", "Software"),
    ("zero-trust-air-gapped-supply-chain", "Simulation", "Software"),
    ("arctic-domain-awareness", "Simulation", "Software"),
    ("lentus-drone-mapping", "Simulation", "Software"),
    ("arctic-isr-drone", "Planned 2027", "Build guide"),
    ("gps-denied-cargo-ugv", "Planned 2027", "Build guide"),
    ("seabed-survey-boat", "Planned 2027", "Build guide"),
    ("counter-drone-scoring-harness", "Planned 2027", "Build guide"),
    ("secure-fleet-autonomy", "Planned 2027", "Build guide"),
    ("sovereign-ai-enclave", "Planned 2027", "Build guide"),
]


def cargo_crates(path):
    """Rust crates one level down (e.g. agent-rs/, dsp-rs/)."""
    return [os.path.join(path, d) for d in sorted(os.listdir(path)) if os.path.exists(os.path.join(path, d, "Cargo.toml"))]


def test_cmd(path):
    if os.path.exists(os.path.join(path, "go.mod")):
        return ["go", "test", "./..."]
    mk = os.path.join(path, "Makefile")
    if os.path.exists(mk) and "\ntest:" in "\n" + open(mk).read():
        return ["make", "-s", "test"]
    if os.path.isdir(os.path.join(path, "tests")):
        return [sys.executable, "-m", "unittest", "-q"]
    return None


def run(root):
    rows = []
    for repo, stage, area in REPOS:
        p = os.path.join(root, repo)
        if not os.path.isdir(p):
            rows.append((repo, stage, area, "missing", 0.0))
            continue
        cmd = test_cmd(p)
        if not cmd:
            rows.append((repo, stage, area, "no tests", 0.0))
            continue
        t0 = time.time()
        runs = [(cmd, p)] + [(["cargo", "test", "-q", "--release"], c) for c in cargo_crates(p)]
        ok = True
        for c, cwd in runs:
            r = subprocess.run(c, cwd=cwd, capture_output=True, text=True)
            if r.returncode:
                ok = False
                print(f"--- {repo} ({' '.join(c)}) ---\n{(r.stdout + r.stderr)[-1500:]}", file=sys.stderr)
        label = "pass" if ok else "FAIL"
        if len(runs) > 1:
            label += f" (+{len(runs) - 1} rust)"
        rows.append((repo, stage, area, label, time.time() - t0))
    return rows


def main():
    root = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else os.path.dirname(os.getcwd())
    rows = run(root)
    md = "--md" in sys.argv
    if md:
        print("| Repo | Stage | Area | Tests |\n|---|---|---|---|")
    for repo, stage, area, res, dt in rows:
        print(f"| {repo} | {stage} | {area} | {res} |" if md else f"{res:8s} {dt:5.1f}s  {repo:42s} {stage:13s} {area}")
    sys.exit(any(r[3].startswith("FAIL") for r in rows))


if __name__ == "__main__":
    main()
