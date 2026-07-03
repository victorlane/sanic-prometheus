import re
import subprocess
import sys
import unittest
from functools import partial
from time import sleep
from urllib import request
from urllib.error import URLError

from sanic import Sanic
from sanic.response import json
from sanic.worker.loader import AppLoader

from sanic_prometheus import SanicPrometheusError, monitor

TEST_PORT = 54424


def create_app(name):
    app = Sanic(name)

    @app.route('/test')
    async def test(request):
        return json({'a': 'b'})

    monitor(app, per_worker_metrics=True).expose_endpoint()
    return app


def launch_server():
    loader = AppLoader(factory=partial(create_app, 'test_mp'))
    app = loader.load()
    app.prepare(port=TEST_PORT, workers=2)
    Sanic.serve(primary=app, app_loader=loader)


def wait_for_server(url, timeout_sec=30):
    attempts = int(timeout_sec / 0.5)
    for _ in range(attempts):
        try:
            request.urlopen(url).read()
            return
        except URLError:
            sleep(0.5)
    raise RuntimeError(
        'server did not start within {} seconds'.format(timeout_sec))


class TestMultiprocessing(unittest.TestCase):
    def setUp(self):
        self._procs = []

    def tearDown(self):
        for p in self._procs:
            p.terminate()
            p.wait(timeout=10)

    def test_start_server_should_not_work_with_mp(self):
        app = Sanic('test_mp_start_server')
        self.assertRaises(SanicPrometheusError, monitor(app).start_server)

    def test_metrics_are_aggregated_between_workers(self):
        # Sanic's worker manager requires a fresh interpreter with an
        # unset multiprocessing start method, so launch via subprocess
        p = subprocess.Popen([
            sys.executable, '-c',
            'from tests.it_multiprocess import launch_server; '
            'launch_server()',
        ])
        self._procs.append(p)
        wait_for_server("http://localhost:{}/test".format(TEST_PORT))

        for _ in range(100):
            r = request.urlopen("http://localhost:{}/test".format(TEST_PORT))
            _ = r.read()

        r = request.urlopen("http://localhost:{}/metrics".format(TEST_PORT))
        nreqs = None
        worker_counts = {}
        for line in r.readlines():
            line = line.decode('ascii')
            m = re.match(
                r"^sanic_request_count_total\{.+\}\s+(\d+)(\.\d+)?\s*", line)
            if m:
                nreqs = int(m.group(1))
                continue
            m = re.match(
                r'^sanic_worker_request_count_total\{.*'
                r'worker="([^"]+)".*\}\s+(\d+)(\.\d+)?\s*', line)
            if m:
                worker_counts[m.group(1)] = int(m.group(2))
        self.assertIsNotNone(nreqs)
        # the warm-up requests from wait_for_server are counted too,
        # so we only check the lower bound
        self.assertGreaterEqual(nreqs, 100)
        # per-worker series must exist and add up to the aggregate
        self.assertGreaterEqual(len(worker_counts), 1)
        self.assertEqual(sum(worker_counts.values()), nreqs)
