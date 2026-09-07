"""
Risk Radar computation engine — pure Python standard library, no dependencies.

One implementation, three consumers: the nightly CI pipeline, the MCP servers,
and (via the JSON they emit) the dashboard. Keeping it dependency-free is a
deliberate choice: a nightly job that cannot break on dependency resolution is
worth more than convenient array syntax, and it guarantees the number an agent
gets from a tool call is produced by the same code that produced the number on
the page.

Every function here computes on real observations. Where a computation cannot
be supported by the data it is given, it returns None with a stated reason
rather than a plausible-looking number.
"""
from . import stats, var, garch, evt, copula, hedge, cfar  # noqa: F401

__all__ = ["stats", "var", "garch", "evt", "copula", "hedge", "cfar"]
__version__ = "1.0.0"
