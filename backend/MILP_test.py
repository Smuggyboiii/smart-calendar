from pulp import *
import pandas as pd

prob = LpProblem("Smart_Calendar_Optimization", LpMaximize)

appointments = {
    "title": [
        "workout","study1","study2","lunch","study3","break"
    ],
    "start": [
        "07:00", "08:00", "09:00", "10:00", "11:00","15:00"
    ],
    "end": [
        "08:00", "09:00", "10:00", "11:00", "12:00", "16:00"
    ],
    "category": [
        "exercise", "task", "task","food", "task", "break"
    ],
    "fixed": [
        "no", "no", "no", "yes", "no","no"
    ]
}

#category matrix optimisation does not work -_- need to fix at least the display of the schedule works correctly now

category_matrix = {
    "task":    {"task": -10, "exercise": +10, "break": +10, "food": +7, "social": +6, "chores": +4, "travel": 0},
    "exercise": {"task": +10, "exercise": -10, "break": +5, "food": 0, "social": +3, "chores": 0, "travel": -3},
    "break":   {"task": +10, "exercise": +5, "break": -10, "food": +3, "social": +3, "chores": +3, "travel": 0},
    "food":    {"task": +3, "exercise": 0, "break": +3, "food": -10, "social": 0, "chores": +5, "travel": +3},
    "social":  {"task": +10, "exercise": +10, "break": +3, "food": 0, "social": -10, "chores": +5, "travel": +3},
    "chores":  {"task": +10, "exercise": +5, "break": 0, "food": -5, "social": +5, "chores": -10, "travel": -3},
    "travel":  {"task": 0, "exercise": -3, "break": 0, "food": +3, "social": +3, "chores": -3, "travel": -10}
}

df = pd.DataFrame(appointments)
print(df)

# Start and end of the day
s_min = 7
s_max = 22

# Creating the LpVariables
"""
At the beginning, the LpVariables do not have a value themselves; they will be solved later.
Using LpVariable.varValue we can check their value (which is None at the beginning).
Fixed events have a fixed value, which is the start time of the event.
"""
lpvariable_lst = []
s_vars = {}  # Dictionary to store start time variables for easy access

for i in range(len(df)):
    if df.loc[i,"fixed"] != "no":
        start_time = int((df.loc[i,"start"].lstrip("0").split(":")[0]))  # Convert HH:MM to int
        lpvariable_lst.append(start_time)
        s_vars[df.loc[i,"title"]] = start_time  # Store fixed value aka start time
    else:
        var = LpVariable(df.loc[i,"title"], s_min, s_max, cat="Integer")
        lpvariable_lst.append(var)
        s_vars[df.loc[i,"title"]] = var  # Store variable
        

#Constraint1 no overlapping
# Large M for enforcing constraints (should be large enough but not too large)
M = s_max - s_min  # The largest possible scheduling range

# Create binary decision variables for ordering
z_vars = {}  # Store binary variables

for i in range(len(df)):
    for j in range(i + 1, len(df)):
        event_i = df.loc[i, "title"]
        event_j = df.loc[j, "title"]

        s_i = s_vars[event_i]  # Start time of event i
        s_j = s_vars[event_j]  # Start time of event j
        d_i = int(df.loc[i, "end"].split(":")[0]) - int(df.loc[i, "start"].split(":")[0])  # Duration of event i
        d_j = int(df.loc[j, "end"].split(":")[0]) - int(df.loc[j, "start"].split(":")[0])  # Duration of event j

        # Create binary variable to decide order (z_ij = 1 if i before j, 0 otherwise)
        z_ij = LpVariable(f"z_{event_i}_{event_j}", cat="Binary")
        z_vars[(event_i, event_j)] = z_ij

        # Enforce no overlap using Big-M method
        prob += s_i + d_i <= s_j + M * (1 - z_ij), f"NoOverlap_{event_i}_{event_j}_1"
        prob += s_j + d_j <= s_i + M * z_ij, f"NoOverlap_{event_i}_{event_j}_2"



# Delta constraint

# Create a dictionary to store all delta variables
delta_vars = {}

# Loop over all event pairs (i, j)
for i in range(len(df)):
    for j in range(len(df)):
        if i != j:  # No self-transitions
            delta_name = f"delta_{df.loc[i, 'title']}_{df.loc[j, 'title']}"
            delta_var = LpVariable(delta_name, cat="Binary")
            delta_vars[(df.loc[i, 'title'], df.loc[j, 'title'])] = delta_var  # Store in dictionary


for i in range(len(df)):
    for j in range(len(df)):
        if i != j:  # Ensure we don’t compare an event with itself
            event_i = df.loc[i, "title"]
            event_j = df.loc[j, "title"]

            s_i = s_vars[event_i]  # Start time of event i
            s_j = s_vars[event_j]  # Start time of event j
            d_i = int(df.loc[i, "end"].split(":")[0]) - int(df.loc[i, "start"].split(":")[0])  # Duration
            delta_ij = delta_vars[(event_i, event_j)]  # Binary transition variable

            # Add the constraint to enforce event ordering
            prob += s_j >= (s_i + d_i) - M * (1 - delta_ij), f"Delta_{event_i}_{event_j}"

# Enforce fixed events stay fixed with some flexibility
# for i in range(len(df)):
#     if df.loc[i, "fixed"] == "yes":
#         event = df.loc[i, "title"]
#         fixed_start_time = int(df.loc[i, "start"].split(":")[0])  # Convert HH:MM to integer hours
#         prob += s_vars[event] >= fixed_start_time - 1, f"FixedLower_{event}"
#         prob += s_vars[event] <= fixed_start_time + 1, f"FixedUpper_{event}"

#All events are after the start and before the end of day
for i in range(len(df)):
    event = df.loc[i, "title"]
    prob += s_vars[event] >= s_min, f"MinTime_{event}"
    prob += s_vars[event] <= s_max, f"MaxTime_{event}"

# Ensure every event has at least one transition (in or out)
# for event in df["title"]:
#     prob += s_vars[event] >= s_min, f"EnsureStart_{event}"
#     prob += s_vars[event] <= s_max, f"EnsureEnd_{event}"

#Make more transitions likely so nothing is left out
#prob += lpSum(1 - delta_vars[(i, j)] for i in df["title"] for j in df["title"] if i != j), "EncourageTransitions"



#Objective function

weight_factor = 100  # Adjust based on optimization needs
prob += lpSum(
    weight_factor * category_matrix[df.loc[i, "category"]][df.loc[j, "category"]] * delta_vars[(df.loc[i, "title"], df.loc[j, "title"])]
    for i in range(len(df)) for j in range(len(df)) if i != j
), "Maximize_Weighted_Transition_Score"




prob.solve()

print("\n📋 Optimized Schedule:")
for event in df["title"]:
    start_time = s_vars[event] if isinstance(s_vars[event], int) else s_vars[event].varValue
    print(f"{event}: {start_time}:00")

print("Solver Status:", LpStatus[prob.status])
