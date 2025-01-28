import sqlite3
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import csv
import json
from ollama import ask as ollama_ask

# Function to initialize the database
def initialize_database(db_path):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # Create tables if they don't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS organizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS request_letters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient TEXT NOT NULL,
        recipient_name TEXT NOT NULL,
        subject TEXT NOT NULL,
        content TEXT NOT NULL,
        date TEXT NOT NULL
    );
    """)

    connection.commit()
    connection.close()

# Function to fetch data from SQLite
def fetch_data_from_db(db_path, query):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    connection.close()
    return data

# Function to generate a default template PDF
def generate_default_template(output_file):
    c = canvas.Canvas(output_file, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 100, "Report Header (Add Your Organization Header Here)")
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 140, "This is a default template.")
    c.save()

# Function to generate a request letter PDF
def generate_request_letter(output_file, organization_name, request_details):
    c = canvas.Canvas(output_file, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 100, f"Request Letter - {organization_name}")
    c.setFont("Helvetica", 12)

    c.drawString(100, height - 140, f"Date: {request_details['date']}")
    c.drawString(100, height - 160, f"To: {request_details['recipient']}")
    c.drawString(100, height - 180, f"Subject: {request_details['subject']}")

    c.drawString(100, height - 220, f"Dear {request_details['recipient_name']},")
    c.drawString(100, height - 260, f"{request_details['content']}")

    c.drawString(100, height - 300, f"Sincerely,")
    c.drawString(100, height - 320, organization_name)
    c.save()

# Function to process OSINT data files
def process_osint_data(file_path):
    if file_path.endswith(".csv"):
        with open(file_path, newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            data = [row for row in reader]
    elif file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as jsonfile:
            data = json.load(jsonfile)
    elif file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as txtfile:
            data = txtfile.readlines()
    else:
        raise ValueError("Unsupported file format. Please provide a CSV, JSON, or text file.")
    return data

# Function to generate OSINT report using Ollama
def generate_osint_report(output_file, organization_name, osint_data):
    c = canvas.Canvas(output_file, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 100, f"OSINT Report - {organization_name}")
    c.setFont("Helvetica", 12)

    y = height - 140
    for entry in osint_data:
        if isinstance(entry, dict):
            text = ollama_ask(f"Generate OSINT report entry based on the following data: {entry}")
        else:
            text = ollama_ask(f"Generate OSINT report entry based on the following text: {entry}")
        
        if y < 100:  # Add new page if space is insufficient
            c.showPage()
            y = height - 100
        c.drawString(100, y, text)
        y -= 40

    c.save()

# Main function
if __name__ == "__main__":
    db_path = "data.sqlite"

    # Initialize database and insert sample data if necessary
    initialize_database(db_path)

    # Ask user which report to generate
    print("Which report would you like to generate?")
    print("1. Request Letter")
    print("2. OSINT Report")
    choice = input("Enter the number corresponding to your choice: ")

    # Get the organization name from the database
    organization_query = "SELECT name FROM organizations WHERE id = 1"
    organization_data = fetch_data_from_db(db_path, organization_query)
    organization_name = organization_data[0][0] if organization_data else "Your Organization"

    if choice == "1":
        # Fetch request letter details
        request_query = "SELECT recipient, recipient_name, subject, content, date FROM request_letters WHERE id = 1"
        request_data = fetch_data_from_db(db_path, request_query)
        request_details = {
            "recipient": request_data[0][0],
            "recipient_name": request_data[0][1],
            "subject": request_data[0][2],
            "content": request_data[0][3],
            "date": request_data[0][4],
        }

        # Ask for a template file
        template_file = input("Provide the path to the template file (or press Enter to use default): ")
        if not template_file:
            template_file = "default_template.pdf"
            generate_default_template(template_file)

        # Generate Request Letter
        output_file = "request_letter.pdf"
        generate_request_letter(output_file, organization_name, request_details)
        print(f"Request Letter saved as {output_file}")

    elif choice == "2":
        # Process OSINT data
        data_file = input("Provide the path to the OSINT data file (CSV, JSON, or TXT): ")
        osint_data = process_osint_data(data_file)

        # Generate OSINT Report
        output_file = "osint_report.pdf"
        generate_osint_report(output_file, organization_name, osint_data)
        print(f"OSINT Report saved as {output_file}")

    else:
        print("Invalid choice. Exiting.")

