"""
Simple HTTP server for the Aurora frontend
"""
import http.server
import socketserver
import os

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

os.chdir(os.path.dirname(__file__))

print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🌟 Aurora Concierge Intelligence Dashboard                ║
║                                                              ║
║   Frontend server started successfully!                     ║
║                                                              ║
║   🌐 Open in browser: http://localhost:{PORT}               ║
║                                                              ║
║   ⚡ Make sure backend is running on port 8000              ║
║                                                              ║
║   Press Ctrl+C to stop the server                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
