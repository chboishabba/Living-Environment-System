# Monitoring

This directory provides a minimal observability stack for the
Living Environment System (LES).  Metrics from the core LES
process are exported via the [`prometheus_client`](https://github.com/prometheus/client_python)
library and visualised in Grafana.

## Starting the Stack

1. Ensure the LES metrics server is running:

   ```bash
   pip install -r requirements.txt
   python les_core.py --iterations 0  # runs indefinitely
   ```

   The metrics endpoint will be available at `http://localhost:8000/metrics`.

2. Start Prometheus and Grafana:

   ```bash
   cd grafana
   docker-compose up
   ```

   * Prometheus will be available at <http://localhost:9090>.
   * Grafana will be available at <http://localhost:3000> (default login `admin` / `admin`).

3. Grafana automatically loads the dashboard defined in
   [`dashboard.json`](grafana/dashboard.json) and connects to the
   Prometheus data source.

## Alerting

Example alerting rules are provisioned in
[`provisioning/alerting/rules.yml`](grafana/provisioning/alerting/rules.yml).
These include simple warnings for high pH and critically low
dissolved oxygen.  Alerts can be customised through Grafana's
alerting interface once the stack is running.

## How LES Pushes Metrics

The core `les_core.py` process uses `prometheus_client` gauges and
counters to expose water chemistry and simulation throughput
statistics.  Prometheus scrapes these metrics and stores them for
visualisation and alerting.
