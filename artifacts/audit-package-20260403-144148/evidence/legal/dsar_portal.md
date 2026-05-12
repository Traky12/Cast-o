# DSAR Portal Guide

Endpoint:
- POST /api/v1/dsar/request

Supported request types:
- access
- rectify
- delete
- port

Supported data categories:
- sensors
- blockchain
- logs

Processing notes:
- delete requests are marked as processing.
- all other requests are marked as queued.

Auditability:
- Each request returns request_id and received_at timestamp.
