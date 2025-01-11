import boto3
import os

try:
    import claves  # Solo se usará en el entorno local
except ImportError:
    pass

# Configuración de AWS
BUCKET_NAME = "d-ex"  # Cambia esto por el nombre de tu bucket
FILE_NAME = "https://d-ex.s3.us-east-2.amazonaws.com/refresh_token.txt"  # Nombre del archivo donde guardarás el token

# Inicializa el cliente S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

def save_refresh_token_to_s3(refresh_token):
    """
    Guarda el refresh_token en un archivo en S3.
    """
    try:
        s3_client.put_object(Bucket=BUCKET_NAME, Key=FILE_NAME, Body=refresh_token)
        print(f"Refresh token saved to S3: {FILE_NAME}")
    except Exception as e:
        print(f"Error saving refresh token to S3: {e}")

def load_refresh_token_from_s3():
    """
    Carga el refresh_token desde un archivo en S3.
    """
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=FILE_NAME)
        refresh_token = response['Body'].read().decode('utf-8')
        print(f"Refresh token loaded from S3: {refresh_token}")
        return refresh_token
    except Exception as e:
        print(f"Error loading refresh token from S3: {e}")
        return None
