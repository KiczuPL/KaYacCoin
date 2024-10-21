import tkinter as tk
from tkinter import messagebox
from wallet import create_identity, save_identity_to_file
from encryption import decrypt_identity  # Import the decryption function
import json
import base64

def generate_identity():
    """Handle the identity generation and saving process."""
    name = entry_name.get()
    password = entry_password.get()

    if not name or not password:
        messagebox.showerror("Input Error", "Please fill in both fields.")
        return

    # Create identity
    identity = create_identity(name)

    # Save identity to file
    try:
        save_identity_to_file(identity, password, 'identity.json')
        messagebox.showinfo("Success", f"Identity for '{name}' has been saved successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while saving: {str(e)}")

def load_and_decrypt_identity():
    """Load and decrypt the saved identity from the JSON file."""
    password = entry_password.get()

    if not password:
        messagebox.showerror("Input Error", "Please enter your password.")
        return

    try:
        with open('identity.json', 'r') as json_file:
            identity_json = json.load(json_file)
        
        # Base64 decode the encrypted data, salt, and IV
        encrypted_data = base64.b64decode(identity_json['encrypted_data'])
        salt = base64.b64decode(identity_json['salt'])
        iv = base64.b64decode(identity_json['iv'])

        # Decrypt the identity
        decrypted_identity = decrypt_identity(encrypted_data, password, salt, iv)
        messagebox.showinfo("Decrypted Identity", f"Identity:\n{decrypted_identity}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while loading/decrypting: {str(e)}")

# Create the main application window
root = tk.Tk()
root.title("Crypto Wallet Identity Generator")

# Create and place labels and entry fields
label_name = tk.Label(root, text="Identity Name:")
label_name.pack(pady=5)

entry_name = tk.Entry(root, width=30)
entry_name.pack(pady=5)

label_password = tk.Label(root, text="Password:")
label_password.pack(pady=5)

entry_password = tk.Entry(root, show='*', width=30)
entry_password.pack(pady=5)

# Create and place the generate button
button_generate = tk.Button(root, text="Generate Identity", command=generate_identity)
button_generate.pack(pady=10)

# Create and place the load button
button_load = tk.Button(root, text="Load and Decrypt Identity", command=load_and_decrypt_identity)
button_load.pack(pady=10)

# Run the application
root.mainloop()
