import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
from math import ceil
import os
import datetime

# Create a SQLite database for storing contacts
conn = sqlite3.connect('contacts.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        address TEXT
    )
''')
conn.commit()
conn.close()

# Create the main application window
app = tk.Tk()
app.title("Contact Management App")

# Global variables for pagination and search results
current_page = 1
page_size = 50
search_query = ""

# Functions for CRUD operations

def add_contact():
    name = name_entry.get()
    phone = phone_entry.get()
    email = email_entry.get()
    address = address_entry.get()
    
    if name:
        conn = sqlite3.connect('contacts.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO contacts (name, phone, email, address) VALUES (?, ?, ?, ?)", (name, phone, email, address))
        conn.commit()
        conn.close()
        clear_entries()
        display_contacts()
    else:
        messagebox.showerror("Error", "Name field is required.")

def edit_contact(event=None):
    selected_contact = contact_tree.selection()
    if selected_contact:
        contact_id = contact_tree.item(selected_contact, 'values')[0]
        new_name = name_entry.get()
        new_phone = phone_entry.get()
        new_email = email_entry.get()
        new_address = address_entry.get()
        
        if contact_id:
            conn = sqlite3.connect('contacts.db')
            cursor = conn.cursor()
            
            # Build the UPDATE statement dynamically based on which fields are not empty
            update_values = []
            if new_name:
                update_values.append(("name", new_name))
            if new_phone:
                update_values.append(("phone", new_phone))
            if new_email:
                update_values.append(("email", new_email))
            if new_address:
                update_values.append(("address", new_address))
            
            # Construct the SQL query
            update_query = "UPDATE contacts SET " + ", ".join([f"{field} = ?" for field, _ in update_values])
            update_query += " WHERE id = ?"
            
            # Extract values for the query
            update_params = [value for _, value in update_values] + [contact_id]
            
            cursor.execute(update_query, update_params)
            conn.commit()
            conn.close()
            clear_entries()
            display_contacts()
            messagebox.showinfo("Edit Successful", "Contact edited successfully.")
        else:
            messagebox.showerror("Error", "Contact not found.")
    else:
        messagebox.showerror("Error", "Please select a contact to edit.")

def delete_contact(event):
    selected_contact = contact_tree.selection()
    if selected_contact:
        contact_id = contact_tree.item(selected_contact, 'values')[0]
        conn = sqlite3.connect('contacts.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contacts WHERE id=?", (contact_id,))
        conn.commit()
        conn.close()
        display_contacts()
    else:
        messagebox.showerror("Error", "Please select a contact to delete.")

def clear_entries():
    name_entry.delete(0, tk.END)
    phone_entry.delete(0, tk.END)
    email_entry.delete(0, tk.END)
    address_entry.delete(0, tk.END)

def display_contacts():
    global current_page, search_query
    conn = sqlite3.connect('contacts.db')
    cursor = conn.cursor()
    
    # Calculate the OFFSET based on the current page and page size
    offset = (current_page - 1) * page_size
    
    if search_query:
        # Search for contacts by name, email, or address
        cursor.execute("SELECT * FROM contacts WHERE name LIKE ? OR email LIKE ? OR address LIKE ? LIMIT ? OFFSET ?", 
                       (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', page_size, offset))
    else:
        cursor.execute("SELECT * FROM contacts LIMIT ? OFFSET ?", (page_size, offset))
    
    contacts = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM contacts WHERE name LIKE ? OR email LIKE ? OR address LIKE ?", 
                   (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
    total_contacts = cursor.fetchone()[0]
    
    conn.close()
    
    contact_tree.delete(*contact_tree.get_children())
    
    for contact in contacts:
        contact_tree.insert('', 'end', values=contact)
    
    # Calculate the total number of pages
    total_pages = ceil(total_contacts / page_size)
    
    status_label.config(text=f"Page {current_page} of {total_pages} | Total Contacts: {total_contacts}")

# Function for importing contacts from a CSV file
def import_csv():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])

    if file_path:
        try:
            with open(file_path, 'r', newline='') as csvfile:
                csvreader = csv.DictReader(csvfile)
                conn = sqlite3.connect('contacts.db')
                cursor = conn.cursor()

                for row in csvreader:
                    name = row.get('Name', '')
                    phone = row.get('Phone', '')
                    email = row.get('Email', '')
                    address = row.get('Address', '')

                    cursor.execute("INSERT INTO contacts (name, phone, email, address) VALUES (?, ?, ?, ?)", (name, phone, email, address))

                conn.commit()
                conn.close()
                current_page = 1  # Reset to the first page after import
                display_contacts()
                messagebox.showinfo("Import Successful", "Contacts imported successfully from CSV.")
        except Exception as e:
            messagebox.showerror("Error", f"Error importing CSV: {str(e)}")

# Function to navigate to the next page
def next_page():
    global current_page
    current_page += 1
    display_contacts()

# Function to navigate to the previous page
def prev_page():
    global current_page
    if current_page > 1:
        current_page -= 1
        display_contacts()

# Function to perform a search
def search_contacts():
    global current_page, search_query
    search_query = search_entry.get()
    current_page = 1  # Reset to the first page after a new search
    display_contacts()

# Function to display About information
def display_about_info():
    about_info = """
    Contact Management App

    Description:
    This application allows you to manage your contacts.

    Creator: Swathik Devadiga
    Version: 1.0
    Last Modified: {}
    """.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    messagebox.showinfo("About", about_info)

# Function to handle double-click on a contact
def on_double_click(event):
    item = contact_tree.selection()
    if item:
        contact_id = contact_tree.item(item, 'values')[0]
        if contact_id:
            edit_window = tk.Toplevel(app)
            edit_window.title("Edit Contact")
            
            # Fetch contact details from the database
            conn = sqlite3.connect('contacts.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contacts WHERE id=?", (contact_id,))
            contact_details = cursor.fetchone()
            conn.close()
            
            # Create and populate the edit form
            edit_frame = ttk.Frame(edit_window)
            edit_frame.grid(row=0, column=0, padx=10, pady=10)
            
            name_label = tk.Label(edit_frame, text="Name:")
            name_label.grid(row=0, column=0)
            name_entry = ttk.Entry(edit_frame, width=70, style="Rounded.TEntry")
            name_entry.grid(row=0, column=1)
            name_entry.insert(0, contact_details[1])  # Populate with existing name
            
            phone_label = tk.Label(edit_frame, text="Phone:")
            phone_label.grid(row=1, column=0)
            phone_entry = ttk.Entry(edit_frame, width=70, style="Rounded.TEntry")
            phone_entry.grid(row=1, column=1)
            phone_entry.insert(0, contact_details[2])  # Populate with existing phone number
            
            email_label = tk.Label(edit_frame, text="Email:")
            email_label.grid(row=2, column=0)
            email_entry = ttk.Entry(edit_frame, width=70, style="Rounded.TEntry")
            email_entry.grid(row=2, column=1)
            email_entry.insert(0, contact_details[3])  # Populate with existing email
            
            address_label = tk.Label(edit_frame, text="Address:")
            address_label.grid(row=3, column=0)
            address_entry = ttk.Entry(edit_frame, width=70, style="Rounded.TEntry")
            address_entry.grid(row=3, column=1)
            address_entry.insert(0, contact_details[4])  # Populate with existing address
            
            # Function to update the contact details
            def update_contact():
                updated_name = name_entry.get()
                updated_phone = phone_entry.get()
                updated_email = email_entry.get()
                updated_address = address_entry.get()
                
                if updated_name:
                    conn = sqlite3.connect('contacts.db')
                    cursor = conn.cursor()
                    cursor.execute("UPDATE contacts SET name=?, phone=?, email=?, address=? WHERE id=?",
                                   (updated_name, updated_phone, updated_email, updated_address, contact_id))
                    conn.commit()
                    conn.close()
                    edit_window.destroy()
                    display_contacts()
                    messagebox.showinfo("Update Successful", "Contact updated successfully.")
                else:
                    messagebox.showerror("Error", "Name field is required.")
            
            # Create an "Update Contact" button with rounded edges
            style = ttk.Style()
            style.configure("RoundedButton.TButton", borderwidth=0, relief="flat", padding=5)
            update_button = ttk.Button(edit_frame, text="Update Contact", style="RoundedButton.TButton", command=update_contact)
            update_button.grid(row=4, columnspan=2, pady=5)
            
            edit_window.mainloop()

# Create user interface components

# Create a Frame for the Create Form and Add Button
create_frame = ttk.Frame(app)
create_frame.grid(row=0, column=0, padx=10, pady=10, sticky="w")

name_label = tk.Label(create_frame, text="Name:")
name_label.grid(row=0, column=0)
name_entry = ttk.Entry(create_frame, style="Rounded.TEntry")
name_entry.grid(row=1, column=0)

phone_label = tk.Label(create_frame, text="Phone:")
phone_label.grid(row=0, column=1)
phone_entry = ttk.Entry(create_frame, style="Rounded.TEntry")
phone_entry.grid(row=1, column=1)

email_label = tk.Label(create_frame, text="Email:")
email_label.grid(row=0, column=2)
email_entry = ttk.Entry(create_frame, style="Rounded.TEntry")
email_entry.grid(row=1, column=2)

address_label = tk.Label(create_frame, text="Address:")
address_label.grid(row=0, column=3)
address_entry = ttk.Entry(create_frame, style="Rounded.TEntry")
address_entry.grid(row=1, column=3)

# Create a custom style for the "Add Contact" button with rounded edges
style = ttk.Style()
style.configure("RoundedButton.TButton", borderwidth=0, relief="flat", padding=5)
add_button = ttk.Button(create_frame, text="Add Contact", style="RoundedButton.TButton", command=add_contact)
add_button.grid(row=4, columnspan=4, pady=5)

# Create a custom style for the rounded search box
rounded_search_style = ttk.Style()
rounded_search_style.configure("Rounded.TEntry", borderwidth=1, relief="solid", padding=5, foreground="black")

# Create a search frame with an Entry and Search button
search_frame = ttk.Frame(app)
search_frame.grid(row=0, column=1, padx=10, pady=10, sticky="e")

search_entry = ttk.Entry(search_frame, style="Rounded.TEntry")
search_entry.grid(row=1, column=1)

search_button = ttk.Button(search_frame, text="Search", command=search_contacts, style="RoundedButton.TButton")
search_button.grid(row=1, column=2, padx=5)

# Create an "About" button
about_button = ttk.Button(app, text="About", command=display_about_info, style="RoundedButton.TButton")
about_button.grid(row=0, column=2, padx=10, pady=5, sticky="ne")

# Create a Treeview widget to display contacts in a tabular format
contact_tree = ttk.Treeview(app, columns=("ID", "Name", "Phone", "Email", "Address"), show="headings")
contact_tree.heading("ID", text="ID")
contact_tree.heading("Name", text="Name")
contact_tree.heading("Phone", text="Phone")
contact_tree.heading("Email", text="Email")
contact_tree.heading("Address", text="Address")

contact_tree.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

# Create an "Import CSV" button at the top right
import_csv_button = ttk.Button(app, text="Import CSV", command=import_csv, style="RoundedButton.TButton")
import_csv_button.grid(row=0, column=2, padx=10, pady=5, sticky="e")

prev_button = ttk.Button(app, text="Previous Page", command=prev_page, style="RoundedButton.TButton")
prev_button.grid(row=2, column=0, sticky='w', padx=10, pady=5)

next_button = ttk.Button(app, text="Next Page", command=next_page, style="RoundedButton.TButton")
next_button.grid(row=2, column=2, sticky='e', padx=10, pady=5)

status_label = tk.Label(app, text="", anchor="e")
status_label.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="e")

# Configure grid row and column weights for resizing
app.grid_rowconfigure(1, weight=1)
app.grid_columnconfigure(0, weight=1)

# Bind double-click event to the contact_tree
contact_tree.bind("<Double-1>", on_double_click)

display_contacts()

# Add right-click context menu for editing and deleting contacts
contact_tree.bind("<Button-3>", lambda event: contact_tree_popup(event))

def contact_tree_popup(event):
    popup_menu = tk.Menu(app, tearoff=0)
    popup_menu.add_command(label="Edit Contact", command=lambda: on_double_click(event))
    popup_menu.add_command(label="Delete Contact", command=lambda: delete_contact(event))
    popup_menu.post(event.x_root, event.y_root)

app.mainloop()
