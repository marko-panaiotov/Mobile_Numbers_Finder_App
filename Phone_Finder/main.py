import re
import pyodbc


def extract_name_phone_pairs(text):
    pattern = r'(?:([A-Z][a-z]+\s[A-Z][a-z]+)[^\d]+)?(\+\d{1,3})?[-.\s]?(\(?\d{3}\)?)?[-.\s]?(\d{3})[-.\s]?(\d{4,5})'
    matches = re.findall(pattern, text)
    cleaned_matches = []

    for name, part2, part3, part4, part5 in matches:
        phone_number = f"{part2 or ''}{'-' if part2 else ''}{part3.replace('(', '').replace(')', '')}-{part4}-{part5}"
        phone_number = phone_number.replace('--', '-')  # Уверяваме се, че няма двойни тирета
        cleaned_matches.append((name.strip() if name else "Unknown", phone_number))

    return cleaned_matches
# def extract_name_phone_pairs(text):
#     pattern = r'(?:([A-Z][a-z]+\s[A-Z][a-z]+)[^\d]+)?\(?\+?(\d{1,3})\)?[-.\s]?(\d{3})[-.\s]?(\d{3})[-.\s]?(\d{4,5})'
#     matches = re.findall(pattern, text)
#     cleaned_matches = []
#
#     for name, part1, part2, part3, part4 in matches:
#         country_code = f"+{part1}" if part1 else ""
#         phone_number = f"{country_code}-{part2}-{part3}-{part4}"
#         cleaned_matches.append((name.strip() if name else "Unknown", phone_number))
#
#     return cleaned_matches
def save_to_database(name, phone):
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 18 for SQL Server};'
        'SERVER=192.168.1.72;'
        'DATABASE=Phone_Finder_DB;'
        'UID=sa;'
        'PWD=MSSQLdb!2;'
        'TrustServerCertificate=yes;'
    )
    cursor = conn.cursor()
    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'contacts')
        CREATE TABLE contacts (name NVARCHAR(255), phone NVARCHAR(50))
    """)
    cursor.execute("INSERT INTO contacts (name, phone) VALUES (?, ?)", (name, phone))
    conn.commit()
    conn.close()

def process_text(text):
    name_phone_pairs = extract_name_phone_pairs(text)
    for name, phone in name_phone_pairs:
        save_to_database(name, phone)
        print(f"Saved: {name} - {phone}")

if __name__ == "__main__":
    sample_text = "John Doe's phone number is +1-800-555-0199. You can also reach Jane Smith at (202) 555-0136. E +359-98888888."
    process_text(sample_text)

