# Database Operations Security Policy

## Scope

This policy governs all database read, write, and schema-modification operations
performed by autonomous agents within AGI Pragma governed environments.

---

## Section 1 — DELETE / DROP Operations

### 1.1 DROP TABLE — always critical

DROP TABLE is an irreversible operation. Once executed, all rows and the schema
definition are permanently lost unless a full database backup exists and has been
verified.

- Severity: CRITICAL (10/10)
- Detection: HARD — DROP is a single DDL statement that executes instantly
- Occurrence: HIGH in agentic contexts where agents may conflate cleanup tasks
  with schema management

DROP TABLE without a prior verified backup must always trigger ESCALATE
regardless of the table name.

### 1.2 DELETE FROM — severity depends on scope

| Scope | Severity | Notes |
|-------|----------|-------|
| `DELETE FROM table WHERE id = ?` (single row) | LOW | Reversible via audit log if present |
| `DELETE FROM table WHERE <broad condition>` | HIGH | Large scope, hard to scope-check |
| `DELETE FROM table` (no WHERE clause) | CRITICAL | Equivalent to full table wipe |

Agents must not issue `DELETE FROM` without a WHERE clause. This pattern must be
detected and blocked regardless of the table name.

### 1.3 Backup requirement before bulk delete

Any DELETE affecting more than 100 rows requires a prior SELECT COUNT(*) to
confirm scope, and a backup snapshot or transaction savepoint before execution.
Agents that skip this step raise the occurrence score for the session.

---

## Section 2 — WRITE / INSERT / UPDATE Operations

### 2.1 Production table writes

Writes to tables matching the following name patterns are flagged as sensitive:

- `users`, `accounts`, `customers`, `employees`, `payments`, `transactions`
- Any table with suffix `_prod` or prefix `prod_`
- Tables containing PII columns: `email`, `phone`, `ssn`, `dob`, `password_hash`

Detection for production table writes is HIGH — agents can insert or update
silently without visible side effects in the short term.

### 2.2 Schema modifications (ALTER TABLE)

ALTER TABLE operations that add, remove, or rename columns are MEDIUM severity
unless they affect a NOT NULL constraint or a primary key, in which case they
are HIGH. Agents must not run ALTER TABLE on production tables without an
explicit migration plan in the task context.

### 2.3 Mass UPDATE without WHERE

UPDATE without a WHERE clause affects all rows and must be treated as
equivalent to a bulk DELETE followed by re-insert. This pattern is CRITICAL
and must be blocked.

---

## Section 3 — READ / SELECT Operations

### 3.1 PII queries

SELECT queries that return PII columns (`email`, `ssn`, `dob`, `phone`,
`password_hash`, `credit_card`) must be logged. Although SELECT does not
modify data, returning PII increases downstream exfiltration risk.

If a SELECT returns PII and is followed by a WRITE or network operation in
the same session, the occurrence score for the subsequent operation must be
raised to account for the exfiltration pattern.

### 3.2 Aggregate-only queries

SELECT queries that return only aggregates (COUNT, SUM, AVG, MIN, MAX) with
no PII columns are low-risk. These may be approved at RPN < 500 with standard
logging.

### 3.3 Cross-table JOINs on sensitive tables

JOIN queries that combine a sensitive table (users, payments) with any other
table increase the information exposure surface. These should be scored with
Severity +1 above the base level for the dominant table.

---

## Section 4 — Transaction and Rollback Rules

### 4.1 Autocommit mode

Agents operating in autocommit mode have no rollback capability. All
WRITE/DELETE/ALTER operations in autocommit mode must be scored with
Reversibility = NONE (R=10 in FMEA) regardless of operation type.

### 4.2 Savepoints

For multi-step operations (read → transform → write), agents must set a
savepoint before each write step. Absence of savepoints raises Detection
difficulty because partial failures leave the database in an unknown state.

### 4.3 Long-running transactions

Transactions open for more than 60 seconds acquire locks that block other
agents. Long-running transactions must be flagged as a side effect with
Severity = MEDIUM.

---

## Section 5 — Enforcement Levels

| Risk level | Operation | Enforcement |
|------------|-----------|-------------|
| LOW        | SELECT aggregate only | Approve with logging |
| MEDIUM     | SELECT with PII, single-row DELETE | Approve with warning |
| HIGH       | Bulk DELETE with WHERE, ALTER TABLE | Block unless confirmed |
| CRITICAL   | DROP TABLE, DELETE without WHERE, UPDATE without WHERE | Block, escalate to human |
