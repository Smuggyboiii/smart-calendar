import pandas as pd
from datetime import datetime
from skopt import gp_minimize
from skopt.space import Integer


class Appointment:
    def __init__(self, title, start, end, category, priority, notes=None, location=None,fix=None):
        self.title = title
        self.start = datetime.strptime(start, '%H:%M')  # Only store time
        self.end = datetime.strptime(end, '%H:%M')  # Only store time
        self.priority = priority
        self.notes = notes
        self.location = location 
        self.category = category
        self.fix = fix

    def to_dict(self):
        """Convert appointment to dictionary format."""
        return {
            'title': self.title,
            'start': self.start.strftime('%H:%M'),  # Display time only
            'end': self.end.strftime('%H:%M'),
            'category': self.category,
            'priority': self.priority,
            'notes': self.notes,
            'location': self.location,
            'fix': self.fix
            
        }

    def check_appointment(self):
        """Check if the appointment's start time is before the end time."""
        if self.start >= self.end:
            print(f"❌ Error: Start time is after or equal to end time for '{self.title}'.")
            return False
        print(f"✅ Appointment '{self.title}' is valid.")
        return True
        

class Calendar:
    def __init__(self):
        self.appointments = []
    
    def add_appointment(self, appointment):
        if appointment.check_appointment():
            self.appointments.append(appointment)
        else:
            print(f"❌ Appointment '{appointment.title}' not added.")

    def remove_appointment(self, title):
        for appt in self.appointments:
            if appt.title == title:
                self.appointments.remove(appt)
                print(f"✅ Appointment '{title}' removed successfully.")
                return
        print(f"❌ Appointment '{title}' not found.")

    def change_appointment(self, title, new_title=None, new_start=None, new_end=None, new_category=None, new_priority=None, new_notes=None, new_location=None):
        """Change an appointment by title."""
        for appt in self.appointments:
            if appt.title == title:
                if new_title:
                    appt.title = new_title
                if new_start:
                    appt.start = datetime.strptime(new_start, '%H:%M')  # Only use time
                if new_end:
                    appt.end = datetime.strptime(new_end, '%H:%M')
                if new_category:
                    appt.category = new_category
                if new_priority:
                    appt.priority = new_priority
                if new_notes:
                    appt.notes = new_notes
                if new_location:
                    appt.location = new_location
                print(f"✅ Appointment '{title}' updated successfully.")
                return
        print(f"❌ Appointment '{title}' not found.")

    def show_appointment_info(self, title):
        for appt in self.appointments:
            if appt.title == title:
                print(f"Title: {appt.title}")
                print(f"Start: {appt.start.strftime('%H:%M')}")
                print(f"End: {appt.end.strftime('%H:%M')}")
                print(f"Category: {appt.category}")
                print(f"Priority: {appt.priority}")
                print(f"Notes: {appt.notes}")
                print(f"Location: {appt.location}")
                return
        print(f"❌ Appointment '{title}' not found.")

    def clear_appointments(self):
        self.appointments = []
        print("✅ All appointments cleared.")

    def to_dataframe(self):
        """Convert all appointments to a pandas DataFrame."""
        return pd.DataFrame([appt.to_dict() for appt in self.appointments])

    def show_all_appointments(self):
        df = self.to_dataframe()
        print(df.sort_values(by="start", ascending=True))


class Optimised_Calendar:
    def __init__(self, calendar):
        self.calendar = calendar  # Store the Calendar instance
        self.activities = {}
        self.category_matrix = {
        "task": {"task": -10, "exercise": +10, "break": +10, "food": +7, "social": +6, "chores": +4, "travel": 0},
        "exercise": {"task": +10, "exercise": -10, "break": +5, "food": +5, "social": +3, "chores": 0, "travel": 0},
        "break": {"task": +10, "exercise": +5, "break": -10, "food": -3, "social": -5, "chores": +3, "travel": 0},
        "food": {"task": +3, "exercise": -5, "break": +3, "food": -10, "social": 0, "chores": +5, "travel": 0},
        "social": {"task": +10, "exercise": +10, "break": -1, "food": 0, "social": -10, "chores": +5, "travel": 0},
        "chores": {"task": +10, "exercise": +5, "break": -5, "food": -5, "social": +5, "chores": -10, "travel": 0},
        "travel": {"task": 0, "exercise": 0, "break": 0, "food": 0, "social": 0, "chores": 0, "travel": 0}
        }

    def extract_activities(self):
        """Extract activities and their durations from the Calendar automatically."""
        self.activities = {
            appt.title: {
                "start_time": appt.start.hour + appt.start.minute / 60,  # Convert to decimal hours
                "duration": (appt.end - appt.start).total_seconds() // 60,  # Convert to minutes
                "category": appt.category  # Work, Break, etc.
            }
            for appt in self.calendar.appointments
        }
        return [appt["start_time"] for appt in self.activities.values()]  # Return start times

    
#create a list of important categories and see how they can be smartly implemented and not with nested if statements etc

    def schedule_optimisation(self, times):
        sorted_times = sorted(zip(times, list(self.activities.keys())), key=lambda x: x[0])
        prev_task = None
        score = 0

        for _, activity in sorted_times:
            category = self.activities[activity]["category"]

            if prev_task:
                prev_category = self.activities[prev_task]["category"]

                # ✅ Loop through the matrix dynamically
                if prev_category in self.category_matrix and category in self.category_matrix[prev_category]:
                    score += self.category_matrix[prev_category][category]
            
            prev_task = activity  # Update prev_task to the current activity
        print("Final Score:", score)
        return score   


    
        



# Example Usage (Single Day Planner)
calendar = Calendar()

# Add appointments (No year or month, just time)
calendar.add_appointment(Appointment("Workout", "07:00", "08:00", "exercise", 1,))
calendar.add_appointment(Appointment("Breakfast", "08:30", "09:00", "food", 3))
calendar.add_appointment(Appointment("Studying", "09:00", "12:00", "task", 2))
calendar.add_appointment(Appointment("Lunch", "12:00", "13:00", "food", 2))
calendar.add_appointment(Appointment("Studying", "13:00", "20:00", "task", 2))
calendar.add_appointment(Appointment("Break", "20:00", "20:30", "break", 2))
calendar.add_appointment(Appointment("Washing", "20:30", "21:00", "chores", 3))
calendar.add_appointment(Appointment("Dinner", "21:00", "21:30", "food", 3))


# Show specific appointment
calendar.show_appointment_info("Lunch")

# Change an appointment time
#calendar.change_appointment("Meeting", new_start="07:30")

# Display all appointments
calendar.show_all_appointments()

optimiser = Optimised_Calendar(calendar)
optimiser.schedule_optimisation(optimiser.extract_activities())




