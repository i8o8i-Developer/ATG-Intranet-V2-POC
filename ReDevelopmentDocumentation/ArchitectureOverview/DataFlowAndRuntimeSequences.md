# Data Flow And Runtime Sequences

## Purpose

This Document Captures The Most Important Current Operational Flows And States How They Must Be Rebuilt In The New Multitenant Platform.

## Flow One: Onboarding And Offer Acceptance

### Current Flow

- HR Or Manager Creates A Provisional Offer.
- Offer Is Sent By Email.
- Candidate Accepts The Offer Link.
- User, Profile, Department, Position, And Pay Metadata Are Created.

### Rebuild Rule

The New Platform Must Model Offer, Acceptance, Provisioning, And Employment Creation As Explicit Tenant-Scoped Workflow Steps With Audit Trails And Idempotent Provisioning.

## Flow Two: Project Setup To Delivery Execution

### Current Flow

- Project Is Created With Client, Team, Dates, And Budget Context.
- Milestones And Checkpoints Are Generated.
- Team Membership And Repository Context Are Added.
- Tasks, EOD, Alerts, And Documents Extend The Delivery Flow.

### Rebuild Rule

The New Platform Must Treat Project Creation As A Transactionally Safe Workspace Setup Flow, Not As A View That Reaches Across Multiple Shared Models.

## Flow Three: Payroll Review To Payout

### Current Flow

- Managers Review Payroll Inputs.
- Finance Filters And Approves Queue Items.
- Payment Records Persist.
- Razorpay Supports Payout Activity.
- Employee Views Payroll History And Payslips.

### Rebuild Rule

The New Platform Must Separate Compensation, Payroll Calculation, Approval, Payout, And Payslip Generation Into Explicit Finance Subdomains With Reconciliation Support.

## Flow Four: Lead Intake To Delivery Conversion

### Current Flow

- Leads Enter Through Banao.
- BA Users Add Notes, Proposals, Audits, And Workflow Updates.
- LMS Reads The Same Operational Data For Workload And Analytics.
- Downstream Delivery Matching Is Inferred Through Project And Budget Context.

### Rebuild Rule

The New Platform Must Create An Explicit Opportunity And Conversion Model So Revenue And Delivery Are Connected Through Contracts Rather Than Loose Analytical Matching.

## Flow Five: EOD To Slack Summary

### Current Flow

- Users Submit EOD Entries.
- Celery Aggregates Missing Reports And Department Summaries.
- Slack Messages And Threads Are Posted And Tracked.

### Rebuild Rule

The New Platform Must Publish Explicit Work Reporting Events And Handle Messaging Through Durable Worker Paths With Idempotent Delivery.

## Flow Six: Knowledge Authoring And Access

### Current Flow

- Author Creates A Documentation Record.
- Google File Or Document Is Created.
- Permissions Are Applied.
- Viewer Access Is Redirected To The External Document.

### Rebuild Rule

The New Platform Must Decide Clearly Between External-First And Internal-First Knowledge Viewing While Keeping Metadata, Ownership, Access, And Activity Tenant-Aware.

## Flow Seven: Compliance And Talent Operations

### Current Flow

- Assessments Are Assigned And Tracked.
- Anti-Phishing Assignments Are Linked To Project Or User Context.
- Talent And Recruitment Views Track College, Internship, And Performance Signals.

### Rebuild Rule

The New Platform Must Unify Learning, Compliance, And Talent Tracking Under Deliberate Domain Boundaries Instead Of Leaving Similar workflows Spread Across Separate legacy apps.

## Flow Design Rule

Every Rebuilt Flow Must Name Its Trigger, Owner, Tenant Scope, State Changes, External Side Effects, Audit Records, And Failure Recovery Path. If Any Of Those Are Still Implicit, The New Runtime Is Repeating The Old Ambiguity.