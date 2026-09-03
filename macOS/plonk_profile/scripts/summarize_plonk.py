import csv
import re
from pathlib import Path
from statistics import mean, stdev

runtime_re = re.compile(r"ZK3D_RUNTIME,prove_ms=(\d+)")
fft_re = re.compile(r"ZK3D_PROFILE,(FFT|IFFT),elements=(\d+)")
msm_re = re.compile(
    r"ZK3D_PROFILE,MSM,KZG_COMMIT,bases=(\d+),scalars=(\d+)"
)

runs = []

for run_id in [1, 2, 3]:
    stdout_path = Path(
        f"results/raw/plonk_profile_run{run_id}_stdout.txt"
    )
    stderr_path = Path(
        f"results/raw/plonk_profile_run{run_id}_stderr.txt"
    )

    stdout = stdout_path.read_text()
    stderr = stderr_path.read_text().splitlines()

    m = runtime_re.search(stdout)
    if not m:
        raise RuntimeError(f"Missing runtime in run {run_id}")

    prove_ms = int(m.group(1))

    fft_rows = []
    msm_rows = []

    for line in stderr:
        line = line.strip()

        m = fft_re.fullmatch(line)
        if m:
            direction, elements = m.groups()

            fft_rows.append({
                "run_id": run_id,
                "direction": direction,
                "elements": int(elements),
            })
            continue

        m = msm_re.fullmatch(line)
        if m:
            bases, scalars = map(int, m.groups())

            msm_rows.append({
                "run_id": run_id,
                "bases_supplied": bases,
                "scalars_supplied": scalars,
                "effective_pairs": min(bases, scalars),
            })

    runs.append({
        "run_id": run_id,
        "prove_ms": prove_ms,
        "fft_rows": fft_rows,
        "msm_rows": msm_rows,
    })


# Check that all three runs have identical algorithmic signatures.

fft_signatures = [
    [(x["direction"], x["elements"]) for x in r["fft_rows"]]
    for r in runs
]

msm_signatures = [
    sorted(
        (
            x["bases_supplied"],
            x["scalars_supplied"],
            x["effective_pairs"],
        )
        for x in r["msm_rows"]
    )
    for r in runs
]

if not all(sig == fft_signatures[0] for sig in fft_signatures):
    raise RuntimeError("FFT workload differs across runs")

if not all(sig == msm_signatures[0] for sig in msm_signatures):
    raise RuntimeError("MSM workload differs across runs")


all_fft = [x for r in runs for x in r["fft_rows"]]
all_msm = [x for r in runs for x in r["msm_rows"]]


with open("results/plonk_fft_detail.csv", "w", newline="") as f:
    w = csv.DictWriter(
        f,
        fieldnames=["run_id", "direction", "elements"]
    )
    w.writeheader()
    w.writerows(all_fft)


with open("results/plonk_msm_detail.csv", "w", newline="") as f:
    w = csv.DictWriter(
        f,
        fieldnames=[
            "run_id",
            "bases_supplied",
            "scalars_supplied",
            "effective_pairs",
        ],
    )
    w.writeheader()
    w.writerows(all_msm)


fft_per_run = runs[0]["fft_rows"]
msm_per_run = runs[0]["msm_rows"]

fft_elements_per_run = sum(
    x["elements"] for x in fft_per_run
)

msm_pairs_per_run = sum(
    x["effective_pairs"] for x in msm_per_run
)

prove_times = [r["prove_ms"] for r in runs]


summary = {
    "proof_system": "PLONK-KZG",
    "runs": len(runs),
    "fft_ifft_calls_per_run": len(fft_per_run),
    "fft_ifft_elements_per_run": fft_elements_per_run,
    "msm_calls_per_run": len(msm_per_run),
    "msm_effective_pairs_per_run": msm_pairs_per_run,
    "prove_ms_mean": round(mean(prove_times), 3),
    "prove_ms_std": round(stdev(prove_times), 3),
    "prove_ms_min": min(prove_times),
    "prove_ms_max": max(prove_times),
}

with open(
    "results/plonk_workload_summary.csv",
    "w",
    newline=""
) as f:
    w = csv.DictWriter(
        f,
        fieldnames=summary.keys()
    )
    w.writeheader()
    w.writerow(summary)


print("Wrote:")
print("  results/plonk_fft_detail.csv")
print("  results/plonk_msm_detail.csv")
print("  results/plonk_workload_summary.csv")
