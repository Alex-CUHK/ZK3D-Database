import csv
import json

SCALAR_BYTES = 32
G1_BYTES = 48

MSM_EFFECTIVE_PAIRS = 5661
MSM_CALLS = 11
FFT_ELEMENTS = 31744

msm_read = MSM_EFFECTIVE_PAIRS * (G1_BYTES + SCALAR_BYTES)
msm_written = MSM_CALLS * G1_BYTES
msm_total = msm_read + msm_written

fft_read = FFT_ELEMENTS * SCALAR_BYTES
fft_written = FFT_ELEMENTS * SCALAR_BYTES
fft_total = fft_read + fft_written

max_bytes = max(msm_total, fft_total)

rows = [
    {
        "workload": "PLONK-KZG-TestCircuit",
        "source": "MEMORY",
        "target": "MSM",
        "logical_bytes": msm_total,
        "logical_bytes_read": msm_read,
        "logical_bytes_written": msm_written,
        "normalized_weight": msm_total / max_bytes,
        "critical": False,
        "measured_or_derived": "DERIVED",
        "derivation":
            "effective_pairs * (48-byte G1Affine + 32-byte Scalar) "
            "+ one 48-byte G1Affine output per KZG commitment",
    },
    {
        "workload": "PLONK-KZG-TestCircuit",
        "source": "MEMORY",
        "target": "NTT_FFT",
        "logical_bytes": fft_total,
        "logical_bytes_read": fft_read,
        "logical_bytes_written": fft_written,
        "normalized_weight": fft_total / max_bytes,
        "critical": False,
        "measured_or_derived": "DERIVED",
        "derivation":
            "transform_elements * 32-byte Scalar * "
            "(one logical read + one logical write)",
    },
]

with open("results/plonk_zk3d_edges.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)

graph = {
    "workload": "PLONK-KZG-TestCircuit",
    "metadata": {
        "scalar_serialized_bytes": SCALAR_BYTES,
        "g1_serialized_bytes": G1_BYTES,
        "note":
            "Logical payload proxy based on Dusk canonical serialized sizes; "
            "NOT measured physical DRAM/HBM traffic."
    },
    "nodes": ["MEMORY", "MSM", "NTT_FFT"],
    "edges": rows,
}

with open("results/plonk_zk3d_graph.json", "w") as f:
    json.dump(graph, f, indent=2)

print("Wrote:")
print("  results/plonk_zk3d_edges.csv")
print("  results/plonk_zk3d_graph.json")
