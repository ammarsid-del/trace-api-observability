"""Repeatable HTTP load test using only the Python standard library.

Example:
  python scripts/benchmark.py --url http://localhost:8000/demo/42 --requests 500 --concurrency 10

This measures client-observed latency (network + app + database), not the
server-side request duration displayed in Trace.
"""
import argparse
import concurrent.futures
import json
import math
import statistics
import time
import urllib.error
import urllib.request

def percentile(values, p):
    ordered = sorted(values)
    if not ordered:
        return 0.0
    return ordered[max(0, math.ceil(len(ordered) * p / 100) - 1)]

def request_once(url, timeout):
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except (urllib.error.URLError, TimeoutError, OSError):
        status = 0
    return (time.perf_counter() - started) * 1000, status

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000/demo/42")
    parser.add_argument("--requests", type=int, default=500)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args()
    if args.requests < 1 or args.concurrency < 1:
        parser.error("--requests and --concurrency must be positive")
    if not (args.url.startswith("http://localhost:") or args.url.startswith("http://127.0.0.1:")):
        parser.error("Benchmark is restricted to localhost to prevent accidental load on external services")
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = list(pool.map(lambda _: request_once(args.url, args.timeout), range(args.requests)))
    elapsed = time.perf_counter() - started
    latencies = [ms for ms, _ in results]
    successes = sum(200 <= status < 400 for _, status in results)
    report = {
        "url": args.url, "requests": args.requests, "concurrency": args.concurrency,
        "successes": successes, "failures": args.requests - successes,
        "duration_seconds": round(elapsed, 3),
        "requests_per_second": round(args.requests / elapsed, 2),
        "mean_latency_ms": round(statistics.mean(latencies), 2),
        "p50_latency_ms": round(percentile(latencies, 50), 2),
        "p95_latency_ms": round(percentile(latencies, 95), 2),
        "p99_latency_ms": round(percentile(latencies, 99), 2),
    }
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
