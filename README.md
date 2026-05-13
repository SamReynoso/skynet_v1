# Skynet V1

### Stock backtesting and trading system

Last actively worked on: April 30, 2024.

Skynet V1 was an experimental backtesting framework focused on reducing iteration time during strategy development. The core feature was hot-reloading trading strategy code across multiple running worker processes without restarting the full system.

That meant strategy logic could be modified mid-run while preserving:

loaded historical market data,
in-memory state,
existing process infrastructure, and
initialized objects/resources.

Before hot reload support:

Full restart time per iteration: ~90 seconds

After hot reload support:

Iteration time: ~9 seconds

The system dramatically improved development speed by eliminating repeated database reads, object reconstruction, and process startup overhead during backtesting sessions.


## Get started

Just don't. You'll need your own alpaca.market api key and secret. So I would't even bother really.
