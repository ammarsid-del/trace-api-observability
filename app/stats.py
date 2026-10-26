from math import ceil

def percentile(values, percent):
    if not 0 <= percent <= 100:
        raise ValueError('percent must be between 0 and 100')
    values = sorted(values)
    if not values:
        return 0.0
    return round(float(values[max(0, ceil(percent * len(values) / 100) - 1)]), 2)

def latency_percentiles(values):
    values = sorted(values)
    return {f'p{p}_latency_ms': percentile(values, p) for p in (50, 95, 99)}
