"""Smoke test script verifying Docker Compose backing services and local connectivity."""

import socket
import sys
import urllib.request
import asyncio


def check_tcp_port(host: str, port: int, timeout: float = 3.0) -> bool:
    """Check whether a TCP port is open and listening."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        sock.close()
        return True
    except Exception:
        return False


def check_http_endpoint(url: str, expected_status: int = 200, timeout: float = 3.0) -> bool:
    """Check whether an HTTP endpoint responds with expected status."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ATIP-SmokeTest/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status == expected_status
    except urllib.error.HTTPError as e:
        return e.code == expected_status
    except Exception:
        return False


async def check_postgres() -> bool:
    """Verify live PostgreSQL query."""
    try:
        import asyncpg
        conn = await asyncpg.connect("postgresql://atip:atip_dev_password@localhost:5432/atip_db")
        val = await conn.fetchval("SELECT 1")
        await conn.close()
        return val == 1
    except Exception as e:
        print(f"  [!] PostgreSQL check error: {e}")
        return False


async def check_redis() -> bool:
    """Verify live Redis ping."""
    try:
        import redis.asyncio as redis
        r = redis.from_url("redis://localhost:6379/0")
        pong = await r.ping()
        await r.aclose()
        return pong is True
    except Exception as e:
        print(f"  [!] Redis check error: {e}")
        return False


async def check_rabbitmq() -> bool:
    """Verify live RabbitMQ connection."""
    try:
        import aio_pika
        connection = await aio_pika.connect_robust("amqp://atip:atip_dev_password@localhost:5672/")
        await connection.close()
        return True
    except Exception as e:
        print(f"  [!] RabbitMQ check error: {e}")
        return False


async def main() -> int:
    print("=" * 60)
    print("ATIP Docker Compose & Infrastructure Smoke Test")
    print("=" * 60)

    results = {}

    # 1. PostgreSQL
    print("[1/4] Checking PostgreSQL (port 5432)...")
    tcp_pg = check_tcp_port("localhost", 5432)
    query_pg = await check_postgres() if tcp_pg else False
    results["PostgreSQL"] = tcp_pg and query_pg
    print(f"      TCP Port: {'PASS' if tcp_pg else 'FAIL'}, Query: {'PASS' if query_pg else 'FAIL'}")

    # 2. Redis
    print("[2/4] Checking Redis (port 6379)...")
    tcp_redis = check_tcp_port("localhost", 6379)
    ping_redis = await check_redis() if tcp_redis else False
    results["Redis"] = tcp_redis and ping_redis
    print(f"      TCP Port: {'PASS' if tcp_redis else 'FAIL'}, Ping: {'PASS' if ping_redis else 'FAIL'}")

    # 3. RabbitMQ
    print("[3/4] Checking RabbitMQ (port 5672 / 15672)...")
    tcp_rabbit = check_tcp_port("localhost", 5672)
    tcp_mgmt = check_tcp_port("localhost", 15672)
    conn_rabbit = await check_rabbitmq() if tcp_rabbit else False
    results["RabbitMQ"] = tcp_rabbit and conn_rabbit
    print(f"      AMQP Port: {'PASS' if tcp_rabbit else 'FAIL'}, Management: {'PASS' if tcp_mgmt else 'FAIL'}, Connect: {'PASS' if conn_rabbit else 'FAIL'}")

    # 4. MinIO Object Storage
    print("[4/4] Checking MinIO (port 9000 / 9001)...")
    tcp_minio = check_tcp_port("localhost", 9000)
    http_minio = check_http_endpoint("http://localhost:9000/minio/health/live", 200)
    results["MinIO"] = tcp_minio and http_minio
    print(f"      S3 Port: {'PASS' if tcp_minio else 'FAIL'}, Health Probe: {'PASS' if http_minio else 'FAIL'}")

    print("-" * 60)
    all_passed = all(results.values())
    for svc, status in results.items():
        print(f"  {svc.ljust(15)} : {'OK' if status else 'FAILED'}")
    print("=" * 60)

    if all_passed:
        print("[SUCCESS] All 4 Compose backing services are verified healthy and operational!")
        return 0
    else:
        print("[FAILURE] One or more backing services failed smoke test.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
