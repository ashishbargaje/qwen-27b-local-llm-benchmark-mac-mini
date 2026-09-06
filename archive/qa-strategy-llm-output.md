# QA Strategy for an Enterprise Expense Management Platform

This strategy is written from a **failure-mode-first, risk-based perspective**. The highest-value QA work is not “happy-path coverage,” but **preventing incorrect money movement, duplicate ERP transactions, unauthorized approvals, security leaks, and inconsistent state across async systems**.

---

## 1. Ten Highest-Risk Areas

| # | High-risk area | Why it is risky | QA focus |
|---|---|---|---|
| 1 | **Kafka duplicate / out-of-order event processing** | Kafka can deliver duplicates and out-of-order messages. A duplicate `ExpenseApproved` event can cause duplicate ERP export. Out-of-order events can apply stale business decisions. | Idempotent consumers, event sequencing, DB state checks, replay tests. |
| 2 | **ERP export idempotency and retry after timeout** | A request may reach ERP, be accepted, but the response may not arrive before the 30-second API timeout. Blind retries can create a second external transaction. | Stable idempotency keys, ERP reconciliation, retry safety. |
| 3 | **Approval state machine and concurrent approval/rejection** | Multiple managers, UI latency, async events, and race conditions can create invalid transitions such as approving after rejection or double approval. | State transition enforcement, DB locking, optimistic concurrency, audit trails. |
| 4 | **No atomic transaction across DB, Kafka, and ERP** | The system cannot atomically span Kafka and ERP. A DB update, Kafka event, and ERP call can become inconsistent if one fails. | Outbox pattern, saga/reconciliation, durable event logging, split-brain tests. |
| 5 | **OCR extraction accuracy** | OCR is approximately 95% accurate. Amount, date, vendor, or tax errors can flow into ERP. Wrong data can corrupt finance records. | OCR confidence thresholds, manual review workflow, data validation. |
| 6 | **Duplicate expense detection** | If duplicate detection is too weak, two expenses for the same receipt can be exported. If too strong, valid expenses may be blocked. | Unique receipt hash, vendor/date/amount rules, false positive/negative tests. |
| 7 | **Authorization and ownership controls** | Employees must not approve their own expenses. Managers and finance users have different permissions. Weak RBAC can allow fraud or accidental export. | Role-based API tests, IDOR tests, JWT validation, permission matrix. |
| 8 | **Receipt file privacy** | Receipt images/PDFs must never be publicly accessible. Public S3 URLs or leaked presigned links can expose financial documents. | S3 ACL tests, presigned URL expiry, role-limited access, audit logs. |
| 9 | **Exchange rate and transaction-date correctness** | Expenses must use the exchange rate applicable on the transaction date. Using today’s rate or a stale rate can change amount/tax. | Rate lookup tests, date boundary tests, rate outage fallback tests. |
| 10 | **Performance, concurrency, and auditability** | 10,000 concurrent users, API timeout, Kafka backlog, ERP outage, and state mismatches can hide defects. Audit trails are needed to detect duplicate exports. | Load testing, SLO monitoring, audit reconciliation, observability. |

---

## 2. End-to-End QA Strategy

### 2.1 Testing philosophy

The QA strategy should prioritize:

1. **State consistency**: Every expense must have one authoritative status.
2. **Money integrity**: ERP exports must be unique, auditable, and recoverable.
3. **Authorization correctness**: Only allowed users can act.
4. **Recovery correctness**: Failures in Kafka, ERP, S3, OCR, or DB must not corrupt state.
5. **Observability**: Every important transition must be traceable.

The main risk is not simply “expense was created,” but **“expense was exported incorrectly, exported twice, exported without approval, exported with wrong data, or exported from an unauthorized file.”**

---

### 2.2 Functional testing

Functional testing should cover the full business workflow and failure states.

Key scenarios:

- Employee creates expense.
- Employee uploads receipt.
- OCR extracts amount, date, vendor, tax.
- Expense is submitted.
- Manager receives notification.
- Manager approves.
- Manager rejects.
- Expense above $5,000 requires two-level approval.
- Employee cannot approve own expense.
- Expense cannot be approved after rejection.
- Duplicate expenses are detected.
- Approved expense is exported to ERP.
- ERP returns external transaction ID.
- Expense status becomes `EXPORTED`.

Test data matrix should include:

- Amount below $5,000.
- Amount exactly $5,000.
- Amount above $5,000.
- Different currencies.
- Different transaction dates.
- Different vendors.
- Duplicate receipts.
- Invalid receipts.
- OCR low-confidence results.
- Missing receipt.
- Expired or corrupted receipt file.

Functional tests should assert not only final status, but also:

- Audit log contains every transition.
- Correct actor performed the transition.
- Correct approval level was required.
- ERP was not called for rejected expenses.
- ERP was not called before all required approvals.

---

### 2.3 API testing

API tests should cover REST contract, state transitions, authorization, and idempotency.

Key API tests:

1. **Expense creation**
   - Valid payload accepted.
   - Invalid payload rejected.
   - Duplicate creation rejected or flagged.

2. **Receipt upload**
   - Valid PDF/image accepted.
   - Invalid file rejected.
   - File stored non-public.
   - Presigned URL only accessible to allowed roles.

3. **Submit**
   - Expense can be submitted only after required validation.
   - Duplicate submit attempt rejected.

4. **Approve/reject**
   - Only authorized managers can approve/reject.
   - Employee cannot approve own expense.
   - Rejection after approval is blocked.
   - Two-level approval required above $5,000.

5. **Export trigger**
   - Export request only valid for approved expenses.
   - Export request idempotent.
   - Export response includes ERP external transaction ID.

6. **Status retrieval**
   - UI and API reflect same authoritative status.
   - Stale cache does not show incorrect status.

API tests should use:

- Contract tests.
- Authorization matrix.
- State-transition tests.
- Idempotency tests.
- Error-code tests.
- Timeout tests.

---

### 2.4 UI testing

UI testing should focus on role-based flows and state visibility.

Test roles:

- Employee.
- Manager.
- Finance user.
- Finance exporter/admin.
- Auditor.

UI scenarios:

- Employee sees expense in `SUBMITTED`.
- Manager sees notification and can approve/reject.
- Employee cannot approve own expense in UI.
- UI prevents approving after rejection.
- UI shows `APPROVED_PENDING_EXPORT`, `IN_EXPORT`, `EXPORTED`, or `EXPORT_FAILED` states.
- Finance UI shows ERP external transaction ID.
- UI handles OCR low-confidence or manual review state.
- UI handles ERP outage without blocking the user indefinitely.
- UI does not expose direct public S3 links.

UI tests should include:

- Web UI.
- Mobile app, if in scope.
- Accessibility basics.
- State synchronization with backend.
- Error and loading states.
- Permission-denied states.

---

### 2.5 Integration testing

Integration testing should cover all external and internal dependencies:

- PostgreSQL.
- Kafka.
- Elasticsearch.
- Redis.
- S3-compatible object storage.
- ERP REST API.
- Email.
- Microsoft Teams.
- OCR service.
- Exchange rate source.

Key integration tests:

1. **Kafka integration**
   - Event schema validation.
   - Duplicate message handling.
   - Out-of-order message handling.
   - Consumer offset tracking.
   - Dead-letter queue handling.
   - Replay behavior.

2. **S3 integration**
   - Files stored private.
   - Presigned URLs expire.
   - Role-limited access.
   - No public bucket access.
   - Download audit logging.

3. **ERP integration**
   - ERP accepts export.
   - ERP returns external transaction ID.
   - ERP outage handling.
   - Retry safety.
   - Duplicate prevention.
   - Partial response handling.

4. **Search integration**
   - Elasticsearch index reflects expense status.
   - Stale index does not mislead users.
   - Search does not expose unauthorized records.

5. **Cache integration**
   - Redis cache invalidation after state change.
   - Cache does not show stale approval/rejection status.

6. **Notification integration**
   - Manager receives notification.
   - Notifications do not leak receipt files.
   - Notification links are role-restricted.

---

### 2.6 Event-driven / Kafka testing

Kafka testing is one of the highest-risk areas. The system must assume Kafka is unreliable: duplicates, out-of-order events, consumer crashes, partition failures, and replays.

QA should test:

- Producer schema validation.
- Consumer idempotency.
- Event ordering.
- Consumer retries.
- Dead-letter queue.
- Offset recovery.
- Partition failure recovery.
- Replay safety.

Recommended pattern:

> Use **at-least-once delivery** with **idempotent consumers**, not blind exactly-once expectations.  
> The consumer should read the current authoritative DB state before acting, and use a stable idempotency key for ERP export.

Compare approaches:

| Approach | Pros | Cons | Recommendation |
|---|---|---|---|
| Exactly-once Kafka consumption | Simpler event semantics | Complex, often insufficient in production, still needs idempotency at business level | Not sufficient alone |
| At-least-once + idempotent consumer | Handles duplicates, replay, retries | Requires careful DB state checks | Recommended |
| Event-only state machine | Simple | Prone to race and stale events | Not recommended |
| DB-authoritative + outbox/reconciliation | More robust | More complex | Recommended |

---

### 2.7 Database testing

Database tests should focus on state consistency, concurrency, constraints, and auditability.

Key tests:

1. **State transition constraints**
   - Invalid transitions rejected.
   - Approve after reject blocked.
   - Export after rejection blocked.
   - Export before full approval blocked.

2. **Concurrency**
   - Two managers approve simultaneously.
   - One approval wins.
   - The other attempt is rejected or audited as denied.
   - No lost update.

3. **Duplicate expense constraints**
   - Unique receipt hash.
   - Vendor/date/amount duplicate rule.
   - Duplicate submit blocked.

4. **Audit logging**
   - Every transition logged.
   - Actor, timestamp, event ID, ERP ID, status before/after.
   - Audit log can detect duplicate ERP exports.

5. **Transaction safety**
   - DB commit does not depend on Kafka success.
   - DB update occurs before ERP export or is idempotent if repeated.
   - Failed DB update does not leave inconsistent status.

Recommended DB pattern:

- Expense row has a version or status.
- Updates use optimistic concurrency or row locking.
- Export state is stored with ERP external transaction ID.
- Audit log records all transitions.
- If ERP export is async, use an outbox table or durable export queue.

---

### 2.8 Security testing

Security tests should cover authentication, authorization, data privacy, and financial fraud.

Key tests:

1. **OAuth2 / JWT**
   - Valid tokens accepted.
   - Expired tokens rejected.
   - Invalid issuer rejected.
   - Token replay detection if supported.

2. **Role-based access control**
   - Employee cannot approve own expense.
   - Manager can approve.
   - Finance can export.
   - Auditor can read audit trail.
   - Unauthorized user cannot export.

3. **Insecure direct object references**
   - User A cannot approve expense B by changing URL.
   - User A cannot export expense B without permission.
   - Expense IDs are not guessable or are protected by authorization.

4. **Receipt file access**
   - S3 object is private.
   - Anonymous GET returns 403.
   - Presigned URL expires.
   - Presigned URL role-limited.
   - File download logged.

5. **Sensitive data exposure**
   - OCR output not exposed to unauthorized users.
   - ERP response not exposed to unauthorized users.
   - Audit logs protected.

6. **Fraud scenarios**
   - Employee creates high-value expense and attempts self-approval.
   - Manager attempts to approve after rejection.
   - Finance attempts to export rejected expense.
   - Duplicate high-value expense attempt.

---

### 2.9 Performance testing

Given 10,000 concurrent users and a 30-second API timeout, performance testing is critical.

Test objectives:

- p95 API response time under 30 seconds.
- Kafka consumer lag within acceptable SLO.
- ERP export throughput under normal load.
- DB lock contention under concurrent approvals.
- Redis cache hit/miss behavior.
- S3 upload/download throughput.
- OCR processing latency.
- System behavior during ERP outage.

Performance scenarios:

1. 10,000 concurrent users performing expense creation and approval.
2. 1,000 approved expenses exported to ERP concurrently.
3. ERP outage for several hours while expense queue grows.
4. Kafka partition failure under load.
5. OCR batch processing under load.
6. Approval storm: many managers approving/rejecting at same time.

Pass criteria:

- API p95 < 30 seconds.
- No unbounded queue growth during ERP outage.
- No deadlock during concurrent approvals.
- Kafka consumer lag below defined SLO.
- Export throughput meets business requirement.

---

### 2.10 Resilience / recovery testing

Resilience testing should simulate real failure modes.

Key failure scenarios:

1. **ERP outage**
   - ERP unavailable for 6 hours.
   - Export queue grows.
   - No duplicate exports after recovery.
   - No lost exports.
   - Reconciliation after recovery.

2. **Kafka consumer crash**
   - Consumer crashes after processing but before DB update.
   - Consumer restarts.
   - Replay does not duplicate ERP export.

3. **Kafka partition failure**
   - Partition leader fails.
   - Consumers resume.
   - No duplicate or lost messages.
   - Offset recovery correct.

4. **Network failure after ERP accepted**
   - ERP accepts request but response is lost.
   - Client retries.
   - Idempotency prevents duplicate external transaction.

5. **OCR failure**
   - OCR timeout or invalid result.
   - Expense does not auto-export.
   - Manual review path works.

6. **S3 failure**
   - Upload fails.
   - Expense remains in correct state.
   - No public file leak.

7. **Redis failure**
   - Cache miss does not corrupt status.
   - Backend remains source of truth.

---

### 2.11 Auditability

Auditability is not a “nice-to-have.” It is required by the business rules.

Every state transition must be auditable. This means:

- Expense ID.
- Previous status.
- New status.
- Actor ID.
- Timestamp.
- Event ID.
- Approval level.
- ERP request ID.
- ERP external transaction ID.
- Idempotency key.
- Failure reason, if any.

QA should verify:

1. Every approval, rejection, export, retry, and failure is logged.
2. Audit log can prove whether an ERP export was requested once or multiple times.
3. Audit log can detect duplicate external transaction IDs.
4. Audit log can detect export after rejection.
5. Audit log can detect self-approval attempt.
6. Audit log supports reconciliation between application status and ERP external transaction ID.

Recommended audit check:

```text
For each expense:
  - count EXPORTED transitions
  - count ERP external transaction IDs
  - verify exactly one EXPORTED transition
  - verify ERP external transaction ID matches stored ID
```

If the ERP has two external transaction IDs for the same expense, the audit log should flag it immediately.

---

## 3. Investigation of the Duplicate ERP Export Defect

The reported defect:

> An expense was exported twice to the ERP even though the application showed only one `EXPORTED` record.

This strongly suggests a **non-idempotent export path**, a **race condition**, a **retry after ambiguous timeout**, or a **stale event processing** problem.

Below are five technically plausible root causes.

---

### Root Cause 1: Duplicate Kafka message consumed without stable idempotency

#### How it could happen

Kafka can deliver duplicate messages. If the finance consumer receives two `ExpenseApproved` events for the same expense and does not check the current DB state or use a stable idempotency key, it may call ERP twice.

Example:

1. Kafka delivers `ExpenseApproved(expenseId=E1)` twice.
2. Consumer processes first event.
3. Consumer calls ERP.
4. Consumer updates DB to `EXPORTED`.
5. Consumer processes second event.
6. If consumer does not re-read DB state or uses a non-stable key, it may call ERP again.

#### How to reproduce

1. Create approved expense `E1`.
2. Publish two identical `ExpenseApproved` events for `E1`.
3. Run finance consumer.
4. Instrument ERP mock or test ERP.
5. Check whether two ERP external transaction IDs were created.

#### Logs/metrics/traces to inspect

- Kafka topic and partition.
- Kafka offset.
- Event ID.
- Expense ID.
- Consumer instance ID.
- ERP request ID.
- Idempotency key.
- ERP response.
- DB status before and after processing.
- Audit log entries.
- Metrics:
  - `export_attempts`
  - `export_successes`
  - `duplicate_external_transaction_ids`
  - `kafka_consumer_lag`

#### Regression test

Duplicate-event test:

- Publish same approved event twice.
- Assert exactly one ERP external transaction ID.
- Assert exactly one `EXPORTED` transition in audit log.
- Assert DB stores the same ERP external transaction ID.

---

### Root Cause 2: Timeout after ERP accepted, then retry with non-stable key

#### How it could happen

The finance service sends an ERP export request. ERP accepts the request and creates an external transaction, but the response does not arrive before the 30-second API timeout.

If the finance service treats the request as failed and retries:

- Retry uses a new request ID or new idempotency key.
- ERP sees it as a new request.
- ERP creates a second external transaction.

The application may still show only one `EXPORTED` record if the DB was eventually updated once, while ERP has two external transactions.

#### How to reproduce

1. Create approved expense `E1`.
2. Send ERP export request with idempotency key `K1`.
3. Simulate ERP accepting the request but delaying response beyond 30 seconds.
4. Let client timeout.
5. Retry request.
6. If retry uses a new key `K2`, ERP creates second transaction.
7. If retry uses stable key `K1`, ERP should return same external ID.

#### Logs/metrics/traces to inspect

- Client request ID.
- Idempotency key for first request.
- Idempotency key for retry.
- ERP request correlation ID.
- ERP external transaction ID.
- Client timeout log.
- Retry count.
- DB status at retry time.
- Metrics:
  - `erp_timeout_count`
  - `erp_retry_count`
  - `duplicate_external_transaction_ids`
  - `erp_request_latency`

#### Regression test

Timeout/retry idempotency test:

- First request times out after ERP accepted.
- Retry uses same stable idempotency key.
- Assert ERP returns same external transaction ID.
- Assert only one external transaction exists.
- Assert DB contains one `EXPORTED` transition.

---

### Root Cause 3: Consumer acknowledges Kafka before durable DB update, then replay causes duplicate export

#### How it could happen

The consumer may process an event in this unsafe order:

1. Read expense.
2. Call ERP.
3. Acknowledge Kafka offset.
4. Update DB status to `EXPORTED`.
5. DB update fails or is delayed.

If the consumer crashes after step 3 but before step 4, Kafka may replay the event. The consumer then calls ERP again because DB still says `APPROVED` or an intermediate state.

#### How to reproduce

1. Publish approved event.
2. Consumer sends ERP export.
3. Simulate ERP success.
4. Prevent DB update from committing.
5. Kill consumer after Kafka ack but before DB commit.
6. Restart consumer.
7. Replay event.
8. Check ERP external transaction count.

#### Logs/metrics/traces to inspect

- Kafka offset committed.
- Consumer crash timestamp.
- ERP request timestamp.
- ERP response timestamp.
- DB update failure timestamp.
- Replay event timestamp.
- DB status before replay.
- Audit log entries.
- Metrics:
  - `consumer_crash_count`
  - `export_attempts`
  - `db_commit_latency`
  - `duplicate_external_transaction_ids`

#### Regression test

Crash/replay test:

- Consumer crashes after ERP success but before DB update.
- Consumer restarts.
- Event replayed.
- Assert no second ERP external transaction.
- Assert DB eventually reaches one `EXPORTED` state.

Recommended fix test:

- Consumer should not ack until DB status is durable, or it must be fully idempotent if replay happens.

---

### Root Cause 4: Out-of-order or stale Kafka event processed without checking current DB state

#### How it could happen

Kafka messages can arrive out of order, especially across partitions or during rebalancing. The consumer may trust the event payload instead of the DB.

Example:

1. Expense is approved.
2. Expense is rejected later.
3. An old `ExpenseApproved` event is replayed or processed late.
4. Consumer sees `ExpenseApproved` and exports it.
5. DB later shows rejected, but ERP already has a transaction.

Or:

1. Expense is exported.
2. A stale approval event is replayed.
3. Consumer exports again.

#### How to reproduce

1. Create expense.
2. Publish events in non-business order:
   - `ExpenseApproved`
   - `ExpenseRejected`
   - `ExpenseApproved`
3. Run consumer.
4. Check whether export occurs after rejection or after export.
5. Check audit log.

#### Logs/metrics/traces to inspect

- Event sequence.
- Kafka offset.
- Partition.
- Producer timestamp.
- Consumer processing timestamp.
- DB status at processing time.
- Audit log.
- Metrics:
  - `invalid_transition_count`
  - `export_after_rejection_count`
  - `duplicate_export_count`

#### Regression test

Out-of-order event test:

- Publish stale or reordered events.
- Consumer must read current DB state.
- Invalid transitions rejected.
- No export after rejection.
- No second export if already exported.

---

### Root Cause 5: Idempotency key is wrong, per-message, colliding, or missing

#### How it could happen

The ERP may accept an idempotency key, but the finance service may generate the key incorrectly.

Bad key choices:

- Use Kafka message ID as idempotency key.
- Use event ID instead of expense ID.
- Generate a new key on every retry.
- Omit the key.
- Use a key that does not represent the business object.

Example:

1. Duplicate delivery creates two Kafka messages with different message IDs.
2. Consumer uses message ID as idempotency key.
3. ERP sees two different keys.
4. ERP creates two external transactions.

#### How to reproduce

1. Publish same logical event twice with different Kafka message IDs.
2. Consumer generates key from message ID.
3. ERP receives two different keys.
4. ERP creates two external transactions.
5. Application may still show one `EXPORTED` if DB update succeeded once.

#### Logs/metrics/traces to inspect

- Idempotency key in each ERP request.
- Expense ID.
- Event ID.
- Message ID.
- ERP external transaction ID.
- ERP request count by key.
- Audit log.
- Metrics:
  - `idempotency_key_mismatch_count`
  - `duplicate_external_transaction_ids`

#### Regression test

Idempotency key stability test:

- Same expense exported multiple times.
- Key must be stable per business object, not per message.
- Assert ERP returns same external ID for same key.
- Assert only one external transaction.

Recommended key design:

```text
EXPORT:<expenseId>:<approvedVersion>
```

If the expense cannot be modified after approval, use:

```text
EXPORT:<expenseId>
```

Do not use Kafka message ID as the business idempotency key.

---

## 4. Kafka Test Scenarios

These tests should be automated in an integration environment with real Kafka or a Kafka-compatible broker.

| # | Scenario | Test design | Expected result | Defect detected |
|---|---|---|---|---|
| K1 | Duplicate delivery | Publish the same `ExpenseApproved` event twice with the same logical expense ID. | Consumer creates only one ERP external transaction and one `EXPORTED` transition. | Non-idempotent consumer or bad idempotency key. |
| K2 | Out-of-order events | Publish events in non-business order, e.g. approved, rejected, approved, or approved, exported, approved. | Consumer reads current DB state and ignores stale/invalid transitions. No export after rejection or after export. | Consumer trusts event payload over DB state. |
| K3 | Consumer retry | Simulate ERP failure during export. Consumer retries with stable idempotency key and bounded backoff. | No duplicate ERP transaction after successful retry. Failed events eventually move to dead-letter or reconcile. | Blind retry or missing idempotency. |
| K4 | Consumer crash | Kill consumer after processing but before or after DB update. Restart consumer and replay event. | No lost event and no duplicate ERP export. DB eventually reaches correct state. | Ack before durable state, replay duplicate, split-brain. |
| K5 | Poison message | Send malformed event: missing expense ID, invalid amount, invalid currency, missing receipt, negative value. | Consumer validates and rejects or routes to dead-letter. Consumer does not crash or export bad data. | Missing validation, crash-prone consumer. |
| K6 | Partition failure | Simulate partition leader failure or rebalance. Consumers resume from last committed offsets. | No duplicate or lost messages. Kafka lag recovers. ERP no duplicate export. | Offset loss, rebalance duplicate, recovery failure. |
| K7 | Replay | Replay a range of compacted or previously processed events. | Consumer recognizes already processed business state and does not re-export. ERP external transaction count remains one. | Missing idempotency, no durable state check. |

Recommended Kafka test assertions:

```text
For each expense:
  - ERP external transaction count == 1
  - EXPORTED transition count == 1
  - No EXPORTED transition after REJECTED
  - No export attempt for unapproved expense
  - Dead-letter events are observable and auditable
```

---

## 5. ERP Integration Test Scenarios

ERP integration is the second highest-risk area because the ERP is an external financial system.

| # | Scenario | Test design | Expected result | Defect detected |
|---|---|---|---|---|
| E1 | Timeout | ERP request delays beyond 30 seconds. Client times out, then retries with stable idempotency key. | If ERP accepted the first request, retry returns the same external transaction ID. Only one external transaction. | Ambiguous timeout, non-idempotent retry. |
| E2 | 500 response | ERP returns 500. Consumer retries with stable key and backoff. | Expense remains in export-pending state until success. No export until ERP confirms. After recovery, one external transaction. | Blind retry, premature `EXPORTED` status. |
| E3 | 429 response | ERP returns 429 with rate limit. Consumer backs off and respects Retry-After or equivalent behavior. | No retry storm. Queue bounded. Export eventually succeeds. | Thundering herd, unbounded retries. |
| E4 | Network failure after ERP accepted | Proxy accepts ERP request but drops the response before client receives it. Client retries. | Stable idempotency key ensures same external transaction. No duplicate ERP record. | Split-brain, retry after accepted request. |
| E5 | Duplicate request | Send two ERP requests with same idempotency key for same expense. | ERP returns same external transaction ID. Only one external transaction created. | Missing ERP idempotency or bad key. |
| E6 | Partial response | ERP returns success but missing external transaction ID, or response is truncated/malformed. | Consumer marks expense as `IN_EXPORT` or `EXPORT_PENDING`, queries ERP by idempotency key, and reconciles. No premature `EXPORTED`. | Missing confirmation, partial response handling. |
| E7 | ERP outage for 6 hours | Disable ERP for 6 hours. Approved expenses queue. | Queue grows but remains bounded. No duplicate exports after recovery. No lost exports. Reconciliation after outage. | Unbounded queue, duplicate retry, loss. |
| E8 | Retry storm | Many export attempts fail repeatedly. | Exponential backoff, jitter, circuit breaker, and concurrency limit prevent storm. Dead-letter or manual reconciliation after max retries. | Retry storm, resource exhaustion. |

Recommended ERP export flow:

1. Finance consumer reads expense from DB.
2. Validate expense is approved and not already exported.
3. Generate stable idempotency key.
4. Send ERP request.
5. On success, store ERP external transaction ID in DB.
6. On timeout or ambiguous response, query ERP by idempotency key.
7. If ERP confirms existing transaction, update DB with existing external ID.
8. If ERP does not confirm, retry with same key.
9. After max retries, move to dead-letter and alert.

---

## 6. Idempotency Test Design for ERP Export

### 6.1 Idempotency key

Requirement:

> ERP export must be idempotent.

Assumption:

> ERP honors a stable idempotency key and returns the same external transaction ID for repeated requests with that key.

Recommended idempotency key:

```text
EXPORT:<expenseId>:<approvedVersion>
```

If the expense is immutable after approval, use:

```text
EXPORT:<expenseId>
```

Avoid:

```text
EXPORT:<kafkaMessageId>
EXPORT:<requestId>
EXPORT:<eventTimestamp>
```

Those keys can differ for retries or duplicate deliveries.

### 6.2 Request generation

Create an approved expense:

```text
expenseId = "EXP-1001"
status = APPROVED
amount = 1200
currency = USD
transactionDate = 2026-01-15
vendor = "Vendor X"
tax = 180
```

Generate ERP export request:

```http
POST /erp/expenses
Idempotency-Key: EXPORT:EXP-1001:1
Content-Type: application/json

{
  "expenseId": "EXP-1001",
  "amount": 1200,
  "currency": "USD",
  "transactionDate": "2026-01-15",
  "vendor": "Vendor X",
  "tax": 180,
  "receiptId": "R-1001"
}
```

For retry, the request must use the same idempotency key.

### 6.3 Retry behavior

Retry behavior should be:

1. First request sent with key `EXPORT:EXP-1001:1`.
2. If response succeeds, store ERP external transaction ID.
3. If response times out or is ambiguous, do not assume success.
4. Query ERP by idempotency key.
5. If ERP reports existing transaction, update DB with that external transaction ID.
6. If ERP reports no transaction, retry with same key.
7. Use bounded retries with exponential backoff.
8. After max retries, mark export failed and send to dead-letter.

### 6.4 Database state

DB state should be:

Before export:

```text
status = APPROVED
erpExternalTransactionId = NULL
```

After successful ERP confirmation:

```text
status = EXPORTED
erpExternalTransactionId = "ERP-12345"
```

If export is attempted but not confirmed:

```text
status = IN_EXPORT or EXPORT_PENDING
erpExternalTransactionId = NULL
```

DB update should be safe under concurrency:

- Use row lock or optimistic version.
- Only update from `APPROVED` to `EXPORTED` if not already `EXPORTED`.
- Store audit transition.

### 6.5 Expected ERP behavior

Expected ERP behavior:

1. First request with key `EXPORT:EXP-1001:1` creates external transaction `ERP-12345`.
2. Second request with same key returns `ERP-12345`.
3. ERP does not create a second external transaction.
4. If first request was accepted but response was lost, second request with same key should return existing `ERP-12345`.
5. If key is different, ERP may create a second transaction, which should be detected as a defect.

### 6.6 Assertions

A strong idempotency test should assert:

```text
ERP external transaction count for expenseId == 1
ERP external transaction ID for request 1 == ERP external transaction ID for request 2
DB status for expenseId == EXPORTED
DB erpExternalTransactionId == ERP-12345
Audit EXPORTED transition count == 1
Audit export attempt log contains stable idempotency key
No EXPORTED transition after REJECTED
No second external transaction ID exists for the same expense
```

Concrete test steps:

1. Create and approve expense.
2. Send ERP export request with stable key.
3. Simulate timeout after ERP accepted.
4. Retry with same stable key.
5. Assert ERP mock shows one created external transaction.
6. Assert both requests return same external ID.
7. Assert DB shows one `EXPORTED` transition.
8. Assert audit log can reconcile application status with ERP external ID.

---

## 7. Race Conditions in the Approval/Export Workflow

At least five race conditions are possible.

| # | Race condition | How it can happen | QA test |
|---|---|---|---|
| R1 | Two managers approve the same expense simultaneously | Two API calls attempt `APPROVED` at the same time. Without row lock/version control, both may succeed or both may create audit confusion. | Concurrent approve test: only one approval transition succeeds; other is rejected or audited as denied. |
| R2 | Approval and rejection happen concurrently | One manager approves, another rejects at the same time. The system must enforce one final state. | Concurrent approve/reject test: final state is one of approved or rejected; no both. |
| R3 | Export consumer reads stale `APPROVED` status while manager rejects | Consumer reads DB, sees approved, starts ERP export, but rejection commits before ERP completes. | Re-check DB state immediately before ERP call and after response; do not export rejected expense. |
| R4 | Duplicate expense submissions race | Two employees submit the same receipt simultaneously. Duplicate detection may miss the race if it only checks after insert. | Concurrent duplicate submit test: second insert rejected or flagged as duplicate. |
| R5 | Kafka consumer and DB commit race | Duplicate event is processed before first DB export commit completes. Second event sees old status and exports again. | Duplicate event + delayed DB commit test: no duplicate ERP external transaction. |
| R6 | OCR post-processing changes data after export starts | OCR result arrives late and updates amount/vendor, while export is already in flight. | Export uses locked snapshot; late OCR changes require revalidation or new export version. |

Recommended mitigation:

- DB is the source of truth.
- Use row locks or optimistic concurrency.
- Re-check state before external side effect.
- Use stable idempotency keys.
- Audit every conflict.

---

## 8. Risk-Based Regression Strategy for a 2-Week Release with 3 QA Engineers

With only 3 QA engineers and a 2-week release, the strategy must be risk-based and automation-heavy. Manual full coverage is not feasible. The goal is to **block release on critical financial/security/state defects** and manage lower-risk items separately.

### 8.1 Priority definitions

#### P0 — Release blockers

P0 defects must prevent release unless accepted by product/finance with mitigation.

P0 areas:

1. Duplicate ERP export.
2. ERP idempotency failure.
3. Invalid approval state.
4. Self-approval by employee.
5. Export after rejection.
6. Receipt file public access.
7. Missing audit trail for money movement.
8. Exchange rate applied to wrong date.
9. Two-level approval failure for expenses above $5,000.
10. Unauthorized export by wrong role.

#### P1 — High priority

P1 defects are serious but may be mitigated or monitored if not blocking.

P1 areas:

1. Kafka out-of-order event handling.
2. Consumer crash/replay duplicate export.
3. ERP outage recovery.
4. OCR low-confidence handling.
5. Duplicate expense detection false positives/negatives.
6. Performance under 10,000 users.
7. Audit reconciliation.
8. Dead-letter and retry storm handling.
9. Search/cache consistency.

#### P2 — Medium priority

P2 defects should be fixed if feasible, but do not block release if P0/P1 are stable.

P2 areas:

1. Search result staleness.
2. Notification display issues.
3. UI edge cases.
4. Logging completeness for non-money events.
5. Mobile app minor defects.
6. Accessibility issues.

#### P3 — Lower priority

P3 defects are acceptable to defer if no business risk.

P3 areas:

1. Cosmetic UI issues.
2. Non-critical error messages.
3. Low-risk log verbosity.
4. Minor search sorting issues.
5. Non-blocking analytics gaps.

---

### 8.2 Allocation of 3 QA engineers

| QA engineer | Focus | Main deliverables |
|---|---|---|
| QA 1 | API, Kafka, ERP, idempotency | Duplicate export tests, timeout/retry tests, Kafka replay, ERP outage, API contract tests. |
| QA 2 | UI, functional, security, audit | Role-based approval tests, self-approval, file privacy, audit log validation, UI state consistency. |
| QA 3 | Performance, resilience, data, OCR | Load tests, ERP outage, Kafka partition failure, OCR low-confidence, exchange rate, reconciliation. |

This allocation avoids all three engineers duplicating the same tests.

---

### 8.3 Two-week execution plan

#### Days 1–2: Environment and automation baseline

- Build staging environment.
- Set up mock ERP.
- Set up Kafka test harness.
- Build test data factory.
- Add observability hooks:
  - request IDs
  - idempotency keys
  - ERP external IDs
  - audit log
  - Kafka offsets.

#### Days 3–5: P0 failure-mode tests

Run:

- Duplicate approved Kafka event.
- Timeout after ERP accepted.
- Retry with stable key.
- Export after rejection.
- Self-approval.
- Two-level approval above $5,000.
- Receipt public access.
- Exchange rate date correctness.
- Audit transition checks.

#### Days 6–8: P1 resilience and integration tests

Run:

- Kafka out-of-order.
- Consumer crash/replay.
- Poison message.
- Partition failure.
- ERP 500/429.
- ERP outage.
- Retry storm.
- OCR low-confidence.
- Duplicate expense detection.

#### Days 9–10: Performance and audit reconciliation

Run:

- 10,000 concurrent user load.
- ERP export throughput.
- Kafka lag.
- DB concurrency.
- Audit reconciliation between app and ERP.

#### Days 11–12: Nightly regression, canary, release gate

Run:

- Nightly P0/P1 suite.
- Canaries or shadow traffic.
- Final release gate.
- Defect triage.
- P2/P3 triage if time permits.

---

### 8.4 Release gate decision

Release should be blocked if any of the following are true:

1. P0 duplicate ERP export defect is not resolved.
2. ERP idempotency test fails.
3. Approval state machine allows invalid transitions.
4. Self-approval or unauthorized export is possible.
5. Receipt files are publicly accessible.
6. Audit log cannot prove one ERP export per expense.
7. Exchange rate uses wrong date.
8. Performance fails 30-second API timeout under realistic load.
9. ERP outage causes duplicate or lost exports.
10. Security findings include unauthorized access to financial data.

P1 defects may be released only with:

- Monitoring enabled.
- Runbook defined.
- Dead-letter/reconciliation process verified.
- Risk accepted by product/finance.

---

## 9. Quality Gates for CI/CD

### 9.1 On every pull request

Run fast, targeted checks.

| Test type | Purpose |
|---|---|
| Unit tests | Validate core logic and state transitions. |
| Static analysis / lint | Catch obvious defects and style issues. |
| API schema tests | Validate request/response contracts. |
| Security SAST | Scan code for obvious security issues. |
| UI smoke tests, if UI changed | Ensure basic UI flow works. |
| Build | Ensure artifact builds. |

Pass criteria:

- All unit tests pass.
- No high-severity SAST findings.
- API schema valid.
- UI smoke passes if UI touched.

---

### 9.2 On merge

Run broader integration checks.

| Test type | Purpose |
|---|---|
| Full unit tests | Catch logic regressions. |
| API contract tests | Validate REST behavior. |
| Kafka schema tests | Validate event payloads. |
| UI E2E smoke | Validate main user flows. |
| Security SAST + dependency scanning | Catch vulnerabilities. |
| Audit log tests | Ensure transitions recorded. |
| Integration with mocks | ERP mock, S3 mock, Kafka broker. |
| Duplicate expense detection tests | Catch duplicate workflow regressions. |

Pass criteria:

- P0 functional tests pass.
- Kafka event schema valid.
- Audit log test passes.
- No high-severity security findings.
- UI E2E smoke passes.

---

### 9.3 Nightly

Run the risk-based regression suite.

| Test type | Purpose |
|---|---|
| P0/P1 regression | Detect core financial/state defects. |
| Kafka duplicate/out-of-order tests | Detect event processing failures. |
| ERP failure tests | Timeout, 500, 429, outage, partial response. |
| OCR low-confidence tests | Detect bad extracted data. |
| Performance baseline | Track latency and throughput. |
| Audit reconciliation | Detect app/ERP mismatch. |
| Security spot checks | File access, RBAC, IDOR. |

Pass criteria:

- P0 100%.
- P1 no new critical failures.
- Performance within SLO.
- Audit reconciliation clean.

---

### 9.4 Before production deployment

Run full release gate.

| Test type | Purpose |
|---|---|
| Full P0 suite | Block release on critical defects. |
| Full P1 suite | Verify resilience and recovery. |
| Security penetration / authorization tests | Verify RBAC, file privacy, IDOR. |
| Performance test at realistic load | Verify 10,000 user behavior. |
| Chaos tests | ERP outage, Kafka partition failure, DB write failure. |
| Audit reconciliation | Verify one ERP export per expense. |
| Exchange rate test | Verify transaction-date rate. |
| Canary deployment | Validate zero-downtime behavior. |
| Rollback test | Verify recovery if deployment fails. |

Pass criteria:

- P0 and P1 pass.
- No high-severity security defects.
- Performance SLO met.
- Chaos recovery works.
- Audit reconciliation passes.
- Canary metrics stable.
- Rollback works.

---

## 10. Fifteen High-Value Test Cases

| ID | Scenario | Priority | Test Type | Expected Result |
|---|---|---|---|---|
| T-01 | Duplicate `ExpenseApproved` Kafka event for same expense | P0 | Event/API/Integration | Only one ERP external transaction; one `EXPORTED` transition in DB and audit log. |
| T-02 | ERP export times out after ERP accepted, then retried with same idempotency key | P0 | Integration/ERP | Retry returns same ERP external transaction ID; no second external transaction. |
| T-03 | Expense above $5,000 requires two-level approval | P0 | Functional/API | No ERP export until both required approvals exist. |
| T-04 | Manager tries to approve after rejection | P0 | State machine/API | Approval rejected; expense remains rejected; no ERP export. |
| T-05 | Employee attempts to approve own expense | P0 | Security/API/UI | Action denied; audit log records denied self-approval attempt. |
| T-06 | Duplicate expense submission using same receipt/vendor/date/amount | P0 | Functional/DB | Second submission blocked or flagged as duplicate; no duplicate export. |
| T-07 | Receipt file access attempted by unauthorized user | P0 | Security/S3 | Anonymous or unauthorized access returns 403; only role-limited presigned URL works. |
| T-08 | Exchange rate lookup uses transaction date, not current date | P0 | Data/API | Amount/tax computed using rate applicable to transaction date. |
| T-09 | Out-of-order Kafka event arrives after rejection or export | P1 | Event/DB | Consumer ignores stale event; no invalid transition or duplicate export. |
| T-10 | Consumer crashes after ERP success but before durable DB update, then replays event | P1 | Resilience/Kafka | Replay does not create second ERP external transaction; DB reaches one correct state. |
| T-11 | ERP returns 500 or 429 repeatedly | P1 | Integration/ERP | Bounded retries with backoff; no retry storm; expense remains pending until success or DLQ. |
| T-12 | OCR returns low-confidence amount/vendor/date | P1 | Functional/OCR | Expense routed to manual review; no auto-export with unvalidated data. |
| T-13 | Audit log records every state transition with actor, timestamp, event, and ERP ID | P0 | Audit/DB | Every transition traceable; duplicate ERP export detectable from audit data. |
| T-14 | 10,000 concurrent users submit/approve/export expenses | P1 | Performance | API p95 under 30 seconds; Kafka lag within SLO; no deadlocks or export backlog explosion. |
| T-15 | ERP outage for 6 hours | P1 | Resilience/ERP | Queue bounded; no lost exports; recovery and reconciliation complete without duplicate ERP records. |

---

## 11. Automation Example: Duplicate ERP Export Detection Test

Below is a Java-like pseudocode test. It uses a mock ERP that enforces idempotency by key. The test detects whether a duplicate approved event causes more than one ERP external transaction.

```java
class DuplicateErpExportE2ETest {

    @Test
    void duplicateApprovedEvent_does_not_create_second_external_transaction() {
        Postgres db = TestPostgres.start();
        Kafka kafka = TestKafka.start();
        MockErp erp = new MockErp();
        FinanceConsumer consumer = new FinanceConsumer(db, erp);

        Expense expense = Expense.create("EXP-1001", 1200, "USD", "2026-01-15");
        db.approve("EXP-1001", "MGR-1");

        String eventPayload = "{\"eventId\":\"EVT-1001\",\"expenseId\":\"EXP-1001\"}";

        kafka.produce("expense-approved", eventPayload);
        kafka.produce("expense-approved", eventPayload);

        consumer.processUntilDrained();

        List<String> createdExternalIds = erp.createdExternalTransactionIds();

        // The core assertion: ERP must have only one external transaction.
        assertThat(createdExternalIds).hasSize(1);

        Expense after = db.findById("EXP-1001");
        assertThat(after.status).isEqualTo(ExpenseStatus.EXPORTED);
        assertThat(after.erpExternalTransactionId).isEqualTo(createdExternalIds.get(0));

        List<AuditTransition> transitions =
                db.auditTransitions("EXP-1001", ExpenseStatus.EXPORTED);

        assertThat(transitions).hasSize(1);
    }
}
```

Consumer logic should be defensive:

```java
class FinanceConsumer {

    private final Postgres db;
    private final MockErp erp;

    void process(String payload) {
        Expense event = parseExpenseApprovedEvent(payload);

        Expense expense = db.findForUpdate(event.expenseId);

        if (expense == null) {
            log.warn("Expense not found: " + event.expenseId);
            return;
        }

        if (expense.status != ExpenseStatus.APPROVED) {
            log.info("Ignoring stale event for expense " + expense.id);
            return;
        }

        String idempotencyKey = "EXPORT:" + expense.id;

        ErpResponse response = erp.export(idempotencyKey, expense);

        db.transition(
            expense.id,
            ExpenseStatus.EXPORTED,
            response.externalTransactionId,
            "finance-consumer"
        );
    }
}
```

Mock ERP:

```java
class MockErp {

    private final Map<String, String> keyToExternalId = new HashMap<>();
    private final List<String> createdExternalIds = new ArrayList<>();
    private final List<ErpRequest> requests = new ArrayList<>();

    ErpResponse export(String idempotencyKey, Expense expense) {
        requests.add(new ErpRequest(idempotencyKey, expense));

        String existing = keyToExternalId.get(idempotencyKey);
        if (existing != null) {
            return new ErpResponse(existing);
        }

        String newId = "ERP-" + UUID.randomUUID();
        keyToExternalId.put(idempotencyKey, newId);
        createdExternalIds.add(newId);
        return new ErpResponse(newId);
    }

    List<String> createdExternalTransactionIds() {
        return createdExternalIds;
    }

    List<ErpRequest> requests() {
        return requests;
    }
}
```

What this test catches:

- Consumer does not re-check DB state.
- Consumer uses a non-stable idempotency key.
- Duplicate Kafka event causes duplicate ERP external transaction.
- Audit log does not record one authoritative `EXPORTED` transition.

A stronger variant would simulate a timeout:

```java
erp.simulateTimeoutAfterAccept();
consumer.export();
consumer.retryWithSameKey();
assertThat(erp.createdExternalTransactionIds()).hasSize(1);
```

---

## 12. Challenging the QA Strategy: Five Assumptions and Failure Modes

The strategy depends on several assumptions. If any assumption is false, the QA plan may miss the real failure mode.

| # | Assumption | Status | What could go wrong if false | Mitigation |
|---|---|---|---|---|
| 1 | ERP honors a stable client-generated idempotency key and returns the same external transaction ID for repeated requests. | Assumption, not a stated external ERP fact. | If ERP ignores the key, deduplicates only by request correlation, or treats retries as new transactions, duplicate ERP exports will still occur. | Use ERP-side business key, reconciliation by expense ID, outbox pattern, manual reconciliation, and ERP audit checks. Do not rely only on client-side idempotency. |
| 2 | The DB is the authoritative source of state, and the Kafka consumer can safely re-read DB state before acting. | Assumption. | If the DB is not authoritative, or events are processed from cached/event state, stale events can cause invalid approvals, exports after rejection, or duplicate exports. | Enforce DB re-check before external side effects, use row locks/optimistic versioning, audit state conflicts, and use outbox/reconciliation. |
| 3 | OCR 95% accuracy is acceptable for automatic financial data extraction. | Assumption based on the given constraint. | The remaining 5% errors may corrupt amount, vendor, tax, or date and flow into ERP. If high-value expenses are affected, financial loss can occur. | Require confidence thresholds, manual review for low-confidence results, validation rules, sampling audits, and OCR drift monitoring. |
| 4 | Three QA engineers can achieve sufficient risk coverage in a 2-week release using automation and risk-based selection. | Assumption. | If automation coverage is insufficient, critical defects may reach production. The team may be forced to release with known risk or delay release. | Use automation heavily, focus P0/P1, canary deployment, production monitoring, risk acceptance, and reduced scope if coverage is not achieved. |
| 5 | A timeout is observable enough to decide whether ERP accepted the request, or ERP can be queried by idempotency key. | Assumption. | If timeout is ambiguous and ERP cannot be queried, blind retries can create duplicate external transactions and retry storms. | Query ERP by stable key before retry, use dead-letter after max retries, circuit breaker, bounded concurrency, and reconciliation runbook. |

These assumptions matter because the most dangerous defect in this system is not a simple UI bug. It is an **asynchronous money-movement defect**: an expense becomes financially real in ERP while the application state, Kafka events, DB state, and retry logic do not agree.

---

# Final Architectural Recommendation

The safest QA architecture is:

1. **DB is source of truth.**
2. **Kafka is at-least-once, so consumers must be idempotent.**
3. **ERP export uses a stable business idempotency key.**
4. **No export occurs without authoritative DB state validation.**
5. **Every export attempt is logged and reconcilable.**
6. **Timeouts are treated as ambiguous, not failures.**
7. **ERP retries are bounded and reconcilable.**
8. **Audit logs can prove one ERP external transaction per expense.**
9. **Performance and resilience are tested, not assumed.**
10. **Release gates focus on financial integrity, not only functional success.**