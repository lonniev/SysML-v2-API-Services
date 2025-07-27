#!/usr/bin/env python3
"""
Simple HTTP server to handle OAuth2 implicit grant callbacks.
Displays tokens and provides the authorization URL to visit.
"""

import http.server
import socketserver
import urllib.parse
import webbrowser
import boto3
import argparse
import sys
from urllib.parse import urlparse, parse_qs

CALLBACK_PORT = 3000

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/callback'):
            # Log the callback for debugging
            print(f"\nCallback received: {self.path}")
            
            # Note: URL fragments (#) are not sent to server, only available in browser
            # The JavaScript in the HTML will handle fragment parsing
            parsed_url = urlparse(self.path)
            
            # Parse query parameters if any (though tokens will be in fragment)
            query_params = parse_qs(parsed_url.query) if parsed_url.query else {}
            
            # Create HTML response
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>OAuth2 Callback</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .token {{ background: #f0f0f0; padding: 10px; margin: 10px 0; word-break: break-all; }}
        .error {{ color: red; }}
        .success {{ color: green; }}
    </style>
</head>
<body>
    <h1>OAuth2 Implicit Grant Callback</h1>
    <div id="content">
        <p>Processing callback...</p>
    </div>
    
    <script>
        try {{
            console.log('Full URL:', window.location.href);
            console.log('Hash:', window.location.hash);
            
            // Extract tokens from URL fragment
            const fragment = window.location.hash.substring(1);
            console.log('Fragment:', fragment);
            
            const contentDiv = document.getElementById('content');
            
            let infoHtml = '';
            
            if (fragment) {{
                const params = new URLSearchParams(fragment);
                console.log('Parsed params:', Array.from(params.entries()));
                
                infoHtml = '<h2 class="success">Tokens Received</h2>';
                
                const accessToken = params.get('access_token');
                const idToken = params.get('id_token');
                const tokenType = params.get('token_type');
                const expiresIn = params.get('expires_in');
                const scope = params.get('scope');
                const state = params.get('state');
                
                console.log('Access Token:', accessToken ? 'Found' : 'Not found');
                console.log('Token Type:', tokenType);
                console.log('Expires In:', expiresIn);
                
                if (accessToken) {{
                    infoHtml += '<h3>Access Token:</h3>';
                    infoHtml += `<div class="token">${{accessToken}}</div>`;
                }}
                
                if (idToken) {{
                    infoHtml += '<h3>ID Token:</h3>';
                    infoHtml += `<div class="token">${{idToken}}</div>`;
                }}
                
                if (tokenType) {{
                    infoHtml += `<p><strong>Token Type:</strong> ${{tokenType}}</p>`;
                }}
                
                if (expiresIn) {{
                    infoHtml += `<p><strong>Expires In:</strong> ${{expiresIn}} seconds</p>`;
                }}
                
                if (scope) {{
                    infoHtml += `<p><strong>Scope:</strong> ${{scope}}</p>`;
                }}
                
                if (state) {{
                    infoHtml += `<p><strong>State:</strong> ${{state}}</p>`;
                }}
                
                infoHtml += '<h3>Usage:</h3>';
                infoHtml += '<p>Use the access token in API requests:</p>';
                infoHtml += `<div class="token">curl -H "Authorization: Bearer ${{accessToken}}" https://sysml-v2-api.digitalthread.link/projects</div>`;
                
            }} else {{
                console.log('No fragment found in URL');
                infoHtml = '<h2 class="error">✗ No tokens found</h2><p>The callback did not contain any tokens in the URL fragment.</p><p>Full URL: ' + window.location.href + '</p>';
            }}
            
            contentDiv.innerHTML = infoHtml;
            
        }} catch (error) {{
            console.error('JavaScript error:', error);
            document.getElementById('content').innerHTML = '<h2 class="error">JavaScript Error</h2><p>' + error.message + '</p>';
        }}
    </script>
</body>
</html>
            """
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_content.encode())
        else:
            self.send_response(404)
            self.end_headers()

def get_stack_outputs(stack_name):
    """Get CloudFormation stack outputs"""
    cf = boto3.client('cloudformation')
    try:
        response = cf.describe_stacks(StackName=stack_name)
        outputs = response['Stacks'][0].get('Outputs', [])
        return {output['OutputKey']: output['OutputValue'] for output in outputs}
    except Exception as e:
        print(f"Error getting stack outputs: {e}")
        sys.exit(1)

def get_client_secret(user_pool_id, client_id):
    """Get Cognito client secret"""
    cognito = boto3.client('cognito-idp')
    try:
        response = cognito.describe_user_pool_client(
            UserPoolId=user_pool_id,
            ClientId=client_id
        )
        return response['UserPoolClient'].get('ClientSecret')
    except Exception as e:
        print(f"Error getting client secret: {e}")
        return None

def get_cognito_domain(stack_name):
    """Get Cognito domain from CloudFormation resources"""
    cf = boto3.client('cloudformation')
    try:
        response = cf.list_stack_resources(StackName=stack_name)
        for resource in response['StackResourceSummaries']:
            if resource['ResourceType'] == 'AWS::Cognito::UserPoolDomain':
                domain_name = resource['PhysicalResourceId']
                region = boto3.Session().region_name or 'us-east-1'
                return f"https://{domain_name}.auth.{region}.amazoncognito.com"
        return None
    except Exception as e:
        print(f"Error getting Cognito domain: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='OAuth2 Implicit Grant Callback Server')
    parser.add_argument('--stack', required=True, help='CloudFormation stack name')
    args = parser.parse_args()
    
    # Get configuration from CloudFormation stack
    outputs = get_stack_outputs(args.stack)
    
    client_id = outputs.get('CognitoAPIClientId')
    auth_endpoint = outputs.get('CognitoAuthorizationEndpoint')
    user_pool_id = outputs.get('CognitoUserPoolId')
    
    if not client_id or not auth_endpoint or not user_pool_id:
        print("Error: Could not find required outputs in stack")
        sys.exit(1)
    
    # Get client secret (for reference, not used in implicit flow)
    client_secret = get_client_secret(user_pool_id, client_id)
    
    # Get Cognito hosted UI domain
    cognito_hosted_domain = get_cognito_domain(args.stack)
    redirect_uri = urllib.parse.quote(f"http://localhost:{CALLBACK_PORT}/callback")
    
    # Direct Cognito hosted UI URL
    direct_auth_url = None
    if cognito_hosted_domain:
        direct_auth_url = (
            f"{cognito_hosted_domain}/oauth2/authorize?"
            f"response_type=token&"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope=profile"
        )
    
    # Proxy URL (original)
    proxy_auth_url = (
        f"{auth_endpoint}?"
        f"response_type=token&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=profile"
    )
    
    print("OAuth2 Implicit Grant Flow")
    print("=" * 50)
    print(f"Stack: {args.stack}")
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {client_secret[:10]}..." if client_secret else "Client Secret: None")
    print(f"Auth Endpoint: {auth_endpoint}")
    print(f"Note: Client secret not used in implicit flow")
    print()
    print(f"1. Starting callback server on http://localhost:{CALLBACK_PORT}")
    if direct_auth_url:
        print(f"2. Try direct Cognito hosted UI:")
        print()
        print(direct_auth_url)
        print()
        print(f"3. If needed, try proxy URL:")
        print()
        print(proxy_auth_url)
    else:
        print(f"2. Try proxy URL:")
        print()
        print(proxy_auth_url)
        print()
        print("Note: Could not find Cognito hosted domain")
    print()
    print("4. After authentication, you'll be redirected back here with tokens")
    print("5. Press Ctrl+C to stop the server")
    print()
    
    # Start server
    with socketserver.TCPServer(("", CALLBACK_PORT), CallbackHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    main()