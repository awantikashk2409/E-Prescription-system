


import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import json
import os
from datetime import datetime
from fuzzywuzzy import process

# --- Global Variables and Database Functions ---
DB_FILE = 'medicines_db.json'
medicines_db = []
current_prescription = []

def load_database():
    """Loads the medicine database from the JSON file."""
    global medicines_db
    if not os.path.exists(DB_FILE):
        medicines_db = []
        return
    try:
        with open(DB_FILE, 'r') as f:
            medicines_db = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        medicines_db = []

def save_database():
    """Saves the current medicine database to the JSON file."""
    with open(DB_FILE, 'w') as f:
        json.dump(medicines_db, f, indent=4)

# --- Spelling and Data Management Functions ---
def get_all_symptoms():
    """Extracts a list of all unique symptoms from the database."""
    all_symptoms = set()
    for med in medicines_db:
        symptoms = [s.strip() for s in med.get('symptoms', '').split(',') if s.strip()]
        all_symptoms.update(symptoms)
    return list(all_symptoms)

def correct_symptoms(symptoms_str):
    """Corrects/Standardizes symptom spellings using FuzzyWuzzy against existing symptoms."""
    existing_symptoms = get_all_symptoms()
    input_symptoms = [s.strip() for s in symptoms_str.split(',') if s.strip()]
    corrected_list = []

    for sym in input_symptoms:
        if not existing_symptoms:
            corrected_list.append(sym.title())
            continue
        
        match, score = process.extractOne(sym, existing_symptoms)
        
        if score > 80:
            corrected_list.append(match)
        else:
            corrected_list.append(sym.title())

    return ', '.join(sorted(list(set(corrected_list))))

# --- GUI Related Functions ---

class AddMedicineWindow(simpledialog.Dialog):
    """A pop-up window to add a new medicine."""
    def body(self, master):
        self.title("Add New Medicine")
        tk.Label(master, text="Medicine Name:").grid(row=0, sticky="w")
        tk.Label(master, text="Dosage (e.g., 500mg):").grid(row=1, sticky="w")
        tk.Label(master, text="Symptoms (e.g., Fever, Pain):").grid(row=2, sticky="w")

        self.name_entry = tk.Entry(master, width=30)
        self.dosage_entry = tk.Entry(master, width=30)
        self.symptoms_entry = tk.Entry(master, width=30)
        
        self.name_entry.grid(row=0, column=1)
        self.dosage_entry.grid(row=1, column=1)
        self.symptoms_entry.grid(row=2, column=1)
        
        self.result = None
        return self.name_entry

    def apply(self):
        name = self.name_entry.get().strip().title()
        dosage = self.dosage_entry.get().strip()
        symptoms_raw = self.symptoms_entry.get().strip()

        if not name or not dosage or not symptoms_raw:
            messagebox.showerror("Error", "All fields are required!")
            self.result = None
            return

        if any(med['name'].lower() == name.lower() for med in medicines_db):
            messagebox.showerror("Error", f"Medicine '{name}' already exists in the database.")
            self.result = None
            return

        corrected_syms = correct_symptoms(symptoms_raw)
        
        self.result = {
            "name": name,
            "dosage": dosage,
            "symptoms": corrected_syms
        }

def update_search_results(event=None):
    """Updates the medicine listbox as the user types in the search entry."""
    search_term = search_entry.get().lower()
    search_results_listbox.delete(0, tk.END)

    if not search_term:
        return

    results = []
    for med in medicines_db:
        if med['name'].lower().startswith(search_term):
            results.append(med)
        elif search_term in med['symptoms'].lower():
            if med not in results:
                results.append(med)
    
    if not results:
        search_results_listbox.insert(tk.END, "No medicine found. Click 'Add New'.")
    else:
        for med in results:
            search_results_listbox.insert(tk.END, f"{med['name']} ({med['dosage']})")

def add_selected_to_prescription():
    """Adds the selected medicine from the listbox to the prescription."""
    selected_indices = search_results_listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("Warning", "Please select a medicine from the list.")
        return

    selected_text = search_results_listbox.get(selected_indices[0])
    med_name_to_find = selected_text.split(' (')[0]
    
    found_med = next((med for med in medicines_db if med['name'] == med_name_to_find), None)

    if found_med:
        current_prescription.append(found_med)
        update_prescription_display()
    else:
        messagebox.showerror("Error", "Selected medicine not found in the database.")

def add_new_medicine_flow():
    """Initiates the flow to add a new medicine."""
    dialog = AddMedicineWindow(root)
    new_med = dialog.result
    
    if new_med:
        medicines_db.append(new_med)
        save_database()
        messagebox.showinfo("Success", f"'{new_med['name']}' has been added to the database.")
        current_prescription.append(new_med)
        update_prescription_display()
        search_entry.delete(0, tk.END)
        update_search_results()

def update_prescription_display():
    """Updates the prescription text area with the current list of medicines."""
    prescription_text_area.config(state=tk.NORMAL)
    prescription_text_area.delete('1.0', tk.END)
    
    if not current_prescription:
        prescription_text_area.config(state=tk.DISABLED)
        return
        
    prescription_text_area.insert(tk.END, "--- Rx ---\n\n")
    for i, med in enumerate(current_prescription, 1):
        prescription_text_area.insert(tk.END, f"{i}. {med['name']} ({med['dosage']})\n")
    
    prescription_text_area.config(state=tk.DISABLED)

def generate_and_save_prescription():
    """Generates the final prescription and saves it to a text file."""
    p_name = patient_name_entry.get().strip()
    p_age = patient_age_entry.get().strip()

    if not p_name or not p_age:
        messagebox.showerror("Error", "Patient Name and Age are required.")
        return
    if not current_prescription:
        messagebox.showerror("Error", "The prescription is empty. Please add medicines.")
        return

    timestamp = datetime.now().strftime("%d-%b-%Y %I:%M %p")
    
    prescription_content = f"""
{'='*50}
            ** MEDICAL PRESCRIPTION **
{'='*50}

Patient Name: {p_name.title()}
Patient Age: {p_age}
Date: {timestamp}

{'-'*50}
Rx:
{'-'*50}
"""
    for i, med in enumerate(current_prescription, 1):
        prescription_content += f"\n{i}. {med['name']} ({med['dosage']})"

    prescription_content += f"\n\n{'='*50}"
    
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        title="Save Prescription",
        initialfile=f"Prescription_{p_name.replace(' ', '_')}.txt"
    )

    if file_path:
        with open(file_path, 'w') as f:
            f.write(prescription_content)
        messagebox.showinfo("Success", f"Prescription successfully saved to '{os.path.basename(file_path)}'.")
        start_new_prescription()

def start_new_prescription():
    """Resets the screen for a new prescription."""
    global current_prescription
    current_prescription = []
    patient_name_entry.delete(0, tk.END)
    patient_age_entry.delete(0, tk.END)
    search_entry.delete(0, tk.END)
    update_search_results()
    update_prescription_display()
    patient_name_entry.focus_set()

# --- Main GUI Setup ---
if __name__ == "__main__":
    load_database()

    root = tk.Tk()
    root.title("E-Prescription Tool")
    root.geometry("800x600")

    # --- Top Frame: Patient Information ---
    patient_frame = tk.LabelFrame(root, text="Patient Information", padx=10, pady=10)
    patient_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(patient_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5)
    patient_name_entry = tk.Entry(patient_frame, width=30)
    patient_name_entry.grid(row=0, column=1, padx=5, pady=5)
    
    tk.Label(patient_frame, text="Age:").grid(row=0, column=2, padx=5, pady=5)
    patient_age_entry = tk.Entry(patient_frame, width=10)
    patient_age_entry.grid(row=0, column=3, padx=5, pady=5)

    # --- Main Frame: Search and Prescription ---
    main_frame = tk.Frame(root, padx=10, pady=5)
    main_frame.pack(fill="both", expand=True)

    # --- Left Side: Medicine Search ---
    search_frame = tk.LabelFrame(main_frame, text="Search Medicine", padx=10, pady=10)
    search_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

    search_entry = tk.Entry(search_frame)
    search_entry.pack(fill="x")
    search_entry.bind("<KeyRelease>", update_search_results)

    search_results_listbox = tk.Listbox(search_frame, height=15)
    search_results_listbox.pack(fill="both", expand=True, pady=5)

    btn_frame = tk.Frame(search_frame)
    btn_frame.pack(fill="x")
    
    add_selected_btn = tk.Button(btn_frame, text="Add to Prescription", command=add_selected_to_prescription)
    add_selected_btn.pack(side="left", fill="x", expand=True, padx=(0,2))
    
    add_new_btn = tk.Button(btn_frame, text="Add New Medicine", command=add_new_medicine_flow)
    add_new_btn.pack(side="left", fill="x", expand=True, padx=(2,0))
    
    # --- Right Side: Current Prescription ---
    prescription_frame = tk.LabelFrame(main_frame, text="Current Prescription", padx=10, pady=10)
    prescription_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

    prescription_text_area = tk.Text(prescription_frame, height=15, state=tk.DISABLED, bg="#f0f0f0")
    prescription_text_area.pack(fill="both", expand=True)

    # --- Bottom Frame: Action Buttons ---
    action_frame = tk.Frame(root, pady=10)
    action_frame.pack(fill="x", padx=10)

    generate_btn = tk.Button(action_frame, text="Generate & Save Prescription", bg="#4CAF50", fg="white", height=2, command=generate_and_save_prescription)
    generate_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
    
    new_rx_btn = tk.Button(action_frame, text="New Prescription", bg="#f44336", fg="white", height=2, command=start_new_prescription)
    new_rx_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

    start_new_prescription()
    root.mainloop()