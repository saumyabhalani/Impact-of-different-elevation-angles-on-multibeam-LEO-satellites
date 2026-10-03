from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json
import os


ROOT = Path(__file__).resolve().parent.parent
WEBSITE = ROOT / "website"
RESULTS = ROOT / "results"


class Handler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            directory=str(WEBSITE),
            **kwargs
        )

    def do_GET(self):

        parsed = urlparse(self.path)

        # API endpoint
        if parsed.path == "/api/result":

            q = parse_qs(parsed.query)

            mode = q.get("mode", ["rician"])[0]

            try:
                angle = int(q.get("angle", ["55"])[0])
            except ValueError:
                self.send_json(400, {
                    "error": "Invalid elevation angle."
                })
                return

            # Select the correct JSON file
            if mode == "rician":
                filename = f"macro_with_Rician{angle}deg_100km.json"
            elif mode == "macro":
                filename = f"macro_no_Rician{angle}deg_100km.json"
            else:
                self.send_json(400, {
                    "error": "Invalid simulation mode."
                })
                return

            path = RESULTS / filename

            # Check whether JSON exists
            if not path.exists():
                self.send_json(404, {
                    "error": f"No saved result for {angle} degrees in {mode} mode.",
                    "expected_file": str(path.relative_to(ROOT))
                })
                return

            # Read JSON
            try:
                data = json.loads(
                    path.read_text(encoding="utf-8")
                )

                self.send_json(200, data)

            except Exception as exc:
                self.send_json(500, {
                    "error": str(exc)
                })

            return

        # Homepage
        if parsed.path == "/":
            self.path = "/index.html"

        # Serve website files
        super().do_GET()

    def send_json(self, code, data):

        raw = json.dumps(data).encode("utf-8")

        self.send_response(code)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(raw))
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.end_headers()

        self.wfile.write(raw)


if __name__ == "__main__":

    if not WEBSITE.exists():
        print("ERROR: website/ folder was not found.")
        print("Expected:", WEBSITE)

    if not RESULTS.exists():
        print("WARNING: results/ folder was not found.")
        print("Expected:", RESULTS)

    # Render provides the PORT environment variable.
    # If running locally, use port 8000.
    port = int(os.environ.get("PORT", 8000))

    print()
    print("==============================================")
    print(" LEO Multi-Beam Satellite Website")
    print("==============================================")
    print()
    print("Project root :", ROOT)
    print("Website      :", WEBSITE)
    print("Results      :", RESULTS)
    print("Port         :", port)
    print()
    print("Server started successfully.")
    print()

    server = ThreadingHTTPServer(
        ("0.0.0.0", port),
        Handler
    )

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print()
        print("Server stopped.")

    finally:
        server.server_close()