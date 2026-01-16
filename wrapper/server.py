import http.server
import socketserver
import webbrowser
import os
import sys

# Define the port to serve on
PORT = 8000

# Directory containing this script (and index.html)
web_dir = os.path.join(os.path.dirname(__file__))
os.chdir(web_dir)

Handler = http.server.SimpleHTTPRequestHandler

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server.")
        
        # Automatically open the browser
        webbrowser.open(f"http://localhost:{PORT}")
        
        httpd.serve_forever()
except OSError as e:
    print(f"Error: Could not start server on port {PORT}. {e}")
    print("Maybe another process is already using this port?")
except KeyboardInterrupt:
    print("\nServer stopped.")
