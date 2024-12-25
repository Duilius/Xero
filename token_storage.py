import os

def save_refresh_token(refresh_token, file_path="refresh_token.txt"):
    """
    Guarda el refresh_token en un archivo.
    """
    try:
        with open(file_path, "w") as file:
            file.write(refresh_token)
        print("Refresh token guardado correctamente.")
    except Exception as e:
        print(f"Error al guardar el refresh token: {e}")

def load_refresh_token(file_path="refresh_token.txt"):
    """
    Lee el refresh_token desde un archivo.
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as file:
                refresh_token = file.read().strip()
            return refresh_token
        except Exception as e:
            print(f"Error al leer el refresh token: {e}")
            return None
    else:
        print("El archivo de refresh token no existe.")
        return None
