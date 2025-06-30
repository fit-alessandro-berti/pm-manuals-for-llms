import pm4py
from datetime import datetime
from collections import Counter

# ------------------------------------------------------------------------------
# 1. READ THE LOG AND PREPARE IT
# ------------------------------------------------------------------------------

log = pm4py.read_xes("order_process.xes")                     # traditional event log
log = pm4py.insert_artificial_start_end(log)                  # add ⟨START⟩ / ⟨END⟩ events

# ------------------------------------------------------------------------------
# 2. FILTER: REWORK OF “Check Order”  ▸  CASES INSIDE 2023
# ------------------------------------------------------------------------------

# Keep only cases where “Check Order” appears at least twice
log = pm4py.filter_activities_rework(
    log,
    activity="Check Order",
    min_occurrences=2
)

# Keep only traces whose *all* events lie in 2023
log = pm4py.filter_time_range(
    log,
    dt1="2023-01-01 00:00:00",
    dt2="2023-12-31 23:59:59",
    mode="traces_contained"
)

# ------------------------------------------------------------------------------
# 3. DISCOVER A PROCESS TREE AND CONVERT IT TO BPMN
# ------------------------------------------------------------------------------

tree = pm4py.discover_process_tree_inductive(log)
bpmn = pm4py.convert_to_bpmn(tree)
pm4py.write_bpmn(bpmn, "order_model.bpmn")

# ------------------------------------------------------------------------------
# 4. PERFORMANCE METRICS
# ------------------------------------------------------------------------------

# 4‑a  Average cycle time  ➜  days
cycle_seconds = pm4py.get_cycle_time(log)
print(f"\nAverage cycle time: {cycle_seconds / 86_400:.2f} days")

# 4‑b  Mean service time per activity  ➜  hours
print("\nMean service time per activity (hours):")
service_time_sec = pm4py.get_service_time(log, aggregation_measure="mean")
for activity, secs in service_time_sec.items():
    print(f"  {activity}: {secs / 3_600:.2f}")

# 4‑c  Batch execution analysis (≥ 3 instances by same resource)
batches = pm4py.discover_batches(
    log,
    merge_distance=15 * 60,          # 15 minutes between adjacent events
    min_batch_size=3
)

activity_batches = Counter()
for ((activity, _resource), _size, _details) in batches:
    activity_batches[activity] += 1

print("\nActivities executed in batches of ≥ 3:")
for activity, n_batches in activity_batches.items():
    print(f"  {activity}: {n_batches} batches")
