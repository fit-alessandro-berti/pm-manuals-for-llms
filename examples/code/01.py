import pandas as pd
import pm4py
from datetime import timedelta

# ------------------------------------------------------------------------------
# 1. READ AND FORMAT THE EVENT LOG
# ------------------------------------------------------------------------------

# Load the CSV file (adjust the path if necessary)
df = pd.read_csv("insurance_claims.csv", parse_dates=["time:timestamp"])

# Give the dataframe its canonical process‑mining structure
df = pm4py.format_dataframe(
    df,
    case_id="case:concept:name",
    activity_key="concept:name",
    timestamp_key="time:timestamp"
)

# ------------------------------------------------------------------------------
# 2. FILTER THE LOG AS REQUESTED
# ------------------------------------------------------------------------------

# Keep only cases that start with “Receive Claim”
df = pm4py.filter_start_activities(df, {"Receive Claim"}, retain=True)

# …and end with “Send Final Letter”
df = pm4py.filter_end_activities(df, {"Send Final Letter"}, retain=True)

# Keep cases whose duration ≤ 90 days  (= 7 776 000 seconds)
max_seconds = 90 * 24 * 60 * 60
df = pm4py.filter_case_performance(df, min_performance=0, max_performance=max_seconds)

# ------------------------------------------------------------------------------
# 3. DISCOVER A PETRI NET WITH THE INDUCTIVE MINER
# ------------------------------------------------------------------------------

net, im, fm = pm4py.discover_petri_net_inductive(
    df,
    noise_threshold=0.20,
    activity_key="concept:name",
    timestamp_key="time:timestamp",
    case_id_key="case:concept:name"
)

# ------------------------------------------------------------------------------
# 4. CONFORMANCE MEASURES
# ------------------------------------------------------------------------------

# 4a.  Token‑based replay fitness
fitness_tbr = pm4py.fitness_token_based_replay(
    df, net, im, fm,
    activity_key="concept:name",
    timestamp_key="time:timestamp",
    case_id_key="case:concept:name"
)

# 4b.  Alignment‑based precision
precision_align = pm4py.precision_alignments(
    df, net, im, fm,
    activity_key="concept:name",
    timestamp_key="time:timestamp",
    case_id_key="case:concept:name"
)

# 4c.  Percentage of fitting traces (already in the fitness dict for convenience)
pct_fit = fitness_tbr["percentage_of_fitting_traces"]

# ------------------------------------------------------------------------------
# 5. SELF‑DISTANCE / REWORK ANALYSIS
# ------------------------------------------------------------------------------

# Minimum observed self‑distance per activity
min_self_dist = pm4py.get_minimum_self_distances(
    df,
    activity_key="concept:name",
    timestamp_key="time:timestamp",
    case_id_key="case:concept:name"
)

# Activities with minimum self‑distance ≤ 1
rework_acts = {act for act, dist in min_self_dist.items() if dist <= 1}

# Number of cases in which each of those activities is actually reworked
rework_cases = pm4py.get_rework_cases_per_activity(
    df,
    activity_key="concept:name",
    timestamp_key="time:timestamp",
    case_id_key="case:concept:name"
)
rework_cases = {act: cnt for act, cnt in rework_cases.items() if act in rework_acts}

# ------------------------------------------------------------------------------
# 6. OUTPUT SUMMARY STATISTICS
# ------------------------------------------------------------------------------

print("=== Conformance metrics ===")
print(f"Token‑based replay log‑fitness      : {fitness_tbr['log_fitness']:.3f}")
print(f"Token‑based average trace fitness   : {fitness_tbr['average_trace_fitness']:.3f}")
print(f"Alignment‑based precision           : {precision_align:.3f}")
print(f"Percentage of perfectly fitting cases: {pct_fit:.1f}%\n")

print("=== Rework analysis (minimum self‑distance ≤ 1) ===")
for act, num_cases in rework_cases.items():
    print(f"Activity '{act}' shows rework in {num_cases} cases")

# ------------------------------------------------------------------------------
# 7. SAVE THE MODEL
# ------------------------------------------------------------------------------

pm4py.write_pnml(net, im, fm, "claims_model.pnml")

# (Optional) visual inspection – uncomment if you want an on‑screen view
# pm4py.view_petri_net(net, im, fm)
