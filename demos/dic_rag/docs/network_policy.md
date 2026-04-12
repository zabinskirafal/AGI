# Network Operations Security Policy

## Scope

This policy governs all outbound network requests, API calls, webhook
deliveries, and data transmissions performed by autonomous agents within
AGI Pragma governed environments.

---

## Section 1 — Outbound HTTP / API Requests

### 1.1 Permitted destinations

Agents may make outbound requests only to destinations explicitly listed
in the approved endpoint registry.  Requests to arbitrary user-supplied
URLs are prohibited without operator confirmation.

Severity for unapproved outbound requests is CRITICAL.  Detection is HARD
because HTTP calls execute silently and leave no local trace unless an audit
log captures them.

### 1.2 Authentication credentials in requests

HTTP requests must never include raw credentials, API keys, or bearer tokens
in URL query parameters.  Credentials must be passed via Authorization headers
only.  Any request that embeds credentials in the URL path or query string
must be blocked.

This pattern is irreversible — credentials exposed in a URL are logged by
proxies, CDNs, and browser history.  Once exposed, rotation is required.

### 1.3 Retry and rate limits

Agents must not send more than 10 requests per second to any single endpoint.
Unbounded retry loops are prohibited.  An agent that retries on every error
without back-off is flagged as a high-occurrence risk pattern.

---

## Section 2 — Data Exfiltration Risk

### 2.1 Sensitive data in request bodies

POST bodies containing PII fields (`email`, `ssn`, `phone`, `dob`,
`credit_card`, `password`) require elevated review before transmission.
Severity is HIGH; Detection is HARD because the payload is not visible
in standard access logs.

Agents that read a sensitive file and then immediately issue an outbound
POST request must be flagged as a potential exfiltration pattern.

### 2.2 Bulk data transmission

Transmitting more than 1 MB in a single request body, or more than 10 MB
in a session, requires explicit operator confirmation.  Bulk transmissions
that are not part of an approved backup or sync workflow are escalate to human.

### 2.3 Webhook deliveries

Webhooks deliver data to third-party systems.  Any webhook payload that
contains internal system state, configuration data, or user records must
be reviewed before delivery.  Unapproved webhook targets are prohibited.

---

## Section 3 — DNS and Host Resolution

### 3.1 Internal network access

Agents must not resolve or connect to RFC-1918 addresses (10.x, 172.16-31.x,
192.168.x) unless the target is explicitly approved.  Connecting to internal
services from an external-facing agent context is a sandbox escape pattern.

### 3.2 DNS rebinding

Agents must not follow DNS redirects from an approved external hostname to an
internal IP address.  DNS rebinding attacks allow bypassing the approved
endpoint registry by resolving an approved name to an internal target.

---

## Section 4 — TLS and Encryption

### 4.1 TLS required

All outbound requests must use TLS 1.2 or higher.  Plain HTTP requests are
prohibited except to localhost for local service discovery.

### 4.2 Certificate verification

TLS certificate verification must not be disabled.  Any request made with
`verify=False` or equivalent must be blocked regardless of the target.
Bypassing certificate verification is irreversible from a security standpoint
— it silently removes a critical layer of authentication.

---

## Section 5 — Enforcement Levels

| Risk level | Operation | Enforcement |
|------------|-----------|-------------|
| LOW        | GET to approved endpoint, no auth, no PII | Approve with logging |
| MEDIUM     | POST to approved endpoint, non-sensitive body | Approve with warning |
| HIGH       | POST with PII, bulk transmission > 1 MB | Block unless confirmed |
| CRITICAL   | Unapproved destination, credentials in URL, verify=False | Block, escalate to human |
