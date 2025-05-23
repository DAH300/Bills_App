APP_VERSION = "1.0.3"

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import json
import os
import webbrowser
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta  # Handles accurate month jumps
import requests
import subprocess
import sys
import shutil
import tempfile
import requests

GITHUB_VERSION_URL = "https://raw.githubusercontent.com/DAH300/Bills_App/main/version.txt"
SCRIPT_URL = "https://raw.githubusercontent.com/DAH300/Bills_App/main/Bills.py"
REPO_URL = "https://raw.githubusercontent.com/DAH300/Bills_App/main"
EXE_NAME = "Bills.exe"

BILLS_FILE = Path("bills.json")
HISTORY_FILE = Path("bill_history.json")

FREQUENCY_OPTIONS = ["Monthly", "6 Months", "Yearly"]



class Bill:
    def __init__(self, name, amount, fixed, due_date, frequency, fixed_day, paid, link):
        self.name = name
        self.amount = amount
        self.fixed = fixed  # True = fixed amount, False = variable
        self.due_date = due_date
        self.frequency = frequency  # "Monthly", "6 Months", "Yearly"
        self.fixed_day = fixed_day  # Specific day of the month (1, 15, etc.) or None
        self.paid = paid
        self.link = link



    def to_dict(self):
        return {
            "name": self.name,
            "amount": self.amount,
            "fixed": self.fixed,
            "due_date": self.due_date,
            "frequency": self.frequency,
            "fixed_day": self.fixed_day,
            "paid": self.paid,
            "link": self.link
        }

    @staticmethod
    def from_dict(data):
        return Bill(data["name"], data["amount"], data["fixed"], data["due_date"],
                    data["frequency"], data.get("fixed_day"), data["paid"], data["link"])

    def update_due_date(self):
        today = datetime.today().date()
        due_date = datetime.strptime(self.due_date, "%Y-%m-%d").date()

        if self.paid and due_date < today:
            if self.frequency == "Monthly":
                new_due_date = due_date + relativedelta(months=1)
            elif self.frequency == "6 Months":
                new_due_date = due_date + relativedelta(months=6)
            elif self.frequency == "Yearly":
                new_due_date = due_date + relativedelta(years=1)
            else:
                return

            if self.fixed_day:
                try:
                    new_due_date = new_due_date.replace(day=self.fixed_day)
                except ValueError:
                    new_due_date = new_due_date.replace(day=1) + relativedelta(days=-1)

            self.due_date = new_due_date.strftime("%Y-%m-%d")
            self.paid = False  # Reset payment status for the new cycle


class BillTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bill Tracker")
        self.bills = self.load_bills()
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

                # Menu Bar
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Check for Updates", command=self.check_for_updates)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)


        self.root.geometry("1000x500")

        self.listbox = tk.Listbox(root, width=100, height=15)
        self.listbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.listbox.config(font=('Helvetica', 14))

        button_frame = tk.Frame(root)
        button_frame.grid(row=1, column=0, pady=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)


        tk.Button(button_frame, text="Add Bill", command=self.add_bill, font=("Helvetica", 14)).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Mark Paid/Unpaid", command=self.toggle_paid, font=("Helvetica", 14)).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Open Link", command=self.open_link, font=("Helvetica", 14)).grid(row=0, column=2, padx=5)
        tk.Button(button_frame, text="Update Bills", command=self.update_bills, font=("Helvetica", 14)).grid(row=0, column=3, padx=5)
        tk.Button(button_frame, text="View History", command=self.view_history, font=("Helvetica", 14)).grid(row=0, column=4, padx=5)

        self.refresh_list()

    def show_about(self):
        messagebox.showinfo(
            "About",
            f"Bill Tracker App\nVersion {APP_VERSION}\nCreated by Dwayne Howell\nGitHub: https://github.com/DAH300/Bills_App"
    )
        
    def check_for_updates(self):
        try:
            VERSION_URL = "https://raw.githubusercontent.com/DAH300/Bills_App/main/version.txt"

            response = requests.get(VERSION_URL)
            if response.status_code != 200:
                messagebox.showerror("Update Error", f"Failed to check for updates.\nStatus: {response.status_code}")
                return

            latest_version = response.text.strip()
            if latest_version == APP_VERSION:
                messagebox.showinfo("Up to Date", f"You're already on the latest version ({APP_VERSION}).")
                return
            
            
            DOWNLOAD_URL = f"https://github.com/DAH300/Bills_App/releases/download/{latest_version}/Bills.exe"

            # Ask user if they want to update
            if not messagebox.askyesno("Update Available", f"A new version ({latest_version}) is available. Do you want to update?"):
                return

            # Download the update
            tmp_dir = tempfile.mkdtemp()
            new_exe_path = os.path.join(tmp_dir, "Bills_New.exe")
            with requests.get(DOWNLOAD_URL, stream=True) as r:
                r.raise_for_status()
                with open(new_exe_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            # Path to updater.exe (assumes it's next to the current .exe)
            updater_path = os.path.join(os.path.dirname(sys.argv[0]), "updater.exe")
            if not os.path.exists(updater_path):
                messagebox.showerror("Update Error", "Updater not found. Please ensure updater.exe is in the same folder.")
                return

            subprocess.Popen([updater_path, sys.argv[0], new_exe_path])
            self.root.quit()

        except Exception as e:
            messagebox.showerror("Update Error", f"An error occurred:\n{str(e)}")



    def load_bills(self):
        if BILLS_FILE.exists():
            with open(BILLS_FILE, "r") as f:
                data = json.load(f)
                return sorted([Bill.from_dict(b) for b in data], key=lambda b: b.due_date)
        return []

    def save_bills(self):
        with open(BILLS_FILE, "w") as f:
            json.dump([b.to_dict() for b in self.bills], f, indent=4)

    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        self.bills.sort(key=lambda b: b.due_date)
        for i, bill in enumerate(self.bills, 1):
            status = "✅ Paid" if bill.paid else "❌ Not Paid"
            due_status = f"(Due: {bill.due_date})"
            self.listbox.insert(tk.END, f"{i}. {bill.name} - ${bill.amount} - {status} {due_status}")

    def add_bill(self):
        name = simpledialog.askstring("Bill Name", "Enter the bill name:", parent=self.root)
        if not name:
            return

        try:
            amount = float(simpledialog.askstring("Amount", "Enter the amount:", parent=self.root))
        except (TypeError, ValueError):
            messagebox.showerror("Error", "Invalid amount.")
            return

        fixed = messagebox.askyesno("Bill Type", "Is this a fixed bill amount?")
        frequency = simpledialog.askstring("Frequency", "Enter bill frequency (Monthly, 6 Months, Yearly):", initialvalue="Monthly", parent=self.root)
        if frequency not in FREQUENCY_OPTIONS:
            messagebox.showerror("Error", "Invalid frequency. Use 'Monthly', '6 Months', or 'Yearly'.")
            return

        due_date = simpledialog.askstring("Due Date", "Enter due date (YYYY-MM-DD):", parent=self.root)
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format.")
            return

        fixed_day = simpledialog.askinteger("Fixed Due Day", "Enter a fixed day of the month (1-28) or leave blank:", minvalue=1, maxvalue=28, parent=self.root)
        link = simpledialog.askstring("Link", "Enter the bill's website link:", parent=self.root)
        if not link:
            return

        self.bills.append(Bill(name, amount, fixed, due_date, frequency, fixed_day, False, link))
        self.save_bills()
        self.refresh_list()

    def toggle_paid(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo("No selection", "Please select a bill.")
            return

        index = selected[0]
        bill = self.bills[index]

        if not bill.fixed:
            try:
                new_amount = float(simpledialog.askstring("New Amount", f"Enter new amount for {bill.name}:", parent=self.root))
                bill.amount = new_amount
            except (TypeError, ValueError):
                messagebox.showerror("Error", "Invalid amount.")
                return

        bill.paid = not bill.paid

        if bill.paid:
            self.save_bill_history(bill)

        self.save_bills()
        self.refresh_list()

    def open_link(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo("No selection", "Please select a bill.")
            return

        index = selected[0]
        webbrowser.open(self.bills[index].link)

    def update_bills(self):
        today = datetime.today().strftime("%Y-%m-%d")
        for bill in self.bills:
            bill.update_due_date()
        self.save_bills()
        self.refresh_list()
        messagebox.showinfo("Update Complete", "Bills have been updated based on their due dates.")

    def save_bill_history(self, bill):
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        else:
            history = []

        history_entry = {
            "name": bill.name,
            "amount": bill.amount,
            "paid_date": datetime.today().strftime("%Y-%m-%d"),
            "due_date": bill.due_date,
            "frequency": bill.frequency,
            "link": bill.link
        }

        history.append(history_entry)

        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)

    def view_history(self):
        # Open the history file and read the data
        if not HISTORY_FILE.exists():
            messagebox.showinfo("No History", "No history found.")
            return

        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)

        history_window = tk.Toplevel(self.root)
        history_window.transient(self.root)
        history_window.focus_force()
        history_window.title("Bill Payment History")
        history_window.geometry("700x500")

        # Create a Text widget to display history
        notebook = ttk.Notebook(history_window)
        notebook.pack(fill=tk.BOTH, expand=True)

        grouped = {}
        for entry in history:
            grouped.setdefault(entry['name'], []).append(entry)

        for name, entries in grouped.items():
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=name)

            tree = ttk.Treeview(frame, columns=("Amount", "Paid Date", "Due Date"), show='headings')
            tree.heading("Amount", text="Amount Paid")
            tree.heading("Paid Date", text="Paid Date")
            tree.heading("Due Date", text="Due Date")
            tree.column("Amount", width=100, anchor=tk.CENTER)
            tree.column("Paid Date", width=120, anchor=tk.CENTER)
            tree.column("Due Date", width=120, anchor=tk.CENTER)
            tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            for entry in entries:
                tree.insert("", tk.END, values=(f"${entry['amount']:.2f}", entry['paid_date'], entry['due_date']))


if __name__ == "__main__":
    root = tk.Tk()
    app = BillTrackerApp(root)
    root.mainloop()
