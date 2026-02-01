"""
Docstring per vector_store.opensearch_client

import os
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3


class OpenSearchClient:
    def __init__(self):
        host = os.getenv("OPENSEARCH_HOST", "localhost")
        port = os.getenv("OPENSEARCH_PORT", "9200")
        region = os.getenv("AWS_REGION", "")

        session = boto3.Session()
        credentials = session.get_credentials()
        if not credentials:
            raise ValueError("AWS credentials not found")
        credentials = credentials.get_frozen_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            "es",
            session_token=credentials.token,
        )

        self.client = OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )

    def ping(self):
        return self.client.ping()

    def close(self):
        self.client.transport.close()
"""
