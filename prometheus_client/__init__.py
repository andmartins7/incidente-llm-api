"""Implementação local mínima do cliente Prometheus para uso em ambiente offline."""

from __future__ import annotations

CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"


class _BaseMetric:
    def __init__(self, *args, **kwargs):
        pass

    def labels(self, *args, **kwargs):
        return self

    def inc(self, amount: float = 1.0):
        return self

    def observe(self, value: float):
        return self


class Counter(_BaseMetric):
    pass


class Histogram(_BaseMetric):
    pass


def generate_latest():
    return b""

