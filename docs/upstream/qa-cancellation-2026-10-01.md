# QA waiting and request ownership

This bounded follow-on starts from the coherent Draft #76, exact head `519684a0056abdceb3e25c1d8ea02efd81e6e324`. It adds no dependency and does not incorporate failed catalog PR #71 or any of its diagnostics.

## Reproduced failures

Two new private regressions failed against the unchanged #76 runtime while its nine existing QA page cases passed:

1. A QA promise that never settled left the submit button disabled with no stop control.
2. Navigating to another section in the same course kept the old operation alive. Its delayed answer appeared beneath the new section heading and persisted to the course conversation.

These were distinct from the existing wrong-course guard. The successful #76 acceptance suite did not cover these cases.

## Actual runtime behavior

`QAPage` explicit submission owns one fresh AbortController and operation object → `bookApi.askCourse` forwards its signal → the existing fetch/bounded JSON/Zod path → only the current operation and committed route may update the UI or saved conversation.

- Stop waiting releases ownership before aborting and immediately permits a new explicit question. The original question remains, and there is no automatic replay or fabricated assistant answer.
- The notice says that server/model work may continue, stopping does not prove remote cancellation or undo work, and the user must decide whether to ask again. This is not a refund, transaction rollback or server-cancellation guarantee.
- Route ownership is updated in a layout effect before paint; a scope change aborts the old wait and releases loading. Unmount aborts the owned operation synchronously. An abandoned operation cannot reappear after Back/Forward.
- Object identity acts as the request generation token. A late success, error or finally block cannot append/persist content, replace an error or clear loading for a newer question, even if a mock or transport ignores abort.
- Duplicate submits remain blocked. A caller abort during either success or error body reading remains AbortError in the existing bounded response path.
- The v1 course-scoped session shape and keys remain unchanged. Completed history is preserved, not silently cleared on a new section. Labels now say “question-time section,” and explain that current scope applies only to new questions. No historical origin ID or title is invented when the frozen response does not contain it; verified citation links still carry the actual source identities.
- No provider protocol, server work, StudyRecord, source contract, citation authority, credential or paid call is changed. There is no new automatic response-duration timeout; the new control lets the user stop waiting.

## Checks and remaining acceptance

Local full web tests: 413 passed; typecheck passed. The focused QA page/transport suite has 19 passing cases, covering both original failures, duplicate submit, stopped-request late success/failure, safe next question, unmount, same-course scope changes, Back/Forward, course history and signal/body abort transport. The original frozen session and citation tests still pass.

Two new original-fixture browser journeys are included at desktop and narrow widths. They first let the real original backend finish retrieval and its deterministic answer, then hold response delivery. The user stops waiting, sees the honest cancellation notice, explicitly asks again, follows the validated source and reloads without an automatic resend. Both old and new responses use the real Book API; no model/body diagnostics are logged. These join the five previous journeys for seven serial pilots.

Hosted execution on the new exact head remains required; local discovery is not browser acceptance. The Windows workflow change only removes the stale word “five” from one step label, with no command, timeout or permission change. Existing Linux/Windows source extraction gates build the same code-only package, including this optional document; old v1 manifests remain compatible. Initial #76 source deliveries and their evidence are preserved separately.
