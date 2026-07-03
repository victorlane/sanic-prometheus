import asyncio
import os
import time
from functools import lru_cache

import psutil
from prometheus_client import Counter, Gauge, Histogram


@lru_cache(maxsize=1)
def get_worker_id():
    """
    Identity of the current worker process.

    Sanic's worker manager exports SANIC_WORKER_NAME (e.g.
    'Sanic-Server-0-0') in every worker; fall back to the PID when
    running single-process or under a foreign process manager.
    """
    return os.environ.get('SANIC_WORKER_NAME') or 'pid-{}'.format(os.getpid())


def init(app, latency_buckets=None, multiprocess_mode='all',
         memcollect_enabled=True, metrics_list=None,
         per_worker_metrics=False):
    app.ctx.metrics['RQS_COUNT'] = Counter(
        'sanic_request_count',
        'Sanic Request Count',
        ['method', 'endpoint', 'http_status']
    )

    hist_kwargs = {}
    if latency_buckets is not None:
        hist_kwargs = {'buckets': latency_buckets}
    app.ctx.metrics['RQS_LATENCY'] = Histogram(
        'sanic_request_latency_sec',
        'Sanic Request Latency Histogram',
        ['method', 'endpoint', 'http_status'],
        **hist_kwargs
    )

    if per_worker_metrics:
        app.ctx.metrics['RQS_COUNT_WORKER'] = Counter(
            'sanic_worker_request_count',
            'Sanic Request Count broken down by worker process',
            ['worker', 'method', 'endpoint', 'http_status']
        )
        app.ctx.metrics['RQS_LATENCY_WORKER'] = Histogram(
            'sanic_worker_request_latency_sec',
            'Sanic Request Latency Histogram broken down by worker process',
            ['worker', 'method', 'endpoint', 'http_status'],
            **hist_kwargs
        )

    if memcollect_enabled:
        app.ctx.metrics['PROC_RSS_MEM_BYTES'] = Gauge(
            'sanic_mem_rss_bytes',
            'Resident memory used by process running Sanic',
            multiprocess_mode=multiprocess_mode
        )
        app.ctx.metrics['PROC_RSS_MEM_PERC'] = Gauge(
            'sanic_mem_rss_perc',
            'A per cent of total physical memory used by ' +
            'the process running Sanic',
            multiprocess_mode=multiprocess_mode
        )

    if metrics_list:
        for name, pm_metric in metrics_list:
            app.ctx.metrics[name] = pm_metric


async def periodic_memcollect_task(app, period_sec):
    p = psutil.Process()
    while True:
        await asyncio.sleep(period_sec)
        app.ctx.metrics['PROC_RSS_MEM_BYTES'].set(p.memory_info().rss)
        app.ctx.metrics['PROC_RSS_MEM_PERC'].set(p.memory_percent())


def before_request_handler(request):
    request.ctx.__START_TIME__ = time.time()


def after_request_handler(request, response, get_endpoint_fn):
    lat = time.time() - request.ctx.__START_TIME__
    endpoint = get_endpoint_fn(request)

    # Note, that some handlers can ignore response logic,
    # for example, websocket handler
    response_status = response.status if response else 200
    app_metrics = request.app.ctx.metrics
    app_metrics['RQS_LATENCY'].labels(
        request.method, endpoint, response_status
    ).observe(lat)
    app_metrics['RQS_COUNT'].labels(
        request.method, endpoint, response_status
    ).inc()

    if 'RQS_LATENCY_WORKER' in app_metrics:
        worker = get_worker_id()
        app_metrics['RQS_LATENCY_WORKER'].labels(
            worker, request.method, endpoint, response_status
        ).observe(lat)
        app_metrics['RQS_COUNT_WORKER'].labels(
            worker, request.method, endpoint, response_status
        ).inc()
