from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json

ROOT = Path(__file__).resolve().parent.parent
WEBSITE = ROOT / "website"
RESULTS = ROOT / "results"


class Handler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        # Serve HTML/CSS/JS from the website folder
        super().__init__(*args, directory=str(WEBSITE), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)

        # -----------------------------
        # API: /api/result
        # -----------------------------
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

            if mode == "rician":
                filename = f"macro_with_Rician{angle}deg_100km.json"
            else:
                filename = f"macro_no_Rician{angle}deg_100km.json"

            path = RESULTS / filename

            if not path.exists():
                self.send_json(404, {
                    "error": f"No saved result for {angle} degrees in {mode} mode.",
                    "expected_file": str(path.relative_to(ROOT))
                })
                return

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

        # -----------------------------
        # Website homepage
        # -----------------------------
        if parsed.path == "/":
            self.path = "/index.html"

        # Serve CSS / JS / HTML
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

    if not RESULTS.exists():
        print("WARNING: results/ folder was not found.")

    print()
    print("==============================================")
    print(" LEO Multi-Beam Website")
    print("==============================================")
    print()
    print("Website folder :", WEBSITE)
    print("Results folder :", RESULTS)
    print()
    print("Open this in your browser:")
    print("http://127.0.0.1:8000")
    print()
    print("Press Ctrl+C to stop.")
    print()

    ThreadingHTTPServer(
        ("127.0.0.1", 8000),
        Handler
    ).serve_forever()