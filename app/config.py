import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    HEADLESS = os.getenv('HEADLESS', 'true').lower() in ('true', '1', 't', 'y', 'yes')
    SELECTORS_PATH = os.getenv("SELECTORS_PATH")
    POSTGRES_CONN = os.getenv("POSTGRES_CONN")

    # Variable to detect if we are on AWS
    IS_AWS = os.getenv("AWS_EXECUTION_ENV") is not None

    if IS_AWS:
        # Import boto3 solely if we are into AWS environment
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError

        def get_secret(session, db_user, db_host, db_port):
            """Retrieves secret from AWS IAM or secrets manager"""
            # Get IAM token if IAM_AUTH environment variable is set
            iam_auth = os.getenv('IAM_AUTH', 'disabled')
            if iam_auth != 'disabled':
                try:
                    token = session.client('rds').generate_db_auth_token(
                    DBHostname=db_host,
                    Port=db_port,
                    DBUsername=db_user)
                    return token
                except (BotoCoreError, ClientError) as e:
                    print(f"Error generating IAM token: {e}")

            # Then get password from AWS Secrets manager
            secret_name = os.getenv('DB_USER_SECRET')
            if secret_name:
                try:
                    secrets_client = session.client(service_name="secretsmanager")
                    secret_value_response = secrets_client.get_secret_value(SecretId=secret_name)
                    if secret_value_response:
                        if secret_value_response['SecretString']:
                            return secret_value_response['SecretString']
                except (BotoCoreError, ClientError) as e:
                    print(f"Error getting secret from Secrets Manager : {e}")

            # Else, test if a password is directly provided
            if os.getenv('DB_PASSWORD'):
                return os.getenv('DB_PASSWORD')
            # If nothing is found, return None
            return None

        # Define variables
        db_user = os.getenv('DB_USER')
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME')

        region_name = os.getenv('AWS_REGION', 'eu-west-3')
        session = boto3.session.Session(region_name=region_name)

        # Retrieve secret
        secret = get_secret(session, db_user, db_host, db_port)

        # Build the database connection chain
        ssl_mode = os.getenv('SSL_MODE', 'prefer')
        ssl_root_cert = os.getenv('SSL_ROOT_CERT')
        POSTGRES_CONN = f"postgresql://{db_user}:{secret}@{db_host}:{db_port}/{db_name}?sslmode={ssl_mode}"
        if ssl_root_cert:
            POSTGRES_CONN += f"&sslrootcert={ssl_root_cert}"
