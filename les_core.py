"""Core LES process with Prometheus metrics export.

This script simulates LES metrics such as water chemistry and
simulation throughput and exposes them via the Prometheus
client on an HTTP endpoint.

Run this file directly to start the metrics server and update
metrics in a simple loop.  Use the ``--iterations`` argument
for a finite number of iterations; by default it runs
indefinitely.
"""
from __future__ import annotations

import argparse
import random
import time

from prometheus_client import Counter, Gauge, start_http_server

# Gauges for current state measurements
water_ph = Gauge("water_ph", "Current water pH level")
dissolved_oxygen = Gauge(
    "dissolved_oxygen_mg_per_l",
    "Dissolved oxygen concentration in mg/L",
)

# Throughput and counts
simulation_steps_total = Counter(
    "simulation_steps_total", "Total number of simulation steps processed"
)
simulation_throughput = Gauge(
    "simulation_throughput_steps_per_second", "Simulation steps per second"
)


def run_metrics_server(port: int) -> None:
    """Start the Prometheus metrics HTTP server."""
    start_http_server(port)


def simulate(iterations: int | None = None, delay: float = 1.0) -> None:
    """Update metrics in a loop.

    Parameters
    ----------
    iterations:
        Number of simulation iterations to perform. ``None`` runs indefinitely.
    delay:
        Seconds to wait between iterations.
    """
    start_time = time.time()
    steps = 0
    while iterations is None or steps < iterations:
        # Simulate readings
        water_ph.set(7.0 + random.uniform(-0.3, 0.3))
        dissolved_oxygen.set(8.0 + random.uniform(-1.0, 1.0))

        # Update counters and throughput
        simulation_steps_total.inc()
        steps += 1
        elapsed = time.time() - start_time
        if elapsed > 0:
            simulation_throughput.set(steps / elapsed)

        time.sleep(delay)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--port", type=int, default=8000, help="Port for Prometheus metrics HTTP server"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="Number of simulation iterations; default runs indefinitely",
    )
    parser.add_argument(
        "--delay", type=float, default=1.0, help="Delay between iterations in seconds"
    )
    args = parser.parse_args()

    run_metrics_server(args.port)
    simulate(iterations=args.iterations, delay=args.delay)


if __name__ == "__main__":
    main()
