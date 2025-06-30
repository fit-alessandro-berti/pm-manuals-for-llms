import pm4py
from collections import Counter
from datetime import datetime

# ------------------------------------------------------------------------------
# 1. READ THE LOG, ADD ⟨START⟩/⟨END⟩ AND BASIC FILTERING
# ------------------------------------------------------------------------------

log = pm4py.read_xes("claims_2024.xes")                         # XES ➜ EventLog
log = pm4py.insert_artificial_start_end(log)                    # add artificial markers

# Keep only traces whose events lie inside calendar year 2024
log = pm4py.filter_time_range(
    log,
    dt1="2024-01-01 00:00:00",
    dt2="2024-12-31 23:59:59",
    mode="traces_contained"
)

# Keep cases whose throughput time ≤ 60 days
max_seconds = 60 * 24 * 60 * 60
log = pm4py.filter_case_performance(log, 0, max_seconds)

# ------------------------------------------------------------------------------
# 2. FREQUENT TRACE SEGMENTS (PREFIXSPAN)
# ------------------------------------------------------------------------------

segments_counter: Counter = pm4py.get_frequent_trace_segments(log, min_occ=5)
top10 = segments_counter.most_common(10)

print("\n=== 10 most frequent trace segments (PrefixSpan) ===")
for segment, freq in top10:
    print(f"{segment}  →  {freq}")

# ------------------------------------------------------------------------------
# 3. CUT LOG TO PREFIXES UP TO FIRST “Approve Claim”
# ------------------------------------------------------------------------------

log = pm4py.filter_prefixes(
    log,
    activity="Approve Claim",
    strict=True,
    first_or_last="first"
)

# ------------------------------------------------------------------------------
# 4. DISCOVER DIRECTLY‑FOLLOWS GRAPHS (FREQUENCY & PERFORMANCE)
# ------------------------------------------------------------------------------

dfg, start_acts, end_acts = pm4py.discover_dfg(log)
perf_dfg, _, _ = pm4py.discover_performance_dfg(log)

pm4py.save_vis_dfg(dfg, start_acts, end_acts, "dfg_freq.png")
pm4py.save_vis_performance_dfg(
    perf_dfg, start_acts, end_acts,
    file_path="dfg_perf.png",
    aggregation_measure="mean"
)

# ------------------------------------------------------------------------------
# 5. DISCOVER A PETRI NET WITH THE ALPHA MINER
# ------------------------------------------------------------------------------

net, im, fm = pm4py.discover_petri_net_alpha(log)

# ── Save the model
pm4py.write_pnml(net, im, fm, "claims_2024_model.pnml")

# ------------------------------------------------------------------------------
# 6. STOCHASTIC LANGUAGES  ➜  EARTH MOVER’S DISTANCE
# ------------------------------------------------------------------------------

lang_log   = pm4py.get_stochastic_language(log)
lang_model = pm4py.get_stochastic_language(net, im, fm)
emd_value  = pm4py.compute_emd(lang_log, lang_model)

print(f"\nEarth Mover’s Distance between log and model languages: {emd_value:.4f}")

# ------------------------------------------------------------------------------
# 7. ADDITIONAL PERFORMANCE & STRUCTURAL METRICS
# ------------------------------------------------------------------------------

# 7‑a  Average cycle time (days)
cycle_time_sec = pm4py.get_cycle_time(log)
print(f"\nAverage cycle time: {cycle_time_sec / 86_400:.2f} days")

# 7‑b  Position distribution of “Review Claim”
pos_summary = pm4py.get_activity_position_summary(log, "Review Claim")
print("\nPosition distribution of ‘Review Claim’ within traces:")
for pos, count in sorted(pos_summary.items()):
    print(f"  position {pos}: {count} occurrences")

# 7‑c  Minimum self‑distance witnesses
witnesses = pm4py.get_minimum_self_distance_witnesses(log)
print("\nWitness activities for finite minimum self‑distances:")
for activity, wit_set in witnesses.items():
    print(f"  {activity}: {', '.join(sorted(wit_set))}")
