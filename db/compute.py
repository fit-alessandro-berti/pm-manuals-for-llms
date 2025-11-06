import json, os
import pm4py

ocel = pm4py.read_ocel("C:/example_log.jsonocel")

for file in os.listdir("generic"):
    path = os.path.join("generic", file)
    kpi = json.load(open(path, "r"))

    exec(kpi["code"])
    print(f(ocel))
