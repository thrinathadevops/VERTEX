import json
from app.connectors.base import BaseConnector
from typing import Dict, Any

class GCPConnector(BaseConnector):
    """
    Connects to Google Cloud Platform to fetch resource configurations.
    """
    
    def fetch_config(self, target: str, config_path_or_identifier: str) -> str:
        """
        Fetches GCP resource configuration via Discovery Services.
        target: e.g., 'project_id|zone'
        config_path_or_identifier: e.g., 'compute|instances|instance_name'
        """
        import googleapiclient.discovery
        from google.oauth2 import service_account
        from googleapiclient.errors import HttpError

        service_account_info = self.credentials.get("service_account_info")
        
        try:
            project_id, zone = target.split("|")
            api_service, resource_type, resource_name = config_path_or_identifier.split("|")
        except ValueError:
            raise ValueError("Invalid format. Target must be 'project_id|zone' and path must be 'api_service|resource_type|resource_name'")

        try:
            # Reconstruct credentials from dictionary passed in payload
            if isinstance(service_account_info, str):
                service_account_info = json.loads(service_account_info)
                
            credentials = service_account.Credentials.from_service_account_info(service_account_info)

            # Build the discovery service
            service = googleapiclient.discovery.build(api_service, 'v1', credentials=credentials)
            
            # Simple dispatcher. e.g. for Compute Engine instances
            if api_service == "compute" and resource_type == "instances":
                request = service.instances().get(project=project_id, zone=zone, instance=resource_name)
                response = request.execute()
                return json.dumps(response, default=str, indent=2)
            else:
                raise NotImplementedError(f"Extraction for GCP {api_service}/{resource_type} is not yet implemented.")

        except HttpError as e:
            raise Exception(f"GCP API Error: {str(e)}")
