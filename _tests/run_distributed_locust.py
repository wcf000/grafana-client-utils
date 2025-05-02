"""
Distributed Locust Test Runner
=============================

# Start master (controls test)
python run_distributed_locust.py --master --users 1000

# Start workers (run load)
python run_distributed_locust.py --worker --host <master-ip>

Run as:
1. Master: python run_distributed_locust.py --master
2. Worker: python run_distributed_locust.py --worker
"""
import argparse
import subprocess
import os
from app.core.config import settings

parser = argparse.ArgumentParser()
parser.add_argument("--master", action="store_true", help="Run as master node")
parser.add_argument("--worker", action="store_true", help="Run as worker node")
parser.add_argument("--host", default="localhost", help="Master host")
parser.add_argument("--port", default="5557", help="Master port")
parser.add_argument("--users", type=int, default=100, help="Total users")
parser.add_argument("--spawn-rate", type=float, default=10, help="Users spawned per second")
args = parser.parse_args()

if args.master:
    cmd = f"locust -f locust_performance.py --master --expect-workers 2 --users {args.users} --spawn-rate {args.spawn_rate}"
elif args.worker:
    cmd = f"locust -f locust_performance.py --worker --master-host {args.host} --master-port {args.port}"
else:
    raise ValueError("Must specify --master or --worker")

subprocess.run(cmd, shell=True, check=True)
