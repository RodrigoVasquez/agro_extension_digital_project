"""
Google Cloud authentication utilities for the WhatsApp webhook application.
"""
import google
import google.oauth2.credentials
from google.auth import compute_engine
import google.auth.transport.requests


def idtoken_from_metadata_server(url: str) -> str:
    """
    Use the Google Cloud metadata server in the Cloud Run (or AppEngine or Kubernetes etc.,)
    environment to create an identity token and add it to the HTTP request as part of an
    Authorization header.

    Args:
        url: The url or target audience to obtain the ID token for.
            Examples: http://www.example.com
            
    Returns:
        str: The ID token for the given URL/audience
        
    Raises:
        Exception: If authentication fails or metadata server is unavailable
    """
    request = google.auth.transport.requests.Request()
    
    # Set the target audience.
    # Setting "use_metadata_identity_endpoint" to "True" will make the request use the default application
    # credentials. Optionally, you can also specify a specific service account to use by mentioning
    # the service_account_email.
    credentials = compute_engine.IDTokenCredentials(
        request=request, 
        target_audience=url, 
        use_metadata_identity_endpoint=True
    )

    # Get the ID token.
    # Once you've obtained the ID token, use it to make an authenticated call
    # to the target audience.
    credentials.refresh(request)
    return credentials.token


async def get_id_token(target_url: str) -> str:
    """
    Async wrapper for getting ID token from metadata server.
    
    Args:
        target_url: The target URL/audience for the ID token
        
    Returns:
        str: The ID token
    """
    return idtoken_from_metadata_server(target_url)
