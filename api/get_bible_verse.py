# GET /api/get_bible_verse?book=로마서&start=8:11&end=8:11
import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.bible_verse import get_bible_verse_text


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            q = parse_qs(parsed.query)
            book = (q.get("book") or [""])[0].strip()
            start = (q.get("start") or [""])[0].strip()
            end = (q.get("end") or [start])[0].strip()
            if not book or not start:
                self._json(400, {"detail": "book, start 필요"})
                return
            text = get_bible_verse_text(book, start, end)
            self._json(200, {"text": text, "book": book, "start": start, "end": end})
        except Exception as e:
            self._json(500, {"detail": str(e)})

    def _json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()
