# Security Audit Report — Educational ERP LMS System

**Sprint 7 — Task 19**
**Date:** 2026-06-02
**Reviewer:** Security Audit (S7-T19)
**Odoo Version:** 19.0 Community Edition

---

## 1. Security Group Definitions

The system defines six custom groups in `education_security/security/security.xml`, plus two Odoo built-in portal/public groups used as role anchors.

| # | XML ID | Display Name | User Type | Implied Groups |
|---|--------|-------------|-----------|----------------|
| 1 | `education_security.group_education_admin` | Administrator | Internal | `base.group_user` |
| 2 | `education_security.group_education_admission_officer` | Admission Officer | Internal | `base.group_user` |
| 3 | `education_security.group_education_teacher` | Teacher | Internal | `base.group_user` |
| 4 | `education_security.group_education_student` | Student | Portal | `base.group_portal` |
| 5 | `education_security.group_education_parent` | Parent / Guardian | Portal | `base.group_portal` |
| 6 | `education_security.group_education_accountant` | Accountant | Internal | `base.group_user` |
| 7 | `base.group_user` | Internal User | Internal | — |
| 8 | `base.group_portal` | Portal User | Portal | — |
| 9 | `base.group_public` | Public / Anonymous | Public | — |

> **Note on group_education_student / group_education_parent:** Both are portal groups (`implied_ids` → `base.group_portal`). They do NOT inherit `base.group_user`, so they have no access to back-office menus. Record-level isolation (row-level security rules) further limits them to their own data.

---

## 2. Access Rule Matrix by Module

Legend:
- **R** = perm\_read, **W** = perm\_write, **C** = perm\_create, **D** = perm\_unlink (delete)
- `✓` = granted, `—` = denied, `RO` = read-only (R only)

### 2.1 education\_core

| Model | Admin | Admission Officer | Teacher | Accountant | Student (portal) | Parent (portal) | group\_user | group\_portal | group\_public |
|-------|-------|-------------------|---------|------------|-----------------|-----------------|-------------|---------------|---------------|
| `education.department` | RWCD | — | — | — | — | — | RO | — | — |
| `education.academic.year` | RWCD | — | — | — | — | — | RO | — | — |
| `education.program` | RWCD | RO | — | — | — | — | RO | — | — |
| `education.class` | RWCD | RW | RO | — | — | — | RO | — | — |
| `education.timetable` | RWCD | — | RO | — | — | — | RO | — | — |
| `education.timetable.slot` | RWCD | — | RO | — | — | — | RO | — | — |
| `education.application` | RWCD | RWC | — | — | RO (own only)¹ | — | — | RO (own only)¹ | — |
| `education.enrollment` | RWCD | RWC | RO | — | RO (own only)² | — | — | RO (own only)² | — |
| `education.document.type` | RWCD | — | — | — | — | — | RO | RO | — |
| `education.document` | RWCD | RWCD | — | — | RWC (own only)³ | — | — | RWC (own only)³ | — |
| `education.attendance` | RWCD | — | RWC | — | — | — | RO | — | — |
| `education.leave.request` | RWCD | — | RW | — | RWC (own only) | — | — | RWC (own only) | — |
| `edu.classroom` | RWCD | — | RO | — | — | — | RO | — | — |

**Portal record rules (education\_core):**

1. `rule_application_portal_own` — Portal user: `[('email', '=', user.email)]` (read only)
2. `rule_enrollment_portal_own` — Portal user: `[('student_partner_id', '=', user.partner_id.id)]` (read only)
3. `rule_document_portal_own` — Portal user: `[('enrollment_id.student_partner_id', '=', user.partner_id.id)]` (RWC, no delete)

**Multi-company isolation rules** apply to all core models: `academic_year`, `department`, `program`, `class`, `timetable`, `application`, `enrollment` are filtered by `company_id in company_ids`.

---

### 2.2 education\_exam

| Model | Admin | Teacher | Accountant | Student (portal) | group\_user | group\_portal |
|-------|-------|---------|------------|-----------------|-------------|---------------|
| `edu.exam` | RWCD | RW | — | — | RO | — |
| `edu.exam.subject` | RWCD | RW | — | — | RO | — |
| `edu.exam.seating` | RWCD | RO | — | — | RO | — |
| `edu.exam.invigilator` | RWCD | RW | — | — | — | — |
| `edu.exam.result` | RWCD | RWC | — | RO (own only)⁴ | — | RO (own only)⁴ |
| `edu.exam.result.history` | RWCD | RO | — | — | — | — |
| `edu.exam.mark.entry.wizard` | RWCD | RWCD | — | — | — | — |
| `edu.exam.mark.entry.line` | RWCD | RWCD | — | — | — | — |
| `edu.exam.reevaluation.wizard` | RWCD | — | — | RWCD | — | RWCD |

4. `edu.exam.result` portal row: `base.group_portal` has read access to result records. No explicit record rule scoped to own results was found in `ir.model.access.csv`; a record rule scoping portal to `enrollment_id.student_partner_id = user.partner_id.id` **should be added** (see gap analysis §5).

**Cross-role denial example:** A student (portal) has no write/create/delete on `edu.exam.result` — they cannot falsify their own marks. A teacher has RWC but not delete — published results cannot be silently removed without admin intervention.

---

### 2.3 education\_financial\_management

| Model | Admin | Accountant (`account.group_account_user`) | group\_user | group\_portal |
|-------|-------|-------------------------------------------|-------------|---------------|
| `edu.fee.plan` | RWCD | RWC | RO | — |
| `edu.fee.line` | RWCD | RWC | RO | — |
| `edu.fee.outstanding` | RO | RO | — | — |

> **Note:** The `group_education_accountant` XML ID maps operationally to `account.group_account_user`. Fee plan and line management is intentionally restricted from teachers and students. No portal read on fee records is granted at model level — portal access to fee status must be mediated through a dedicated portal controller/template.

---

### 2.4 education\_library

| Model | Admin | group\_user (incl. Teacher) |
|-------|-------|-----------------------------|
| `edu.library.book` | RWCD | RO |
| `edu.library.book.category` | RWCD | RO |
| `edu.library.member` | RWCD | RO |
| `edu.library.loan` | RWCD | RO |
| `edu.library.issue.wizard` | RWCD | RWCD |

> Teachers and other internal users can read catalogue and issue books via the wizard but cannot create loan records directly. Student portal users have no model-level access to library; book availability should be surfaced through portal templates.

---

### 2.5 education\_hostel

| Model | Admin | group\_user (incl. Teacher) | group\_portal |
|-------|-------|-----------------------------|---------------|
| `edu.hostel.property` | RWCD | RO | — |
| `edu.hostel.room` | RWCD | RO | — |
| `edu.hostel.allocation` | RWCD | RO | — |

> Hostel allocations are admin-managed. Students and parents have no hostel model access; personal allocation can be surfaced via portal template + sudo read.

---

### 2.6 education\_transport

| Model | Admin | group\_user (incl. Teacher) | group\_portal |
|-------|-------|-----------------------------|---------------|
| `edu.transport.vehicle` | RWCD | RO | — |
| `edu.transport.route` | RWCD | RO | — |
| `edu.transport.stop` | RWCD | RO | — |
| `edu.transport.assignment` | RWCD | RO | — |

> Transport assignments are admin-only. Students/parents access assignment info only through portal templates. No portal model-level access is defined, which prevents direct ORM queries from portal sessions.

---

### 2.7 education\_notification

| Model | Admin | group\_user (incl. Teacher) |
|-------|-------|-----------------------------|
| `edu.notification.queue` | RWCD | RO |
| `edu.notification.centre` | RWCD | RW | 

> Internal users (teachers, admission officers) can create notification centre records (RWC at group\_user level for `edu.notification.centre`) but cannot delete — preserving audit trail of sent notifications.

---

### 2.8 education\_lms

| Model | Admin | Teacher | group\_user | group\_portal |
|-------|-------|---------|-------------|---------------|
| `edu.lms.course.category` | RWCD | — | RO | — |
| `education.lms.course` | RWCD | RW | RO | — |
| `education.lms.lesson` | RWCD | RWC | RO | — |
| `edu.lms.quiz` | RWCD | RWC | RO | — |
| `edu.lms.quiz.question` | RWCD | RWCD | — | — |
| `edu.lms.quiz.option` | RWCD | RWCD | — | — |
| `edu.lms.enrollment` | RWCD | — | RO | — |
| `edu.lms.quiz.attempt` | RWCD | — | RW | RW |

> Teachers can author course content (lessons, quizzes, questions) but cannot delete published courses — only admins can. Quiz attempts are writable by `group_user` and `group_portal`, enabling students to submit attempts. **Gap:** No record rule scoping portal quiz attempts to own records — a student could theoretically read other students' attempt records (see §5).

---

### 2.9 education\_alumni

| Model | Admin | group\_user (incl. Teacher) | group\_portal |
|-------|-------|-----------------------------|---------------|
| `edu.alumni` | RWCD | RO | — |

> Alumni records are visible read-only to all internal users. No portal access is granted — alumni are tracked for administrative and networking purposes only.

---

## 3. Portal Isolation Summary

The following record rules enforce row-level isolation for portal (student/parent) users:

| Rule ID | Model | Domain | Groups | Operations |
|---------|-------|--------|--------|------------|
| `rule_application_portal_own` | `education.application` | `email = user.email` | `base.group_portal` | R |
| `rule_enrollment_portal_own` | `education.enrollment` | `student_partner_id = user.partner_id` | `base.group_portal` | R |
| `rule_document_portal_own` | `education.document` | `enrollment.student_partner_id = user.partner_id` | `base.group_portal` | RWC |

**Cross-role denial examples:**

| Scenario | Denied By |
|----------|-----------|
| Student A reads Student B's exam result | `rule_enrollment_portal_own` blocks enrollment access; no direct exam result portal rule (gap — see §5) |
| Student reads another student's application | `rule_application_portal_own` (email match) |
| Parent reads unrelated student's enrollment | `rule_enrollment_portal_own` (partner match — parent must have child linked via `student_partner_id`) |
| Teacher deletes exam results | `edu.exam.result` teacher access = RWC (no D) |
| Accountant edits exam records | No access entry for accountant on any exam model |
| Portal user creates a fee plan | No `group_portal` entry on `edu.fee.plan` |
| Anonymous (public) user reads any core data | No `group_public` entry on any model |

---

## 4. Group Hierarchy and Effective Rights

```
base.group_public
  └── (no implied groups — anonymous web only)

base.group_portal
  ├── group_education_student   (portal + student-specific rules)
  └── group_education_parent    (portal + parent-specific rules)

base.group_user  (all internal users have this baseline)
  ├── group_education_admin          (RWCD all models)
  ├── group_education_admission_officer (Applications, Enrollments, Documents)
  ├── group_education_teacher        (Attendance, Exams, LMS delivery)
  └── group_education_accountant     (Fee plans, invoices — maps to account.group_account_user)
```

**Important:** `group_education_student` and `group_education_parent` do **not** imply `base.group_user`. This prevents portal users from accessing any internal back-office route, menu, or model that is only granted to `base.group_user`.

---

## 5. Security Gap Analysis

| # | Gap | Risk | Recommendation |
|---|-----|------|----------------|
| G-01 | No record rule scoping `edu.exam.result` to own enrollment for portal users | Student A can read Student B's results via RPC if both are portal users | Add `rule_exam_result_portal_own`: domain `[('enrollment_id.student_partner_id', '=', user.partner_id.id)]` on `base.group_portal` |
| G-02 | `edu.lms.quiz.attempt` writable by `base.group_portal` with no own-record rule | Portal user could update another student's quiz attempt (mark inflation) | Add record rule: `[('enrollment_id.student_partner_id', '=', user.partner_id.id)]` on `base.group_portal` for edu.lms.quiz.attempt |
| G-03 | `edu.exam.reevaluation.wizard` grants RWCD to `base.group_portal` | Any portal user (including parents) can create reevaluation requests for any exam result | Scope group to `group_education_student` only and add enrollment-match record rule |
| G-04 | `group_education_parent` has no explicit model access entries | Parents rely solely on `base.group_portal` entries — same rules as students | Consider adding separate parent-specific read-only entries scoped to child's records via a `parent_partner_id` relationship |
| G-05 | `edu.notification.centre` grants RW to `base.group_user` (no C/D) | Any internal user can modify notification records | If notifications should be system-only, restrict to admin or use `ir.rule` to limit to own-created records |
| G-06 | No `group_public` entries defined | Correct — public users have no data access | Maintain; ensure all portal routes use `@http.route(auth='user')` or `auth='public'` with explicit sudo guards |

---

## 6. OWASP Top 10 Checklist

| OWASP Risk | Description | Status in this Implementation |
|------------|-------------|-------------------------------|
| **A01 — Broken Access Control** | Users accessing resources beyond their privileges | **Partially Mitigated.** Model-level ACLs prevent broad access. Record rules enforce own-record isolation for portal users on applications, enrollments, documents. Gaps G-01, G-02, G-03 remain (see §5). |
| **A02 — Cryptographic Failures** | Sensitive data exposed without encryption | **Mitigated (Odoo platform).** Odoo hashes passwords with PBKDF2. HTTPS/TLS is infrastructure responsibility. No plaintext credential storage in models. |
| **A03 — Injection** | SQL/ORM injection | **Mitigated (Odoo ORM).** All database access goes through Odoo ORM with parameterised queries. Direct SQL (`_cr.execute`) is not used in custom models. |
| **A04 — Insecure Design** | Missing security controls at design level | **Partially Mitigated.** Security groups defined at design time; portal isolation by default. Gap: parent role not fully differentiated from student at model level (G-04). |
| **A05 — Security Misconfiguration** | Default credentials, unnecessary features enabled | **Mitigated.** `base.user_admin` is the only user added to `group_education_admin` by default. Demo data does not create test users with admin privileges. `installable: True, application: False` reduces attack surface. |
| **A06 — Vulnerable and Outdated Components** | Using components with known vulnerabilities | **Responsibility shared.** Odoo 19 is the current version. Dependency upgrades tracked via Odoo's release cycle. Custom addon has no additional Python dependencies. |
| **A07 — Identification and Authentication Failures** | Weak authentication, session management | **Mitigated (Odoo platform).** Odoo manages session tokens, password policies, and 2FA (if configured). Portal accounts created via `_create_portal_user` follow Odoo's invitation flow with email verification. |
| **A08 — Software and Data Integrity Failures** | Unsigned code updates, insecure CI/CD | **Partially Mitigated.** Module code reviewed before deployment. No auto-update mechanism in custom modules. LGPL-3 license applied to all modules. CI/CD pipeline integrity is infrastructure responsibility. |
| **A09 — Security Logging and Monitoring Failures** | Insufficient logging | **Partially Mitigated.** `mail.thread` mixin (`_inherit`) on core models (enrollment, alumni, exams, fee) records field-level changes via `tracking=True`. Odoo's built-in audit log captures login/logout. Dedicated `education_audit` module exists in the addon set for extended audit logging. |
| **A10 — Server-Side Request Forgery (SSRF)** | Server making requests to unintended locations | **Not Applicable / Mitigated.** No custom HTTP client calls in the addon codebase. External integrations (if any) are handled in `education_integrations` module with explicit URL validation. |

---

## 7. Recommendations Summary

### High Priority
1. **[G-01]** Add portal record rule for `edu.exam.result` — students must only see their own results.
2. **[G-02]** Add portal record rule for `edu.lms.quiz.attempt` — prevent cross-student attempt manipulation.
3. **[G-03]** Restrict `edu.exam.reevaluation.wizard` portal access to `group_education_student` only with enrollment match.

### Medium Priority
4. **[G-04]** Define explicit `group_education_parent` model access entries with parent→child relationship enforcement.
5. **[G-05]** Review `edu.notification.centre` write access for `base.group_user`; add own-record rule or restrict to admin.

### Low Priority / Hardening
6. Implement `group_education_admission_officer` portal restriction on `education.application` in addition to email match (use partner\_id for consistency with enrollment rule).
7. Add `active` field record rules to prevent portal users accessing archived records through explicit `active=False` domain overrides.
8. Document the `education_audit` module's scope and ensure it captures alumni record creation/modification events for GDPR compliance.

---

*Generated: 2026-06-02 | education\_security module | Odoo 19 Community Edition*
