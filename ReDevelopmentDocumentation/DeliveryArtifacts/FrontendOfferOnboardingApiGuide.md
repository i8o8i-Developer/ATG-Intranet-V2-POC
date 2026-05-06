# Frontend API Guide: Offer Acceptance And Employee Onboarding

This document is for the frontend team implementing the candidate offer acceptance and onboarding flow in `intranet-v2`.

It is based on manual Postman validation performed against the local Docker environment on May 6, 2026.

## Base URLs

Local backend:

```text
http://localhost:8000
```

Local frontend:

```text
http://localhost:5173
```

## Important Route Summary

| Purpose | Method | Endpoint | Auth |
| --- | --- | --- | --- |
| Candidate offer preview | `GET` | `/MainApp/offer/{token}` | Public token URL |
| Candidate offer acceptance | `POST` | `/MainApp/offer/{token}` | Public token URL |
| Employee login | `POST` | `/Users/Auth/Login/` | Public |
| Current logged-in user | `GET` | `/Users/Auth/Me/` | Session |
| Complete onboarding | `POST` | `/Users/EmployeeProfiles/me/complete-onboarding/` | Logged-in employee session |
| Employee profiles list | `GET` | `/Users/EmployeeProfiles/` | Authenticated admin/staff/session |

Note: the acceptance endpoint is currently:

```text
POST /MainApp/offer/{token}
```

It is **not**:

```text
POST /MainApp/offer/{token}/accept
```

## Tenant And Workspace Headers

Authenticated employee/admin APIs should include:

```text
X-Tenant-Id: 1
X-Workspace-Id: 1
```

The validated local tenant/workspace were:

```json
{
  "activeTenant": {
    "id": 1,
    "name": "Banao",
    "slug": "banao"
  },
  "activeWorkspace": {
    "id": 1,
    "name": "Default Workspace",
    "code": "DEFAULT"
  }
}
```

## Browser Auth And CSRF Notes

The backend uses Django session authentication.

For frontend requests that use the logged-in session, send cookies:

```js
fetch(url, {
  credentials: "include"
})
```

For unsafe methods such as `POST`, include the CSRF token:

```text
X-CSRFToken: <csrftoken cookie value>
```

In Postman, we confirmed that after login Django returns:

```text
Set-Cookie: csrftoken=...
Set-Cookie: sessionid=...
```

The `X-CSRFToken` header must match the latest `csrftoken` cookie for the currently logged-in user.

## Candidate Flow

Recommended frontend flow:

```text
Candidate opens /offer/:token
Frontend calls GET /MainApp/offer/:token
Frontend renders offer preview
Candidate accepts NDA and terms
Frontend calls POST /MainApp/offer/:token
Backend provisions auth.User and EmployeeProfile
Frontend shows success/check-email screen
Candidate logs in
Frontend calls POST /Users/EmployeeProfiles/me/complete-onboarding/
```

## 1. Offer Preview

### Request

```http
GET /MainApp/offer/P1FGzDKmqHyFOhO05521meNOCqunYP1jXXx6XCTksTueXAWK
```

### Sample Success Response

```json
{
  "id": 2,
  "created_at": "2026-05-06T04:25:26.624990Z",
  "updated_at": "2026-05-06T04:38:37.521960Z",
  "is_active": true,
  "source_system": "",
  "external_id": "",
  "external_url": "",
  "external_payload": {},
  "candidate_name": "Manual Test Candidate",
  "candidate_email": "manual.test@example.com",
  "company_name": "ATG",
  "position_title": "Intern",
  "offer_type": "Internship",
  "token": "P1FGzDKmqHyFOhO05521meNOCqunYP1jXXx6XCTksTueXAWK",
  "status": "Issued",
  "offer_payload": {
    "username": "manualtestcandidate",
    "department_name": "Engineering",
    "employment_type": "Intern"
  },
  "issued_at": "2026-05-06T04:38:37.521767Z",
  "expires_at": null,
  "accepted_at": null,
  "reminder_count": 0,
  "last_reminder_at": null,
  "created_by": 1,
  "updated_by": 1,
  "tenant": 1,
  "workspace": 1
}
```

### Frontend Behavior

If `status` is `Issued`, render the offer preview and acceptance controls.

If the request returns `404`, show an invalid/expired link style page.

If `status` is already `Accepted`, do not show the acceptance form. Show an already accepted/success state.

## 2. Invalid Acceptance Validation

### Request

```http
POST /MainApp/offer/{token}
Content-Type: application/json
```

```json
{
  "accepted_nda": false,
  "accepted_terms": true,
  "signature_name": "Manual Test Candidate"
}
```

### Confirmed Response

```http
400 Bad Request
```

```json
{
  "non_field_errors": [
    "You must explicitly accept the NDA and terms to proceed."
  ]
}
```

### Frontend Behavior

Disable submit until both legal checkboxes are checked.

Still handle this server response defensively and show a clear form-level validation message.

## 3. Valid Offer Acceptance

### Request

```http
POST /MainApp/offer/{token}
Content-Type: application/json
```

```json
{
  "accepted_nda": true,
  "accepted_terms": true,
  "signature_name": "Manual Test Candidate"
}
```

### Confirmed Success Response

```http
200 OK
```

```json
{
  "id": 2,
  "created_at": "2026-05-06T04:25:26.624990Z",
  "updated_at": "2026-05-06T04:44:27.214341Z",
  "is_active": true,
  "source_system": "",
  "external_id": "",
  "external_url": "",
  "external_payload": {},
  "candidate_name": "Manual Test Candidate",
  "candidate_email": "manual.test@example.com",
  "company_name": "ATG",
  "position_title": "Intern",
  "offer_type": "Internship",
  "token": "P1FGzDKmqHyFOhO05521meNOCqunYP1jXXx6XCTksTueXAWK",
  "status": "Accepted",
  "offer_payload": {
    "username": "manualtestcandidate",
    "department_name": "Engineering",
    "employment_type": "Intern",
    "acceptance": {
      "accepted_nda": true,
      "accepted_terms": true,
      "signature_name": "Manual Test Candidate"
    },
    "onboarding": {
      "username": "manualtestcandidate",
      "employee_id": 10,
      "user_id": 10,
      "provisioned": true,
      "provision_error": null
    }
  },
  "issued_at": "2026-05-06T04:38:37.521767Z",
  "expires_at": null,
  "accepted_at": "2026-05-06T04:44:24.892182Z",
  "reminder_count": 0,
  "last_reminder_at": null,
  "created_by": 1,
  "updated_by": 1,
  "tenant": 1,
  "workspace": 1
}
```

### Important Fields For Frontend

```json
{
  "status": "Accepted",
  "accepted_at": "2026-05-06T04:44:24.892182Z",
  "offer_payload": {
    "onboarding": {
      "username": "manualtestcandidate",
      "employee_id": 10,
      "user_id": 10,
      "provisioned": true,
      "provision_error": null
    }
  }
}
```

### Frontend Behavior

On `200 OK`, route to a success page:

```text
Offer accepted. Your intranet account has been created. Please check your email for credentials.
```

Do not auto-login the user from this response.

The generated password is sent by backend email. In local development, email may not be configured, so developers may manually reset the test user password.

## 4. Duplicate Acceptance

Duplicate acceptance was tested and fixed.

### Request

Same valid acceptance payload sent again:

```http
POST /MainApp/offer/{token}
```

```json
{
  "accepted_nda": true,
  "accepted_terms": true,
  "signature_name": "Manual Test Candidate"
}
```

### Confirmed Response After Fix

```http
409 Conflict
```

```json
{
  "offer": "Offer Already Accepted."
}
```

### Frontend Behavior

Treat this as a non-fatal final state.

Recommended UI:

```text
This offer has already been accepted.
```

Show a login CTA rather than an error stack.

## 5. Candidate Login

### Request

```http
POST /Users/Auth/Login/
Content-Type: application/json
```

```json
{
  "username": "manualtestcandidate",
  "password": "ManualTest123"
}
```

### Confirmed Response

```json
{
  "authenticated": true,
  "user": {
    "id": 10,
    "username": "manualtestcandidate",
    "email": "manual.test@example.com",
    "firstName": "Manual",
    "lastName": "Test Candidate",
    "fullName": "Manual Test Candidate",
    "isStaff": false,
    "isSuperuser": false
  },
  "activeTenant": {
    "id": 1,
    "name": "Banao",
    "slug": "banao"
  },
  "activeWorkspace": {
    "id": 1,
    "name": "Default Workspace",
    "code": "DEFAULT"
  },
  "employees": [
    {
      "id": 10,
      "displayName": "Manual Test Candidate",
      "employeeCode": "EMP-0010",
      "tenantId": 1,
      "workspaceId": 1,
      "departmentId": null,
      "departmentName": "",
      "positionTitle": "",
      "status": "Active"
    }
  ],
  "roles": [],
  "capabilities": []
}
```

### Frontend Behavior

Store no password client-side.

Rely on Django session cookies. For subsequent calls, send:

```js
credentials: "include"
```

Use `activeTenant.id` and `activeWorkspace.id` in headers for tenant-scoped requests.

## 6. Complete Onboarding

This endpoint operates on the **currently logged-in user**.

If admin is logged in, it completes admin onboarding.

If candidate is logged in, it completes candidate onboarding.

### Request

```http
POST /Users/EmployeeProfiles/me/complete-onboarding/
Content-Type: application/json
X-Tenant-Id: 1
X-Workspace-Id: 1
X-CSRFToken: <csrftoken cookie value>
```

```json
{}
```

### Confirmed Success Response

```json
{
  "id": 10,
  "username": "manualtestcandidate",
  "email": "manual.test@example.com",
  "created_at": "2026-05-06T04:44:25.091721Z",
  "updated_at": "2026-05-06T04:58:39.091491Z",
  "is_active": true,
  "source_system": "",
  "external_id": "",
  "external_url": "",
  "external_payload": {},
  "employee_code": "EMP-0010",
  "display_name": "Manual Test Candidate",
  "contact_number": "",
  "avatar_url": "",
  "github_username": "",
  "timezone_name": "",
  "employment_type": "Intern",
  "status": "Active",
  "joined_on": "2026-05-06",
  "exited_on": null,
  "leaves_wallet": "0.00",
  "leaves_per_month": "0.00",
  "onboarding_completed": true,
  "profile_payload": {
    "city": "",
    "offer_id": 2,
    "offer_token": "P1FGzDKmqHyFOhO05521meNOCqunYP1jXXx6XCTksTueXAWK",
    "position_title": "Intern",
    "registered_via": "offer_acceptance",
    "department_name": "Engineering",
    "emergency_contact": ""
  },
  "created_by": 1,
  "updated_by": 10,
  "tenant": 1,
  "workspace": 1,
  "user": 10,
  "department": null,
  "position": null,
  "manager": null
}
```

Important proof:

```json
{
  "onboarding_completed": true,
  "updated_by": 10
}
```

`updated_by: 10` confirms the candidate completed their own onboarding.

### Frontend Behavior

After login, call this endpoint when the candidate completes the frontend onboarding step.

On success:

```text
Mark onboarding as complete in frontend state.
Redirect to employee dashboard/home.
```

If the user is not authenticated, expect `403` or `401` depending on auth state.

If CSRF is wrong, the backend returns:

```json
{
  "detail": "CSRF Failed: CSRF token from the 'X-Csrftoken' HTTP header incorrect."
}
```

Fix by using the latest `csrftoken` cookie from the current login session.

## 7. Employee Profile Verification

### Request

```http
GET /Users/EmployeeProfiles/
X-Tenant-Id: 1
X-Workspace-Id: 1
```

### Confirmed Candidate Record

```json
{
  "id": 10,
  "username": "manualtestcandidate",
  "email": "manual.test@example.com",
  "employee_code": "EMP-0010",
  "display_name": "Manual Test Candidate",
  "employment_type": "Intern",
  "status": "Active",
  "joined_on": "2026-05-06",
  "onboarding_completed": true,
  "profile_payload": {
    "city": "",
    "offer_id": 2,
    "offer_token": "P1FGzDKmqHyFOhO05521meNOCqunYP1jXXx6XCTksTueXAWK",
    "position_title": "Intern",
    "registered_via": "offer_acceptance",
    "department_name": "Engineering",
    "emergency_contact": ""
  },
  "created_by": 1,
  "updated_by": 10,
  "tenant": 1,
  "workspace": 1,
  "user": 10,
  "department": null,
  "position": null,
  "manager": null
}
```

## 8. HR/Admin Offer Creation And Issue APIs

These are useful if the frontend includes HR/admin offer management.

### Create Offer

```http
POST /MainApp/OnboardingOffers/
Content-Type: application/json
X-Tenant-Id: 1
X-Workspace-Id: 1
X-CSRFToken: <csrftoken>
```

```json
{
  "tenant": 1,
  "workspace": 1,
  "candidate_name": "Manual Test Candidate",
  "candidate_email": "manual.test@example.com",
  "company_name": "ATG",
  "position_title": "Intern",
  "offer_type": "Internship",
  "status": "Draft",
  "offer_payload": {
    "username": "manualtestcandidate",
    "employment_type": "Intern",
    "department_name": "Engineering"
  }
}
```

### Confirmed Create Response

```http
201 Created
```

```json
{
  "id": 2,
  "created_at": "2026-05-06T04:25:26.624990Z",
  "updated_at": "2026-05-06T04:25:26.625375Z",
  "is_active": true,
  "source_system": "",
  "external_id": "",
  "external_url": "",
  "external_payload": {},
  "candidate_name": "Manual Test Candidate",
  "candidate_email": "manual.test@example.com",
  "company_name": "ATG",
  "position_title": "Intern",
  "offer_type": "Internship",
  "token": "",
  "status": "Draft",
  "offer_payload": {
    "username": "manualtestcandidate",
    "employment_type": "Intern",
    "department_name": "Engineering"
  },
  "issued_at": null,
  "expires_at": null,
  "accepted_at": null,
  "reminder_count": 0,
  "last_reminder_at": null,
  "created_by": 1,
  "updated_by": 1,
  "tenant": 1,
  "workspace": 1
}
```

### Issue Offer

```http
POST /MainApp/OnboardingOffers/{offerId}/issue/
Content-Type: application/json
X-Tenant-Id: 1
X-Workspace-Id: 1
X-CSRFToken: <csrftoken>
```

```json
{}
```

### Confirmed Issue Response

```json
{
  "id": 2,
  "created_at": "2026-05-06T04:25:26.624990Z",
  "updated_at": "2026-05-06T04:38:37.521960Z",
  "is_active": true,
  "candidate_name": "Manual Test Candidate",
  "candidate_email": "manual.test@example.com",
  "company_name": "ATG",
  "position_title": "Intern",
  "offer_type": "Internship",
  "token": "P1FGzDKmqHyFOhO05521meNOCqunYP1jXXx6XCTksTueXAWK",
  "status": "Issued",
  "offer_payload": {
    "username": "manualtestcandidate",
    "department_name": "Engineering",
    "employment_type": "Intern"
  },
  "issued_at": "2026-05-06T04:38:37.521767Z",
  "expires_at": null,
  "accepted_at": null,
  "tenant": 1,
  "workspace": 1
}
```

## 9. Error Handling Matrix

| Scenario | Status | Response Shape | Frontend Handling |
| --- | --- | --- | --- |
| Invalid token | `404` | `{ "offer": "Offer Token Not Found." }` | Show invalid link page |
| NDA/terms not accepted | `400` | `{ "non_field_errors": [...] }` | Show form validation |
| Already accepted | `409` | `{ "offer": "Offer Already Accepted." }` | Show already accepted/success page |
| Offer not issued | `409` | `{ "offer": "Offer Is Not Available For Acceptance." }` | Show unavailable offer page |
| Expired offer | `410` | `{ "offer": "Offer Token Has Expired." }` | Show expired link page |
| Missing auth on employee APIs | `403`/`401` | `{ "detail": "..." }` | Redirect to login |
| CSRF mismatch | `403` | `{ "detail": "CSRF Failed: ..." }` | Refresh CSRF token or retry login |

## 10. Frontend Implementation Checklist

- Build candidate route such as `/offer/:token`.
- Fetch offer using `GET /MainApp/offer/:token`.
- Render candidate name, company, position, offer type, and payload details.
- Disable accept button until both NDA and terms checkboxes are true.
- Submit `accepted_nda`, `accepted_terms`, and `signature_name`.
- On success, show check-email/login CTA.
- On `409 Offer Already Accepted`, show already accepted page and login CTA.
- Implement login through `POST /Users/Auth/Login/`.
- Use `credentials: "include"` for session APIs.
- Read `activeTenant.id` and `activeWorkspace.id` after login.
- Send `X-Tenant-Id`, `X-Workspace-Id`, and `X-CSRFToken` for authenticated POSTs.
- Complete onboarding through `POST /Users/EmployeeProfiles/me/complete-onboarding/`.
- Redirect to dashboard after `onboarding_completed: true`.

## 11. Manual Validation Status

The following checks were completed successfully:

```text
Create offer: passed
Issue offer: passed
Preview offer by token: passed
Invalid acceptance validation: passed
Valid acceptance and provisioning: passed
EmployeeProfile creation: passed
Duplicate acceptance rejection: passed after backend fix
Candidate login: passed
Candidate onboarding completion: passed
Final employee state verification: passed
```

