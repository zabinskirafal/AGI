# File Operations Security Policy

## Scope

This policy governs all file read, write, and delete operations performed by
autonomous agents within the AGI Pragma sandbox environment.

---

## Section 1 — DELETE Operations

### 1.1 Prohibited deletes

DELETE is prohibited on the following file types without explicit operator
confirmation:

- Production database files: `*.db`, `*.sqlite`, `*.sqlite3`
- Backup archives: `*.zip`, `*.tar`, `*.tar.gz`, `*.bak`
- Credential and key files: `*.pem`, `*.key`, `*.p12`, `id_rsa`, `id_ed25519`
- Configuration files: `*.yaml`, `*.yml`, `*.toml`, `*.ini`, `*.cfg`, `*.conf`
- User data exports: files matching `users_*`, `customers_*`, `accounts_*`

Severity for prohibited DELETE is CRITICAL. Detection is HARD (agents do not
always report intent before acting). Any DELETE on a prohibited pattern must
trigger a risk escalation.

### 1.2 Safe deletes

DELETE is considered low-risk only when ALL of the following hold:

- The file is a known temporary file: `*.tmp`, `*.temp`, `*.cache`, `*.lock`
- The file was created in the current session (not pre-existing)
- A backup copy exists in the same directory

### 1.3 Backup requirement

Before any DELETE on a file larger than 1 KB, a backup must exist or be
created. Agents that skip the backup step before deleting raise the occurrence
probability for subsequent operations in the same session.

---

## Section 2 — WRITE Operations

### 2.1 Sensitive path writes

WRITE to the following paths requires elevated review:

- Any path containing `config`, `env`, `secret`, `credential`, or `key`
- Any path under `~/.ssh/`, `/etc/`, `/usr/`, `/bin/`
- Files ending in `.bashrc`, `.profile`, `.zshrc`, `.bash_profile`

Writes to sensitive paths should be scored with Detection=HIGH (hard to
detect) because agents can modify these silently.

### 2.2 Overwrite risk

Overwriting an existing file is a moderately irreversible operation. Once
overwritten, the previous content is unrecoverable unless a versioned backup
exists. Agents must not overwrite files that have not been read first in the
same session.

### 2.3 Large writes

Writes exceeding 100 KB to a single file increase the probability of partial
writes and filesystem corruption. These should be flagged as side-effect
warnings. Severity escalates if the target path is a configuration or data
file.

---

## Section 3 — READ Operations

### 3.1 Sensitive content reads

READ of the following file types must be logged for audit purposes:

- Credential files: `*.pem`, `*.key`, `.env`, `secrets.yaml`
- User PII: files matching `users_*`, `customers_*`, `*_personal_data*`
- System configuration: `/etc/passwd`, `/etc/hosts`, `/etc/sudoers`

Although READ does not modify the filesystem, reading sensitive content
increases the downstream risk of exfiltration. Occurrence for subsequent
WRITE or network operations should be raised after a sensitive READ.

### 3.2 Non-existent file reads

READ of a file that does not exist is a no-op and carries zero risk. The
agent should be informed that the file is absent rather than being penalised.

---

## Section 4 — Session-Level Rules

### 4.1 Operation sequencing

The following sequences are flagged as high-risk regardless of individual
action RPN:

1. READ sensitive file → WRITE to external path (exfiltration pattern)
2. WRITE config file → DELETE original (config replacement pattern)
3. Multiple DELETEs in sequence without intervening WRITEs (bulk erasure pattern)

### 4.2 Audit requirement

All file operations on files larger than 10 KB or matching sensitive path
patterns must be recorded in a durable audit log. Agents operating in
environments without audit log persistence should be scored with
Detection=VERY_HIGH (extremely hard to detect after the fact).

---

## Section 5 — Enforcement Levels

| Risk level | Action | Enforcement |
|------------|--------|-------------|
| LOW        | Read temp file, write new file | Approve with logging |
| MEDIUM     | Overwrite existing file | Approve with warning |
| HIGH       | Delete non-backup file | Block, require confirmation |
| CRITICAL   | Delete production/credential file | Block, escalate to human |
