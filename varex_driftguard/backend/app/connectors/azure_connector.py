import json
from app.connectors.base import BaseConnector
from typing import Dict, Any

class AzureConnector(BaseConnector):
    """
    Connects to Azure Resource Manager to fetch configurations.
    """
    
    def fetch_config(self, target: str, config_path_or_identifier: str) -> str:
        """
        Fetches Azure resource configuration.
        target: e.g., 'subscription_id|resource_group_name'
        config_path_or_identifier: e.g., 'Microsoft.Compute/virtualMachines|vm_name'
        """
        from azure.identity import ClientSecretCredential
        from azure.mgmt.resource import ResourceManagementClient
        from azure.core.exceptions import HttpResponseError

        tenant_id = self.credentials.get("tenant_id")
        client_id = self.credentials.get("client_id")
        client_secret = self.credentials.get("client_secret")
        
        try:
            subscription_id, resource_group = target.split("|")
            provider_type, resource_name = config_path_or_identifier.split("|")
        except ValueError:
            raise ValueError("Invalid format. Target must be 'subscription_id|resource_group' and path must be 'Provider.Namespace/resourceType|resource_name'")

        try:
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )

            # Extract the raw ARM representation of the resource
            client = ResourceManagementClient(credential, subscription_id)
            
            # Using generic resource fetch 
            # API Version must be provided or obtained dynamically, locking to 2021-04-01 for MVP
            resource = client.resources.get(
                resource_group_name=resource_group,
                resource_provider_namespace=provider_type.split("/")[0],
                parent_resource_path="",
                resource_type=provider_type.split("/")[1],
                resource_name=resource_name,
                api_version="2021-04-01" 
            )
            
            # resource is a GenericResource object, serialize its properties
            return json.dumps(resource.as_dict(), default=str, indent=2)

        except HttpResponseError as e:
            raise Exception(f"Azure API Error: {str(e)}")
