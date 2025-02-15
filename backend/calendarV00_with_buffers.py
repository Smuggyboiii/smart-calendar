import pandas as pd
from datetime import datetime, timedelta

class Appointment:
    def __init__(self, title, start, end, type, priority, buffer_min=None, notes=None, location=None, is_buffer=False):
        self.title = title
        self.start = datetime.strptime(start, '%Y-%m-%d %H:%M')
        self.end = datetime.strptime(end, '%Y-%m-%d %H:%M')
        self.type = type
        self.priority = priority
        self.buffer_min = buffer_min
        self.notes = notes
        self.location = location
        self.is_buffer = is_buffer  

        self.buffer_appointments = []  # Initialize as empty

        # Only create buffer appointments if it's not a buffer & buffer_min is set
        if not self.is_buffer and self.buffer_min is not None:
            self.create_buffer_appointments()

    def create_buffer_appointments(self):
        """Create buffer appointments before and after the main appointment if buffer_min is set."""
        if self.buffer_min is None:
            return

        buffer_half = timedelta(minutes=self.buffer_min // 2)

        # Creating buffer events
        buffer_before = Appointment(
            "Buffer",
            (self.start - buffer_half).strftime('%Y-%m-%d %H:%M'),
            self.start.strftime('%Y-%m-%d %H:%M'),
            "Buffer", 5, None, None, None, is_buffer=True
        )

        buffer_after = Appointment(
            "Buffer",
            self.end.strftime('%Y-%m-%d %H:%M'),
            (self.end + buffer_half).strftime('%Y-%m-%d %H:%M'),
            "Buffer", 5, None, None, None, is_buffer=True
        )

        self.buffer_appointments = [buffer_before, buffer_after]

    def to_dict(self):
        """Convert appointment to dictionary format."""
        return {
            'title': self.title,
            'start': self.start.strftime('%Y-%m-%d %H:%M'),
            'end': self.end.strftime('%Y-%m-%d %H:%M'),
            'type': self.type,
            'priority': self.priority,
            'buffer_minutes': self.buffer_min,
            'notes': self.notes,
            'location': self.location,
            'is_buffer': self.is_buffer
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
        """Check and add appointment only if it's valid, including buffer appointments."""
        if appointment.check_appointment():
            self.appointments.append(appointment)
            print(f"✅ Appointment '{appointment.title}' added successfully.")

            # Add buffer appointments
            for buffer_appt in appointment.buffer_appointments:
                self.appointments.append(buffer_appt)
                print(f"➕ Buffer '{buffer_appt.title}' added from {buffer_appt.start.strftime('%H:%M')} to {buffer_appt.end.strftime('%H:%M')}")

        else:
            print(f"❌ Appointment '{appointment.title}' was not added due to an error.")

    def merge_buffers(self):
        """Merge consecutive buffer periods into a single buffer."""
        if not self.appointments:
            return

        # Sort appointments by start time
        self.appointments.sort(key=lambda x: x.start)

        merged_appointments = []
        prev_buffer = None

        for appt in self.appointments:
            if appt.is_buffer:
                if prev_buffer and prev_buffer.end >= appt.start:
                    # Extend previous buffer
                    prev_buffer.end = max(prev_buffer.end, appt.end)
                else:
                    merged_appointments.append(appt)
                    prev_buffer = appt
            else:
                merged_appointments.append(appt)
                prev_buffer = None  # Reset buffer tracking

        self.appointments = merged_appointments

    def to_dataframe(self):
        """Convert all appointments to a pandas DataFrame."""
        return pd.DataFrame([appt.to_dict() for appt in self.appointments])

    def show_df(self):
        """Display the DataFrame after merging buffers."""
        self.merge_buffers()  # Merge buffers before displaying
        df = self.to_dataframe().drop(columns=['buffer_minutes', 'is_buffer'])
        print(df.sort_values(by="start", ascending=True))


# Example Usage
calendar = Calendar()

# Appointments with buffer times
calendar.add_appointment(Appointment("Meeting", "2025-09-01 09:00", "2025-09-01 10:00", "Work", 1, 30))
calendar.add_appointment(Appointment("Lunch", "2025-09-01 10:30", "2025-09-01 13:00", "Break", 1, 30))
calendar.add_appointment(Appointment("Workout", "2025-09-01 13:00", "2025-09-01 14:00", "Fitness", 1, 20))

calendar.show_df()
