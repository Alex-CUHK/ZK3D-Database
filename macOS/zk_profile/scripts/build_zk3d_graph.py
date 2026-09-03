import csv
import json
from pathlib import Path

FR = 32
G1 = 48
G2 = 96

msm_rows = list(csv.DictReader(open("results/msm_detail.csv")))
fft_rows = list(csv.DictReader(open("results/fft_detail.csv")))

workloads = sorted(set(int(r["steps"]) for r in msm_rows))
edges_out = []
graphs = []

for steps in workloads:
    # Use run 1 because deterministic counters were already verified identical
    msm = [
        r for r in msm_rows
        if int(r["steps"]) == steps and int(r["run_id"]) == 1
    ]
    fft = [
        r for r in fft_rows
        if int(r["steps"]) == steps and int(r["run_id"]) == 1
    ]

    # MSM logical traffic proxy
    msm_read = 0
    msm_write = 0

    for r in msm:
        n = int(r["effective_pairs"])
        label = r["label"]

        point_size = G2 if label == "b_query_g2" else G1

        # Read one point + one scalar per effective pair
        msm_read += n * (point_size + FR)

        # Each MSM produces one group-element result
        msm_write += point_size

    msm_total = msm_read + msm_write

    # FFT/IFFT logical traffic proxy:
    # one field-element read + one field-element write per transform element
    fft_read = sum(int(r["elements"]) * FR for r in fft)
    fft_write = sum(int(r["elements"]) * FR for r in fft)
    fft_total = fft_read + fft_write

    raw_edges = [
        {
            "source": "MEMORY",
            "target": "MSM",
            "logical_bytes": msm_total,
            "logical_bytes_read": msm_read,
            "logical_bytes_written": msm_write,
            "derivation": (
                "effective_pairs * (compressed_point_bytes + scalar_bytes) "
                "+ one compressed output point per MSM"
            ),
            "measured_or_derived": "DERIVED"
        },
        {
            "source": "MEMORY",
            "target": "NTT_FFT",
            "logical_bytes": fft_total,
            "logical_bytes_read": fft_read,
            "logical_bytes_written": fft_write,
            "derivation": (
                "transform_elements * 32-byte field element * "
                "(one logical read + one logical write)"
            ),
            "measured_or_derived": "DERIVED"
        }
    ]

    max_bytes = max(e["logical_bytes"] for e in raw_edges)

    for e in raw_edges:
        e["normalized_weight"] = e["logical_bytes"] / max_bytes
        e["workload"] = f"Groth16-{steps}"
        e["steps"] = steps
        e["critical"] = False
        edges_out.append(e)

    graphs.append({
        "workload": f"Groth16-{steps}",
        "proof_system": "Groth16",
        "steps": steps,
        "nodes": [
            {"id": "MEMORY", "type": "memory"},
            {"id": "MSM", "type": "compute"},
            {"id": "NTT_FFT", "type": "compute"}
        ],
        "edges": raw_edges,
        "metadata": {
            "Fr_bytes": FR,
            "G1Affine_compressed_bytes": G1,
            "G2Affine_compressed_bytes": G2,
            "traffic_definition":
                "Logical payload proxy based on canonical serialized sizes; "
                "NOT physical DRAM/HBM traffic.",
            "edge_weight_formula":
                "logical_bytes / maximum logical_bytes within workload"
        }
    })

with open("results/zk3d_edges.csv", "w", newline="") as f:
    fields = [
        "workload", "steps", "source", "target",
        "logical_bytes", "logical_bytes_read",
        "logical_bytes_written", "normalized_weight",
        "critical", "measured_or_derived", "derivation"
    ]
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for row in edges_out:
        w.writerow({k: row[k] for k in fields})

with open("results/zk_workload_graph.json", "w") as f:
    json.dump(graphs, f, indent=2)

print("Wrote:")
print("  results/zk3d_edges.csv")
print("  results/zk_workload_graph.json")
