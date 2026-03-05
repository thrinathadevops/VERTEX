import json
from app.connectors.base import BaseConnector
from typing import Dict, Any

class AWSConnector(BaseConnector):
    """
    Connects to AWS using boto3 to fetch resource configurations.
    """
    
    def fetch_config(self, target: str, config_path_or_identifier: str) -> str:
        """
        Fetches AWS configuration. 
        target: e.g., 'ec2|us-east-1' (service and region)
        config_path_or_identifier: e.g., 'instance|i-1234567890abcdef0' or 'security_group|sg-01234'
        """
        # boto3 is imported here to avoid crashing if it's not installed in non-AWS environments
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError

        aws_access_key_id = self.credentials.get("aws_access_key_id")
        aws_secret_access_key = self.credentials.get("aws_secret_access_key")
        
        try:
            service, region = target.split("|")
            resource_type, resource_id = config_path_or_identifier.split("|")
        except ValueError:
            raise ValueError("Invalid format. Target must be 'service|region' and path must be 'resource_type|resource_id'")

        try:
            client = boto3.client(
                service,
                region_name=region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )

            # Highly simplified extraction logic for MVP
            if service == "ec2" and resource_type == "instance":
                response = client.describe_instances(InstanceIds=[resource_id])
                # Return the deep nested JSON properties as a formatted string
                return json.dumps(response['Reservations'][0]['Instances'][0], default=str, indent=2)
            elif service == "ec2" and resource_type == "security_group":
                response = client.describe_security_groups(GroupIds=[resource_id])
                return json.dumps(response['SecurityGroups'][0], default=str, indent=2)
            else:
                raise NotImplementedError(f"Extraction for {service}/{resource_type} is not yet implemented.")
                
        except (BotoCoreError, ClientError) as e:
            raise Exception(f"AWS Error: {str(e)}")
