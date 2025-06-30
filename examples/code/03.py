import pm4py
from datetime import datetime
from itertools import islice

# ------------------------------------------------------------------------------
# 1. READ THE OCEL AND PRE‑PROCESS IT
# ------------------------------------------------------------------------------

# Load the object‑centric event log
ocel = pm4py.read_ocel("furniture_factory.jsonocel")

# Remove duplicate E2O relations occurring at the same time
ocel = pm4py.ocel_drop_duplicates(ocel)

# Ensure a strict temporal ordering by adding a tiny Δt based on the index
ocel = pm4py.ocel_add_index_based_timedelta(ocel)

# Retain only executions (connected components) whose events run entirely in 2022
ocel = pm4py.filter_ocel_events_timestamp(
    ocel,
    min_timest="2022-01-01 00:00:00",
    max_timest="2022-12-31 23:59:59"
)

# Keep only the events that belong to orders connected with ≥ 2 components
ocel = pm4py.filter_ocel_object_per_type_count(ocel, {"component": 2})

# ------------------------------------------------------------------------------
# 2. FLATTEN ON THE OBJECT TYPE “order” AND ADD ⟨START⟩/⟨END⟩
# ------------------------------------------------------------------------------

log_df = pm4py.ocel_flattening(ocel, object_type="order")
log_df = pm4py.insert_artificial_start_end(log_df)

# ------------------------------------------------------------------------------
# 3. DISCOVER A PETRI NET WITH THE ILP MINER
# ------------------------------------------------------------------------------

net, im, fm = pm4py.discover_petri_net_ilp(log_df)

# Save a visual copy straight away (before possible decomposition)
pm4py.save_vis_petri_net(net, im, fm, "furniture_pn.png")

# ------------------------------------------------------------------------------
# 4. SOUNDNESS CHECK – MAXIMAL DECOMPOSITION IF NEEDED
# ------------------------------------------------------------------------------

is_sound, _diagnostics = pm4py.check_soundness(net, im, fm)
if not is_sound:
    decomposition = pm4py.maximal_decomposition(net, im, fm)
    print(f"\n⚠️  Net is not a sound WF‑net – maximal decomposition yields {len(decomposition)} sub‑nets.")
else:
    print("\n✅ The discovered Petri net is a sound WF‑net.")

# ------------------------------------------------------------------------------
# 5. CONFORMANCE: ALIGNMENT FITNESS & PRECISION
# ------------------------------------------------------------------------------

fitness = pm4py.fitness_alignments(
    log_df, net, im, fm,
    activity_key="concept:name",
    timestamp_key="time:timestamp",
    case_id_key="case:concept:name"
)
precision = pm4py.precision_alignments(
    log_df, net, im, fm,
    activity_key="concept:name",
    timestamp_key="time:timestamp",
    case_id_key="case:concept:name"
)

print(f"\nAlignment‑based log fitness        : {fitness['log_fitness']:.3f}")
print(f"Average trace fitness (alignment)  : {fitness['average_trace_fitness']:.3f}")
print(f"Alignment‑based precision          : {precision:.3f}")
print(f"Percentage of perfectly fitting cases: {fitness['percentage_of_fitting_traces']:.1f}%")

# ------------------------------------------------------------------------------
# 6. TEMPORAL PROFILE ▸ DEVIATION DETECTION (ζ = 2)
# ------------------------------------------------------------------------------

temporal_profile = pm4py.discover_temporal_profile(log_df)
deviations = pm4py.conformance_temporal_profile(
    log_df, temporal_profile, zeta=2,
    return_diagnostics_dataframe=False
)

# Extract the first five case IDs that have at least one deviation
deviating_cases = [
    case_id for case_id, devs in zip(
        pm4py.project_on_event_attribute(log_df, "case:concept:name"),
        deviations
    )
    if devs  # non‑empty list means at least one deviation
]
print("\nFirst five cases with temporal deviations (ζ = 2):")
for cid in islice(deviating_cases, 5):
    print(f"  {cid}")

# ------------------------------------------------------------------------------
# 7. SAVE THE MODEL
# ------------------------------------------------------------------------------

pm4py.write_pnml(net, im, fm, "furniture_model.pnml")
