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
            # Parse the URL fragment (tokens come after #)
            parsed_url = urlparse(self.path)
            
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
        // Extract tokens from URL fragment
        const fragment = window.location.hash.substring(1);
        const params = new URLSearchParams(fragment);
        
        const contentDiv = document.getElementById('content');
        
        if (fragment) {{
            let html = '<h2 class="success">✓ Tokens Received</h2>';
            
            const accessToken = params.get('access_token');
            const idToken = params.get('id_token');
            const tokenType = params.get('token_type');
            const expiresIn = params.get('expires_in');
            const scope = params.get('scope');
            const state = params.get('state');
            
            if (accessToken) {{
                html += '<h3>Access Token:</h3>';
                html += `<div class="token">${{accessToken}}</div>`;
            }}
            
            if (idToken) {{
                html += '<h3>ID Token:</h3>';
                html += `<div class="token">${{idToken}}</div>`;
            }}
            
            if (tokenType) {{
                html += `<p><strong>Token Type:</strong> ${{tokenType}}</p>`;
            }}
            
            if (expiresIn) {{
                html += `<p><strong>Expires In:</strong> ${{expiresIn}} seconds</p>`;
            }}
            
            if (scope) {{
                html += `<p><strong>Scope:</strong> ${{scope}}</p>`;
            }}
            
            if (state) {{
                html += `<p><strong>State:</strong> ${{state}}</p>`;
            }}
            
            html += '<h3>Usage:</h3>';
            html += '<p>Use the access token in API requests:</p>';
            html += `<div class="token">curl -H "Authorization: Bearer ${{accessToken}}" https://sysml-v2-api.digitalthread.link/your-endpoint</div>`;
            
        }} else {{
            html = '<h2 class="error">✗ No tokens found</h2>';
            html += '<p>The callback did not contain any tokens in the URL fragment.</p>';
        }}
        
        contentDiv.innerHTML = html;
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

def main():
    parser = argparse.ArgumentParser(description='OAuth2 Implicit Grant Callback Server')
    parser.add_argument('--stack', required=True, help='CloudFormation stack name')
    args = parser.parse_args()
    
    # Get configuration from CloudFormation stack
    outputs = get_stack_outputs(args.stack)
    
    client_id = outputs.get('CognitoAPIClientId')
    auth_endpoint = outputs.get('CognitoAuthorizationEndpoint')
    
    if not client_id or not auth_endpoint:
        print("Error: Could not find CognitoAPIClientId or CognitoAuthorizationEndpoint in stack outputs")
        sys.exit(1)
    
    # Generate authorization URL
    auth_url = (
        f"{auth_endpoint}?"
        f"response_type=token&"
        f"client_id={client_id}&"
        f"redirect_uri=http://localhost:{CALLBACK_PORT}/callback&"
        f"scope=openid+email+profile"
    )
    
    print("OAuth2 Implicit Grant Flow")
    print("=" * 50)
    print(f"Stack: {args.stack}")
    print(f"Client ID: {client_id}")
    print(f"Auth Endpoint: {auth_endpoint}")
    print()
    print(f"1. Starting callback server on http://localhost:{CALLBACK_PORT}")
    print(f"2. Visit this URL in your browser to authenticate:")
    print()
    print(auth_url)
    print()
    print("3. After authentication, you'll be redirected back here with tokens")
    print("4. Press Ctrl+C to stop the server")
    print()
    
    # Start server
    with socketserver.TCPServer(("", CALLBACK_PORT), CallbackHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    main()