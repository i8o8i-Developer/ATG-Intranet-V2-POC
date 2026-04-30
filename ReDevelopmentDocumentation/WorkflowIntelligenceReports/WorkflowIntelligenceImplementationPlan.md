# Workflow Intelligence Implementation Plan

## Purpose

This Document Explains The Workflow Intelligence Feature Implemented In The Current Repository And How It Should Be Used During The Full Rebuild Program. It Is A Discovery And Prioritization Instrument, Not The Future Platform Architecture Itself.

## Current Implementation Status

The Feature Is Already Implemented In The Legacy Repository As A Working Slice With Middleware Instrumentation, Reporting Services, Stored Snapshots, And User-Facing Report Pages.

### Implemented Today

- A Dedicated `workflow_intelligence` App.
- Middleware-Based Request Instrumentation.
- Daily Aggregated Route Usage Persistence.
- Business Workflow Classification.
- Dashboard And Report Detail Pages.
- Database-Persisted Report Snapshots.
- Management Command And Scheduled Report Generation.

## Why It Still Matters Under The New Direction

The Program Has Moved To A Full Rebuild From Scratch, But Workflow Intelligence Remains Valuable Because It Gives The Team Real Usage Evidence From The Current System.

It Helps Answer:

1. Which Current Workflows Carry Real Operational Weight?
2. Which Routes Are Actively Used By Real Users?
3. Which Domains Should Be Prioritized During The New Build?
4. Which Low-Traffic Areas Still Need Human Confirmation Before They Are Rebuilt Or Deprioritized?

## What The Feature Captures Today

| Area | Captured Detail |
| --- | --- |
| Route Usage | Route Pattern, App, View, Workflow Group, Hit Count |
| User Context | Username, Employee Type, Department Membership |
| Aggregation Window | Daily Usage Totals For Manual, EOD, Or Standup Reporting |
| Report Snapshot | Persisted Markdown And JSON Report Output |
| Rebuild Guidance | Preserve-First, Refactor-Next, And Review-Later Suggestions |

## How To Read The Output During The Rebuild

- High-Traffic Workflows Should Shape Delivery Priority.
- Low-Traffic Routes Are Not Automatically Obsolete.
- Zero-Hit Routes Need Business Confirmation, Not Blind Deletion.
- Workflow Intelligence Is Evidence For Sequencing, Not The Only Decision Input.

## Role In The New Program

During The New Intranet Build, Workflow Intelligence Should Be Used To:

- Prioritize Which Domains And Screens Are Rebuilt Earlier.
- Confirm Which Current Pages Need Exact Capability Preservation.
- Compare Legacy Adoption Against New-Platform Adoption During Pilot And Cutover.
- Support Migration And Rollout Validation With Real Usage Context.

## Request Capture Flow In The Current System

1. A Request Enters Django.
2. Authentication Resolves The Current User.
3. Workflow Middleware Runs After The Response.
4. Route Context And Workflow Bucket Are Resolved.
5. Daily Aggregate Rows Are Created Or Incremented.
6. Reporting Services Build Human-Readable Snapshots.

## Why Daily Aggregation Was The Right Legacy Choice

- It Is Lighter Than Raw Event Logging.
- It Preserves Useful Business Signals Without Exploding Storage.
- It Is Good Enough For Rebuild Prioritization.

## Future Rebuild Implication

The New Platform Should Reimplement Workflow Intelligence Later As A Tenant-Aware Product Analytics Surface, But That Reimplementation Should Happen On Top Of The New APIs And Read Models, Not By Treating The Legacy App As The Final Shape.

## Validation Rule

Use Workflow Intelligence To Inform Scope And Sequence, But Never Use It Alone To Approve Deletion Of A Business Capability.