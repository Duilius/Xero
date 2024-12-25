import requests

# Datos necesarios
url = "https://identity.xero.com/connect/token"
headers = {"Content-Type": "application/x-www-form-urlencoded"}
data = {
    "grant_type": "authorization_code",
    "code": "fEUNJy3Q-m4p3BZPgL5FuTYnMeAl-KkIcfveGqEHRRc",  # Reemplaza con tu código
    "redirect_uri": "http://localhost:8080/callback",  # Debe coincidir con el que configuraste
    "client_id": "3E305E012630460796C6F87D7753615F",  # Reemplaza con tu Client ID
    "client_secret": "H1XP-raPTjaipa_VHvYEJSwb3KjWP8Od3U4sgFvUAh1yzLpj"  # Reemplaza con tu Client Secret
}

# Realiza la solicitud POST
response = requests.post(url, headers=headers, data=data)

# Manejo de la respuesta
if response.status_code == 200:
    tokens = response.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    print("Access Token:", access_token)
    print("Refresh Token:", refresh_token)
else:
    print(f"Error: {response.status_code} - {response.text}")
