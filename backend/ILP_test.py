from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpStatus

model = LpProblem("Schedule_Optimization", LpMaximize)

start_time = int(input("start time: "))
end_time = int(input("end time: "))

# Define events (Appointments with category, duration, and priority)
events = {
    "Work": {"category": "task", "duration": 2, "priority": 8},
    "Exercise": {"category": "exercise", "duration": 1, "priority": 10},
    "Lunch": {"category": "food", "duration": 1, "priority": 6},
    "Meeting": {"category": "task", "duration": 1.5, "priority": 9},
    "Break": {"category": "break", "duration": 0.5, "priority": 5},
}

# Transition Score Matrix (Encourages good transitions, penalizes bad ones)
category_matrix = {
    "task": {"task": -10, "exercise": +10, "break": +10, "food": +5},
    "exercise": {"task": +10, "exercise": -10, "break": +5, "food": +5},
    "food": {"task": +3, "exercise": -5, "break": +3, "food": -10},
    "break": {"task": +10, "exercise": +5, "break": -10, "food": -3},
}

s = {e: LpVariable(f"start_{e}", start_time, end_time, cat="Continuous") for e in events}
x = {e: LpVariable(f"x_{e}", 0, 1, cat="Binary") for e in events}
o = {e: LpVariable(f"order_{e}", 1, len(events), cat="Integer") for e in events}
y = {(e1, e2): LpVariable(f"y_{e1}_{e2}", 0, 1, cat="Binary") for e1 in events for e2 in events if e1 != e2}

model += lpSum(events[e]["priority"] * x[e] for e in events) + lpSum(
    category_matrix[events[e1]["category"]][events[e2]["category"]] * y[e1, e2]
    for e1 in events for e2 in events if e1 != e2
)


model.solve()
status = model.solve()

if LpStatus[status] == 'Optimal':
    # Print results
    for e in events:
        start_val = s[e].value()
        order_val = o[e].value()
        if start_val is not None and order_val is not None:
            print(f"{e}: Start at {round(start_val, 2)}, Order {round(order_val)}")
        else:
            print(f"{e}: Start or order value is None")
else:
    print("No optimal solution found.")
