import re
import phonenumbers
from phonenumbers import geocoder
import pyodbc

# Конфигурация на MSSQL
DB_CONNECTION = ("DRIVER={ODBC Driver 18 for SQL Server};"
                 "SERVER=192.168.1.72;"
                 "DATABASE=Phone_Finder_DB;"
                 "UID=sa;"
                 "PWD=MSSQLdb!2;"
                 "TrustServerCertificate=yes;"
                 )

def create_table():
    try:
        conn = pyodbc.connect(DB_CONNECTION)
        cursor = conn.cursor()
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'PhoneBook')
            CREATE TABLE PhoneBook (
                id INT IDENTITY(1,1) PRIMARY KEY,
                name NVARCHAR(255),
                phone NVARCHAR(50),
                country NVARCHAR(100)
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")


def extract_phone_numbers(text):
    phone_pattern = re.compile(
        r'\(\+?\d{1,4}\)\s?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}|\+?\d{1,4}[\s\-\(]?\d{1,4}[\)\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}')
    matches = phone_pattern.finditer(text)
    valid_numbers = []

    for match in matches:
        phone = match.group()
        try:
            parsed_number = phonenumbers.parse(phone, None)
            if not phonenumbers.is_valid_number(parsed_number):
                parsed_number = phonenumbers.parse(phone, "US")

            if phonenumbers.is_valid_number(parsed_number):
                country = geocoder.description_for_number(parsed_number, "en")
                valid_numbers.append((phone, country, match.start()))
        except:
            continue

    return valid_numbers


def extract_names(text):
    name_pattern = re.compile(r'([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})*)')
    matches = [(m.group(), m.start()) for m in name_pattern.finditer(text)]
    return matches


def find_names_for_phones(text, phones):
    names = extract_names(text)
    name_phone_pairs = []

    for phone, country, phone_index in phones:
        closest_name = "Unknown"
        for name, name_index in names:
            if name_index < phone_index:
                closest_name = name
            else:
                break
        name_phone_pairs.append((closest_name, phone, country))

    return name_phone_pairs


def save_to_database(name, phone, country):
    try:
        conn = pyodbc.connect(DB_CONNECTION)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO PhoneBook (name, phone, country) VALUES (?, ?, ?)", (name, phone, country))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")


def process_text(text):
    phone_data = extract_phone_numbers(text)
    matched_data = find_names_for_phones(text, phone_data)
    knowledge_base = []

    for name, phone, country in matched_data:
        knowledge_base.append({"name": name, "phone": phone, "country": country})
        save_to_database(name, phone, country)

    return knowledge_base



if __name__ == "__main__":
    # Инициализиране на базата данни
    create_table()

    # Тестов пример
    test_text = "John Doe's number is +1 763-453-4598. Maria Fox's number is (+44) 20 7946 0958. Dr. James Smith can be reached at (+359) 456-7890. Another number is +91-9876543210. (49) 30 1234 5678 belongs to Peter Parker. Contact ( +33 ) 1 23 45 67 89 for more info."
    result = process_text(test_text)
    print(result)

