import asyncio
import gc
import time

DEBUG = True

nanos_per_s = 1_000_000_000
nanos_per_ms = 1_000_000 


async def info(interval=1.0): # seconds
    ctr = 0
    interval_ns = interval * nanos_per_s
    while True:
        start = time.monotonic_ns()

        await asyncio.sleep(interval)

        end = time.monotonic_ns()

        latency_ns = end - start - interval_ns
        log(f"{ctr}",
            f"latency:{latency_ns / nanos_per_ms}ms",
            f"mem_free:{gc.mem_free()}"
            )
        await asyncio.sleep(interval)
        ctr += 1


def log(*msgs):
    line = ''.join([f"[{m}]" for m in msgs])
    print(f"[*] {line}")

def dbg(*msgs):
    DEBUG and log(*msgs)
