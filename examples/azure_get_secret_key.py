import os

from dotenv import load_dotenv

from services.azure_manager import AzureKeyVaultConfig

load_dotenv()

azurekeyvaultconfig = AzureKeyVaultConfig(
    kv_name=os.getenv("AZURE_VAULT_NAME", ""),
    kv_url=os.getenv("AZURE_VAULT_URL", ""),
)

secret_object_name = os.getenv("SECRET_OBJECT_NAME", "")
print(
    f"Your secret is '{azurekeyvaultconfig.get_secret(secret_object_name=secret_object_name)}'."
)
