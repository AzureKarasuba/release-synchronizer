# MVP Tradeoffs

## Included now
- Live-friendly sync plumbing to Azure iterations + user stories.
- Three-screen workflow optimized for internal release coordination.
- Manual-vs-Azure mismatch visualization with action controls.
- Drag-and-drop manual plan board.

## Deferred
- Full two-way bulk writeback with conflict resolution strategy.
- Complex field-level masking policies per customer/vendor contract.
- Async queue framework and retry backoff workers (Celery/Redis).
- Real-time push updates and collaborative editing locks.

## Why this is credible
This MVP demonstrates production-style workflow behavior without overbuilding infrastructure too early.
