import csv
import re
from pathlib import Path
from statistics import mean, stdev

stderr_path = Path("results/raw/groth16_profile_labeled_stderr.txt")
stdout_path = Path("results/raw/groth16_profile_labeled_stdout.txt")

stderr_lines = [x.strip() for x in stderr_path.read_text().splitlines() if x.strip()]
stdout_lines = [x.strip() for x in stdout_path.read_text().splitlines() if x.strip()]

run_re = re.compile(
    r"steps=(\d+),run=(\d+),seed=(\d+),setup_ms=(\d+),prove_ms=(\d+),verify_ms=(\d+),valid=(true|false)"
)

msm_re = re.compile(
    r"ZK3D_PROFILE,MSM,([^,]+),points=(\d+),scalars=(\d+)"
)

fft_re = re.compile(
    r"ZK3D_PROFILE,(FFT|IFFT),([^,]+),elements=(\d+)"
)

runs = []
for line in stdout_lines:
    m = run_re.fullmatch(line)
    if not m:
        raise RuntimeError(f"Unparsed stdout line: {line}")
    steps, run_id, seed, setup_ms, prove_ms, verify_ms, valid = m.groups()
    runs.append({
        "steps": int(steps),
        "run_id": int(run_id),
        "seed": int(seed),
        "setup_ms": int(setup_ms),
        "prove_ms": int(prove_ms),
        "verify_ms": int(verify_ms),
        "valid": valid == "true",
    })

if not all(r["valid"] for r in runs):
    raise RuntimeError("At least one proof failed verification.")

# Each proving run currently emits exactly:
# 7 FFT/IFFT records + 5 MSM records = 12 profile records.
records_per_run = 12

if len(stderr_lines) != len(runs) * records_per_run:
    raise RuntimeError(
        f"Expected {len(runs) * records_per_run} profile records, got {len(stderr_lines)}"
    )

msm_rows = []
fft_rows = []

for i, run in enumerate(runs):
    block = stderr_lines[i * records_per_run:(i + 1) * records_per_run]

    for line in block:
        m = msm_re.fullmatch(line)
        if m:
            label, points, scalars = m.groups()
            points = int(points)
            scalars = int(scalars)
            effective_pairs = min(points, scalars)

            msm_rows.append({
                "steps": run["steps"],
                "run_id": run["run_id"],
                "label": label,
                "points_supplied": points,
                "scalars_supplied": scalars,
                "effective_pairs": effective_pairs,
            })
            continue

        m = fft_re.fullmatch(line)
        if m:
            direction, label, elements = m.groups()
            fft_rows.append({
                "steps": run["steps"],
                "run_id": run["run_id"],
                "direction": direction,
                "label": label,
                "elements": int(elements),
            })
            continue

        raise RuntimeError(f"Unparsed profile line: {line}")

with open("results/msm_detail.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=msm_rows[0].keys())
    w.writeheader()
    w.writerows(msm_rows)

with open("results/fft_detail.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fft_rows[0].keys())
    w.writeheader()
    w.writerows(fft_rows)

summary_rows = []

for steps in sorted({r["steps"] for r in runs}):
    rset = [r for r in runs if r["steps"] == steps]
    mset = [r for r in msm_rows if r["steps"] == steps]
    fset = [r for r in fft_rows if r["steps"] == steps]

    per_run_msm_pairs = []
    per_run_fft_elements = []

    for r in rset:
        rid = r["run_id"]
        per_run_msm_pairs.append(
            sum(x["effective_pairs"] for x in mset if x["run_id"] == rid)
        )
        per_run_fft_elements.append(
            sum(x["elements"] for x in fset if x["run_id"] == rid)
        )

    if len(set(per_run_msm_pairs)) != 1:
        raise RuntimeError(f"MSM counts differ across repeated runs for steps={steps}")

    if len(set(per_run_fft_elements)) != 1:
        raise RuntimeError(f"FFT counts differ across repeated runs for steps={steps}")

    prove_times = [r["prove_ms"] for r in rset]

    summary_rows.append({
        "proof_system": "Groth16",
        "steps": steps,
        "runs": len(rset),
        "msm_calls_per_run": len(mset) // len(rset),
        "msm_effective_pairs_per_run": per_run_msm_pairs[0],
        "fft_ifft_calls_per_run": len(fset) // len(rset),
        "fft_ifft_elements_per_run": per_run_fft_elements[0],
        "prove_ms_mean": round(mean(prove_times), 3),
        "prove_ms_std": round(stdev(prove_times), 3) if len(prove_times) > 1 else 0.0,
        "prove_ms_min": min(prove_times),
        "prove_ms_max": max(prove_times),
        "all_valid": True,
    })

with open("results/workload_summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
    w.writeheader()
    w.writerows(summary_rows)

print("Wrote:")
print("  results/msm_detail.csv")
print("  results/fft_detail.csv")
print("  results/workload_summary.csv")
