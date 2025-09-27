import hashlib

def hash_password(password):
    """Hashear contraseña para almacenar en la BD"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verificar contraseña contra hash"""
    return hash_password(password) == password_hash

# Ejemplo de uso para crear usuarios
if __name__ == "__main__":
    # Generar hashes para nuevas contraseñas
    passwords = {
        "password": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
        "admin": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",
        "ctsc2024": "hash_generado_aqui"
    }
    
    for pwd, expected_hash in passwords.items():
        actual_hash = hash_password(pwd)
        print(f"'{pwd}' -> {actual_hash}")
        print(f"Verificación: {actual_hash == expected_hash}")