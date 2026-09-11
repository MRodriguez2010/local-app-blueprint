import concurrent.futures
import importlib.util
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

spec = importlib.util.spec_from_file_location("counter", Path(__file__).resolve().parents[1] / "examples/counter/app.py")
counter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(counter)


class CounterTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "counter.sqlite3"
        self.store = counter.CounterStore(self.path)

    def start_server(self):
        server = counter.make_server(self.store, port=0)
        worker = threading.Thread(target=server.serve_forever)
        worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(worker.join)
        self.addCleanup(server.shutdown)
        return f"http://127.0.0.1:{server.server_port}"

    def test_reopen_preserves_data(self):
        self.assertEqual(self.store.increment(), 1)
        self.assertEqual(counter.CounterStore(self.path).read(), 1)

    def test_concurrent_increments_are_not_lost(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.store.increment(), range(40)))
        self.assertEqual(sorted(results), list(range(1, 41)))
        self.assertEqual(self.store.read(), 40)

    def test_http_health_and_increment(self):
        base = self.start_server()
        request = urllib.request.Request(base + "/api/increment", data=b"{}", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request) as response:
            self.assertEqual(json.load(response), {"value": 1})
        with urllib.request.urlopen(base + "/health") as response:
            self.assertEqual(json.load(response), {"value": 1})

    def test_invalid_requests_cannot_change_counter(self):
        base = self.start_server()
        cases = [
            ("GET", {}, None, 404),
            ("POST", {"Content-Type": "text/plain"}, b"{}", 415),
            ("POST", {"Content-Type": "application/json", "Origin": "https://example.invalid"}, b"{}", 403),
            ("POST", {"Content-Type": "application/json", "Host": "example.invalid"}, b"{}", 403),
            ("POST", {"Content-Type": "application/json"}, b'{"value":99}', 400),
            ("POST", {"Content-Type": "application/json"}, b"{" * 2048, 400),
        ]
        for method, headers, body, expected in cases:
            with self.subTest(method=method, headers=headers):
                request = urllib.request.Request(base + "/api/increment", data=body, method=method, headers=headers)
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(request)
                self.assertEqual(caught.exception.code, expected)
        self.assertEqual(self.store.read(), 0)


if __name__ == "__main__":
    unittest.main()
