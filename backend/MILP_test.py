from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpStatus
import pandas as pd
prob = LpProblem("Smart_Calendar_Optimization", LpMaximize)

appointments = {
    "title": ["workout", "study", "lunch", "meeting", "coding", "dinner", "reading"],
    "start": ["08:00", "10:00", "12:00", "14:00", "16:00", "18:30", "20:00"],
    "end": ["09:00", "12:00", "13:00", "15:00", "17:30", "19:30", "21:00"],
    "category": ["exercise", "task", "food", "task", "task", "food", "break"],
    "fixed": ["no", "no", "no", "no", "no", "no", "no"]
}


category_matrix = {
        "task": {"task": -10, "exercise": +10, "break": +10, "food": +7, "social": +6, "chores": +4, "travel": 0},
        "exercise": {"task": +10, "exercise": -10, "break": +5, "food": +5, "social": +3, "chores": 0, "travel": 0},
        "break": {"task": +10, "exercise": +5, "break": -10, "food": -3, "social": -5, "chores": +3, "travel": 0},
        "food": {"task": +3, "exercise": -5, "break": +3, "food": -10, "social": 0, "chores": +5, "travel": 0},
        "social": {"task": +10, "exercise": +10, "break": -1, "food": 0, "social": -10, "chores": +5, "travel": 0},
        "chores": {"task": +10, "exercise": +5, "break": -5, "food": -5, "social": +5, "chores": -10, "travel": 0},
        "travel": {"task": 0, "exercise": 0, "break": 0, "food": 0, "social": 0, "chores": 0, "travel": 0}
        }

df = pd.DataFrame(appointments)
print(df)

# Start and end of the day
s_min = 5
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
        
"""
need to figure out why some events are not scheduled at all 
and why more are not scheduled when they are fixed..
"""

#Constraint 1 -> no overlapping events

for i in range(len(df)):
    for j in range(i+1,len(df)):
        event_i =  df.loc[i,"title"]
        event_j =  df.loc[j,"title"]

        s_i = s_vars[event_i]  # Start time of event i
        s_j = s_vars[event_j]  # Start time of event j
        d_i = int(df.loc[i, "end"].split(":")[0]) - int(df.loc[i, "start"].split(":")[0])  # Duration of event i
        d_j = int(df.loc[j, "end"].split(":")[0]) - int(df.loc[j, "start"].split(":")[0])  # Duration of event j

        # Constraint: One event must finish before the other starts
        prob += (s_i + d_i <= s_j) or (s_j + d_j <= s_i), f"NoOverlap_{event_i}_{event_j}"

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
M = 1000  # Large number to ensure constraint works

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
for i in range(len(df)):
    if df.loc[i, "fixed"] == "yes":
        event = df.loc[i, "title"]
        fixed_start_time = int(df.loc[i, "start"].split(":")[0])  # Convert HH:MM to integer hours
        prob += s_vars[event] >= fixed_start_time - 1, f"FixedLower_{event}"
        prob += s_vars[event] <= fixed_start_time + 1, f"FixedUpper_{event}"

#All events are after the start and before the end of day
for i in range(len(df)):
    event = df.loc[i, "title"]
    prob += s_vars[event] >= s_min, f"MinTime_{event}"
    prob += s_vars[event] <= s_max, f"MaxTime_{event}"

# Ensure every event has at least one transition (in or out)
for event in df["title"]:
    prob += s_vars[event] >= s_min, f"EnsureStart_{event}"
    prob += s_vars[event] <= s_max, f"EnsureEnd_{event}"

#Make more transitions likely so nothing is left out
prob += lpSum(1 - delta_vars[(i, j)] for i in df["title"] for j in df["title"] if i != j), "EncourageTransitions"



#Objective function

prob += lpSum(category_matrix[df.loc[i, "category"]][df.loc[j, "category"]] * delta_vars[(df.loc[i, "title"], df.loc[j, "title"])]
             for i in range(len(df)) for j in range(len(df)) if i != j), "Maximize_Transition_Score"

prob.solve()
for v in prob.variables():
    print(v.name, "=", v.varValue)


