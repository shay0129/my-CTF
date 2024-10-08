import os
from cryptography.fernet import Fernet
import base64
import secrets

def generate_key():
    random_part = secrets.token_bytes(28)
    key = b"DZDZ" + random_part
    return base64.urlsafe_b64encode(key)

def encrypt_file(file_path, key):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    f = Fernet(key)
    with open(file_path, 'rb') as file:
        file_data = file.read()
    return f.encrypt(file_data)

def append_data_to_pdf(pdf_path, data, identifier):
    with open(pdf_path, 'ab') as pdf_file:
        pdf_file.write(f"\n%%{identifier}%%\n".encode())
        pdf_file.write(base64.b64encode(data))
        pdf_file.write(f"\n%%END{identifier}%%\n".encode())

def extract_data_from_pdf(pdf_path, identifier):
    with open(pdf_path, 'rb') as pdf_file:
        content = pdf_file.read()
    start_marker = f"\n%%{identifier}%%\n".encode()
    end_marker = f"\n%%END{identifier}%%\n".encode()
    start = content.find(start_marker) + len(start_marker)
    end = content.find(end_marker, start)
    if start != -1 and end != -1:
        return base64.b64decode(content[start:end])
    return None

def find_positions(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        content = pdf_file.read()
    key_pos = content.find(b"%%ENCRYPTION_KEY%%")
    client_pos = content.find(b"%%ENCRYPTED_CLIENT%%")
    return key_pos, client_pos

def main():
    pdf_file = input("Enter the full path of the PDF file to hide data in: ")
    server_py = input("Enter the full path of the server Python file (e.g., ../communication/server.py): ")
    client_py = input("Enter the full path of the client Python file (e.g., ../communication/server.py): ")

    # בדיקה אם הנתיבים תקינים
    if not os.path.exists(pdf_file):
        print(f"Error: The PDF file '{pdf_file}' does not exist.")
        return

    if not os.path.exists(server_py):
        print(f"Error: The server file '{server_py}' does not exist.")
        return

    if not os.path.exists(client_py):
        print(f"Error: The client file '{client_py}' does not exist.")
        return

    try:
        # 1. הסתרת server.py כפי שהוא
        with open(server_py, 'rb') as file:
            server_data = file.read()
        append_data_to_pdf(pdf_file, server_data, 'SERVER_PY')
        print(f"Server Python file hidden in {pdf_file}")

        # 2. יצירת מפתח קבוע והסתרתו
        key = generate_key()
        append_data_to_pdf(pdf_file, key, 'ENCRYPTION_KEY')
        print(f"Encryption key hidden in {pdf_file}")
        print(f"The encryption key is: {key.decode()}")  # הדפסת המפתח

        # 3. הצפנת client.py והסתרתו
        encrypted_client = encrypt_file(client_py, key)
        append_data_to_pdf(pdf_file, encrypted_client, 'ENCRYPTED_CLIENT')
        print(f"Encrypted client Python file hidden in {pdf_file}")

        print("Process completed successfully.")

        # חילוץ והשוואת מיקומים
        extracted_client = extract_data_from_pdf(pdf_file, 'ENCRYPTED_CLIENT')
        if extracted_client:
            output_dir = os.path.dirname(pdf_file)
            extracted_file_path = os.path.join(output_dir, 'extracted_encrypted_client.py')
            with open(extracted_file_path, 'wb') as file:
                file.write(extracted_client)
            print(f"Extracted encrypted client.py saved as '{extracted_file_path}'")
            
            key_pos, client_pos = find_positions(pdf_file)
            print(f"Encryption key position in PDF: {key_pos}")
            print(f"Encrypted client position in PDF: {client_pos}")
            if key_pos < client_pos:
                print("The encryption key appears before the encrypted client in the PDF.")
            else:
                print("The encrypted client appears before the encryption key in the PDF.")
        else:
            print("Failed to extract encrypted client from PDF.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()