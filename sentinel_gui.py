
import csv
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime


# --------------------------------------------------
# PROJECT SENTINEL - WORKER-FRIENDLY INTERFACE
# This file reads the existing CSV files.
# It does not modify the sensor engine or CSV history.
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
READINGS_FILE = BASE_DIR / "sentinel_readings.csv"
ALERTS_FILE = BASE_DIR / "sentinel_alerts.csv"

REFRESH_MS = 2000


class SentinelGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Project Sentinel | Equipment Monitoring")
        self.root.geometry("1100x720")
        self.root.minsize(850, 600)

        self.colors = {
            "background": "#F2F5F9",
            "panel": "#FFFFFF",
            "navy": "#16324F",
            "blue": "#245A81",
            "green": "#237A45",
            "green_bg": "#E4F5E9",
            "yellow": "#966500",
            "yellow_bg": "#FFF3CD",
            "red": "#B42318",
            "red_bg": "#FDE8E7",
            "text": "#172B3A",
            "muted": "#5C6B78",
            "border": "#D7E0E8",
        }

        self.root.configure(bg=self.colors["background"])

        self.style = ttk.Style()
        self.style.configure(
            "Treeview",
            font=("Arial", 11),
            rowheight=34,
            background="white",
            fieldbackground="white",
        )
        self.style.configure(
            "Treeview.Heading",
            font=("Arial", 11, "bold"),
        )
        self.style.configure(
            "TNotebook.Tab",
            font=("Arial", 12, "bold"),
            padding=(18, 10),
        )

        self.latest_reading = None
        self.all_alerts = []

        self.build_header()
        self.build_pages()
        self.refresh_dashboard()
        self.load_alert_history()

    # --------------------------------------------------
    # HEADER AND NAVIGATION
    # --------------------------------------------------

    def build_header(self):
        header = tk.Frame(
            self.root,
            bg=self.colors["navy"],
            padx=22,
            pady=17,
        )
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="PROJECT SENTINEL",
            font=("Arial", 22, "bold"),
            bg=self.colors["navy"],
            fg="white",
        )
        title.pack(side="left")

        subtitle = tk.Label(
            header,
            text="EQUIPMENT MONITORING SYSTEM",
            font=("Arial", 10, "bold"),
            bg=self.colors["navy"],
            fg="#D8E7F3",
        )
        subtitle.pack(side="right", padx=4)

    def build_pages(self):
        container = tk.Frame(
            self.root,
            bg=self.colors["background"],
            padx=18,
            pady=15,
        )
        container.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill="both", expand=True)

        self.dashboard_page = tk.Frame(
            self.notebook,
            bg=self.colors["background"],
            padx=16,
            pady=16,
        )

        self.history_page = tk.Frame(
            self.notebook,
            bg=self.colors["background"],
            padx=16,
            pady=16,
        )

        self.notebook.add(
            self.dashboard_page,
            text="  LIVE DASHBOARD  ",
        )
        self.notebook.add(
            self.history_page,
            text="  HISTORY LOG  ",
        )

        self.build_dashboard()
        self.build_history()

    # --------------------------------------------------
    # LIVE DASHBOARD
    # --------------------------------------------------

    def build_dashboard(self):
        page = self.dashboard_page

        tk.Label(
            page,
            text="Equipment Status",
            font=("Arial", 19, "bold"),
            bg=self.colors["background"],
            fg=self.colors["text"],
        ).pack(anchor="w", pady=(0, 10))

        self.status_panel = tk.Frame(
            page,
            bg=self.colors["green_bg"],
            padx=18,
            pady=16,
            highlightthickness=1,
            highlightbackground=self.colors["border"],
        )
        self.status_panel.pack(fill="x", pady=(0, 14))

        self.status_title = tk.Label(
            self.status_panel,
            text="WAITING FOR SENSOR DATA",
            font=("Arial", 19, "bold"),
            bg=self.colors["green_bg"],
            fg=self.colors["green"],
        )
        self.status_title.pack(anchor="w")

        self.status_message = tk.Label(
            self.status_panel,
            text="Start the sensor simulator to display readings.",
            font=("Arial", 12),
            bg=self.colors["green_bg"],
            fg=self.colors["text"],
            justify="left",
            wraplength=850,
        )
        self.status_message.pack(anchor="w", pady=(6, 0))

        readings_heading = tk.Label(
            page,
            text="Current Sensor Readings",
            font=("Arial", 16, "bold"),
            bg=self.colors["background"],
            fg=self.colors["text"],
        )
        readings_heading.pack(anchor="w", pady=(4, 10))

        readings_frame = tk.Frame(
            page,
            bg=self.colors["background"],
        )
        readings_frame.pack(fill="x")

        self.reading_labels = {}

        sensor_info = [
            ("temperature", "Temperature", "Machine heat level"),
            ("vibration", "Vibration", "How much the machine shakes"),
            ("pressure", "Pressure", "Machine pressure reading"),
            ("power", "Power", "Machine power reading"),
        ]

        for index, (key, name, description) in enumerate(sensor_info):
            card = tk.Frame(
                readings_frame,
                bg=self.colors["panel"],
                padx=15,
                pady=14,
                highlightthickness=1,
                highlightbackground=self.colors["border"],
            )
            card.grid(
                row=index // 2,
                column=index % 2,
                sticky="nsew",
                padx=5,
                pady=5,
            )

            tk.Label(
                card,
                text=name.upper(),
                font=("Arial", 10, "bold"),
                bg=self.colors["panel"],
                fg=self.colors["muted"],
            ).pack(anchor="w")

            value_label = tk.Label(
                card,
                text="--",
                font=("Arial", 23, "bold"),
                bg=self.colors["panel"],
                fg=self.colors["blue"],
            )
            value_label.pack(anchor="w", pady=(4, 2))

            tk.Label(
                card,
                text=description,
                font=("Arial", 10),
                bg=self.colors["panel"],
                fg=self.colors["muted"],
            ).pack(anchor="w")

            self.reading_labels[key] = value_label

        readings_frame.columnconfigure(0, weight=1)
        readings_frame.columnconfigure(1, weight=1)

        self.last_updated_label = tk.Label(
            page,
            text="Last updated: waiting for data",
            font=("Arial", 10),
            bg=self.colors["background"],
            fg=self.colors["muted"],
        )
        self.last_updated_label.pack(anchor="w", pady=(12, 5))

        button_row = tk.Frame(
            page,
            bg=self.colors["background"],
        )
        button_row.pack(fill="x", pady=(8, 0))

        tk.Button(
            button_row,
            text="REFRESH NOW",
            font=("Arial", 11, "bold"),
            bg=self.colors["blue"],
            fg="white",
            activebackground=self.colors["navy"],
            activeforeground="white",
            relief="flat",
            padx=18,
            pady=10,
            command=self.refresh_dashboard,
        ).pack(side="left")

        tk.Button(
            button_row,
            text="VIEW ALERT HISTORY",
            font=("Arial", 11, "bold"),
            bg="#E0EAF3",
            fg=self.colors["navy"],
            activebackground="#C9D9E8",
            relief="flat",
            padx=18,
            pady=10,
            command=lambda: self.notebook.select(
                self.history_page
            ),
        ).pack(side="left", padx=10)

    # --------------------------------------------------
    # HISTORY LOG
    # --------------------------------------------------

    def build_history(self):
        page = self.history_page

        tk.Label(
            page,
            text="Alert History",
            font=("Arial", 19, "bold"),
            bg=self.colors["background"],
            fg=self.colors["text"],
        ).pack(anchor="w")

        tk.Label(
            page,
            text=(
                "All saved warnings, spikes, rising trends, "
                "and critical alerts. Normal readings are hidden."
            ),
            font=("Arial", 11),
            bg=self.colors["background"],
            fg=self.colors["muted"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(5, 12))

        counts_frame = tk.Frame(
            page,
            bg=self.colors["background"],
        )
        counts_frame.pack(fill="x", pady=(0, 12))

        self.warning_count_label = tk.Label(
            counts_frame,
            text="Warnings: 0",
            font=("Arial", 12, "bold"),
            bg=self.colors["yellow_bg"],
            fg=self.colors["yellow"],
            padx=14,
            pady=10,
        )
        self.warning_count_label.pack(side="left", padx=(0, 8))

        self.critical_count_label = tk.Label(
            counts_frame,
            text="Critical: 0",
            font=("Arial", 12, "bold"),
            bg=self.colors["red_bg"],
            fg=self.colors["red"],
            padx=14,
            pady=10,
        )
        self.critical_count_label.pack(side="left", padx=(0, 8))

        self.total_count_label = tk.Label(
            counts_frame,
            text="Total alerts: 0",
            font=("Arial", 12, "bold"),
            bg="#E0EAF3",
            fg=self.colors["navy"],
            padx=14,
            pady=10,
        )
        self.total_count_label.pack(side="left")

        filter_frame = tk.Frame(
            page,
            bg=self.colors["background"],
        )
        filter_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            filter_frame,
            text="Search:",
            font=("Arial", 11, "bold"),
            bg=self.colors["background"],
            fg=self.colors["text"],
        ).pack(side="left")

        self.search_var = tk.StringVar()

        search_entry = tk.Entry(
            filter_frame,
            textvariable=self.search_var,
            font=("Arial", 11),
            width=25,
        )
        search_entry.pack(side="left", padx=(7, 15), ipady=5)
        search_entry.bind(
            "<KeyRelease>",
            lambda event: self.apply_history_filters(),
        )

        tk.Label(
            filter_frame,
            text="Severity:",
            font=("Arial", 11, "bold"),
            bg=self.colors["background"],
            fg=self.colors["text"],
        ).pack(side="left")

        self.severity_var = tk.StringVar(value="ALL")

        severity_filter = ttk.Combobox(
            filter_frame,
            textvariable=self.severity_var,
            values=("ALL", "WARNING", "CRITICAL"),
            state="readonly",
            width=12,
            font=("Arial", 10),
        )
        severity_filter.pack(side="left", padx=7)
        severity_filter.bind(
            "<<ComboboxSelected>>",
            lambda event: self.apply_history_filters(),
        )

        tk.Button(
            filter_frame,
            text="REFRESH HISTORY",
            font=("Arial", 10, "bold"),
            bg=self.colors["blue"],
            fg="white",
            relief="flat",
            padx=12,
            pady=7,
            command=self.load_alert_history,
        ).pack(side="right")

        table_frame = tk.Frame(page, bg="white")
        table_frame.pack(fill="both", expand=True)

        columns = (
            "time",
            "severity",
            "message",
            "temperature",
            "vibration",
        )

        self.history_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.history_table.heading("time", text="DATE / TIME")
        self.history_table.heading("severity", text="SEVERITY")
        self.history_table.heading("message", text="WHAT HAPPENED")
        self.history_table.heading("temperature", text="TEMP")
        self.history_table.heading("vibration", text="VIBRATION")

        self.history_table.column("time", width=155, minwidth=130)
        self.history_table.column("severity", width=105, minwidth=90)
        self.history_table.column("message", width=360, minwidth=220)
        self.history_table.column("temperature", width=90, minwidth=75)
        self.history_table.column("vibration", width=100, minwidth=80)

        scrollbar_y = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.history_table.yview,
        )
        scrollbar_x = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.history_table.xview,
        )

        self.history_table.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
        )

        self.history_table.grid(
            row=0, column=0, sticky="nsew"
        )
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.history_table.tag_configure(
            "WARNING",
            background="#FFF3CD",
            foreground="#765000",
        )
        self.history_table.tag_configure(
            "CRITICAL",
            background="#FDE8E7",
            foreground="#A51D16",
        )

        self.history_table.bind(
            "<<TreeviewSelect>>",
            self.show_selected_alert,
        )

        self.alert_details = tk.Label(
            page,
            text="Select an alert to see its details.",
            font=("Arial", 11),
            bg=self.colors["panel"],
            fg=self.colors["text"],
            justify="left",
            anchor="w",
            wraplength=950,
            padx=12,
            pady=12,
            relief="solid",
            bd=1,
        )
        self.alert_details.pack(fill="x", pady=(10, 0))

    # --------------------------------------------------
    # CSV READING
    # --------------------------------------------------

    @staticmethod
    def read_csv_file(path):
        if not path.exists():
            return []

        try:
            with path.open(
                "r",
                newline="",
                encoding="utf-8-sig",
            ) as file:
                return list(csv.DictReader(file))

        except (OSError, csv.Error) as error:
            raise RuntimeError(
                f"Could not read {path.name}: {error}"
            ) from error

    # --------------------------------------------------
    # LIVE DASHBOARD DATA
    # --------------------------------------------------

    def refresh_dashboard(self):
        try:
            rows = self.read_csv_file(READINGS_FILE)

            if not rows:
                self.show_no_readings()
            else:
                self.latest_reading = rows[-1]
                self.display_latest_reading(self.latest_reading)

            self.last_updated_label.config(
                text=(
                    "Screen refreshed: "
                    + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )

        except RuntimeError as error:
            self.status_title.config(text="DATA FILE ERROR")
            self.status_message.config(text=str(error))
            self.set_status_colors("WARNING")

        finally:
            self.root.after(
                REFRESH_MS,
                self.refresh_dashboard,
            )

    def show_no_readings(self):
        self.status_title.config(text="WAITING FOR SENSOR DATA")
        self.status_message.config(
            text=(
                "No readings found yet. Start sensor_simulator.py "
                "in Terminal, then return to this window."
            )
        )

        for label in self.reading_labels.values():
            label.config(text="--")

        self.set_status_colors("NORMAL")

    def display_latest_reading(self, reading):
        for key in (
            "temperature",
            "vibration",
            "pressure",
            "power",
        ):
            value = reading.get(key, "")
            if value:
                try:
                    value = f"{float(value):.2f}"
                except (ValueError, TypeError):
                    pass
            else:
                value = "N/A"

            self.reading_labels[key].config(text=value)

        status = str(reading.get("status", "NORMAL")).upper()

        if "CRITICAL" in status:
            severity = "CRITICAL"
            title = "CRITICAL ALERT"
            explanation = (
                "A critical condition was recorded. Follow the "
                "approved equipment safety procedure and notify "
                "the responsible supervisor."
            )

        elif "WARNING" in status:
            severity = "WARNING"
            title = "WARNING - CHECK EQUIPMENT"
            explanation = (
                "An unusual reading was recorded. Check the "
                "equipment and follow the approved inspection procedure."
            )

        else:
            severity = "NORMAL"
            title = "NORMAL - NO ACTIVE ALERT"
            explanation = (
                "The latest saved reading is marked normal. "
                "Continue routine monitoring."
            )

        self.status_title.config(text=title)
        self.status_message.config(
            text=explanation + "\n\nRecorded status: " + status
        )
        self.set_status_colors(severity)

    def set_status_colors(self, severity):
        if severity == "CRITICAL":
            background = self.colors["red_bg"]
            foreground = self.colors["red"]

        elif severity == "WARNING":
            background = self.colors["yellow_bg"]
            foreground = self.colors["yellow"]

        else:
            background = self.colors["green_bg"]
            foreground = self.colors["green"]

        self.status_panel.config(bg=background)
        self.status_title.config(
            bg=background,
            fg=foreground,
        )
        self.status_message.config(
            bg=background,
            fg=self.colors["text"],
        )

    # --------------------------------------------------
    # ALERT HISTORY
    # --------------------------------------------------

    def load_alert_history(self):
        try:
            rows = self.read_csv_file(ALERTS_FILE)

        except RuntimeError as error:
            messagebox.showerror(
                "History Log Error",
                str(error),
            )
            return

        self.all_alerts = []

        for row in rows:
            severity = str(row.get("severity", "")).upper()
            message = str(row.get("message", "")).upper()

            # Only show alerts. Ignore normal records if present.
            is_alert = (
                severity in ("WARNING", "CRITICAL")
                or any(
                    word in message
                    for word in (
                        "SPIKE",
                        "RISING",
                        "WARNING",
                        "CRITICAL",
                        "HIGH TEMPERATURE",
                        "HIGH VIBRATION",
                    )
                )
            )

            if not is_alert:
                continue

            # If severity is missing, infer it from the message.
            if severity not in ("WARNING", "CRITICAL"):
                if "CRITICAL" in message:
                    severity = "CRITICAL"
                else:
                    severity = "WARNING"

            row["_display_severity"] = severity
            self.all_alerts.append(row)

        self.all_alerts.reverse()

        warning_count = sum(
            1 for row in self.all_alerts
            if row["_display_severity"] == "WARNING"
        )
        critical_count = sum(
            1 for row in self.all_alerts
            if row["_display_severity"] == "CRITICAL"
        )

        self.warning_count_label.config(
            text=f"Warnings: {warning_count}"
        )
        self.critical_count_label.config(
            text=f"Critical: {critical_count}"
        )
        self.total_count_label.config(
            text=f"Total alerts: {len(self.all_alerts)}"
        )

        self.apply_history_filters()

    def apply_history_filters(self):
        if not hasattr(self, "history_table"):
            return

        search_text = self.search_var.get().strip().lower()
        selected_severity = self.severity_var.get()

        for item in self.history_table.get_children():
            self.history_table.delete(item)

        for index, row in enumerate(self.all_alerts):
            severity = row.get("_display_severity", "WARNING")
            message = str(row.get("message", ""))
            timestamp = str(row.get("time", ""))

            if (
                selected_severity != "ALL"
                and severity != selected_severity
            ):
                continue

            searchable_text = " ".join(
                str(row.get(key, ""))
                for key in (
                    "time",
                    "severity",
                    "message",
                    "temperature",
                    "vibration",
                    "pressure",
                    "power",
                )
            ).lower()

            if search_text and search_text not in searchable_text:
                continue

            self.history_table.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    timestamp,
                    severity,
                    message.replace(", ", " | "),
                    row.get("temperature", "N/A"),
                    row.get("vibration", "N/A"),
                ),
                tags=(severity,),
            )

        self.alert_details.config(
            text="Select an alert above to see its details."
        )

    def show_selected_alert(self, event=None):
        selection = self.history_table.selection()

        if not selection:
            return

        row_id = selection[0]

        try:
            row = self.all_alerts[int(row_id)]
        except (ValueError, IndexError):
            return

        severity = row.get("_display_severity", "WARNING")
        message = row.get("message", "Alert details unavailable.")

        details = (
            f"{severity} ALERT\n"
            f"Time: {row.get('time', 'Unknown')}\n"
            f"Event: {message}\n"
            f"Temperature: {row.get('temperature', 'N/A')}\n"
            f"Vibration: {row.get('vibration', 'N/A')}\n"
            f"Pressure: {row.get('pressure', 'N/A')}\n"
            f"Power: {row.get('power', 'N/A')}\n\n"
            "This entry comes from the saved alert log. "
            "Use the approved equipment procedure to determine "
            "the correct response."
        )

        self.alert_details.config(text=details)


def main():
    root = tk.Tk()
    SentinelGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

