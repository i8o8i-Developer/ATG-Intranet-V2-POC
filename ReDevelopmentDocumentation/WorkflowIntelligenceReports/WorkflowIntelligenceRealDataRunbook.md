# Workflow Intelligence Real Data Runbook

## Plain Answer

Real Workflow Intelligence Data Appears Only After The Middleware Is Running In An Environment That Real Users Actually Use. The Feature Is Implemented. The Remaining Steps Are Deployment, Migration, Restart, Traffic Collection, And Report Generation.

## What You Already Have Before Live Traffic

- Full Route Inventory For The Project.
- Workflow Bucket Classification For Known Routes.
- Zero-Hit Visibility For Routes That Exist But Have Not Yet Been Observed.
- Dashboard And Report Pages Ready To Display Real Data Once Traffic Is Captured.

## What Becomes Real Only After Live Usage

- Hit Counts On Routes.
- Username-Level Usage Patterns.
- Department And Employee-Type Usage Patterns.
- Traffic-Based Workflow Prioritization.
- Preserve-First And Refactor-Next Guidance Grounded In Actual Production Behavior.

## Fastest Safe Path To Real Data

### Step One: Deploy The Code To A Real Environment

- Use The Normal Server Deployment Flow Or The Docker-Based Deployment Path.
- Prefer The Environment That Matches The Project Runtime Rather Than The Local Python 3.13 Virtual Environment.
- This Repository Has Historically Behaved Better In The Python 3.9.12 Docker Flow Than In A Modern Local Interpreter.

### Step Two: Run The Migration

```powershell
python manage.py migrate workflow_intelligence
```

### Step Three: Restart The Runtime

- Restart Django Or The Application Server.
- Restart Celery Worker.
- Restart Celery Beat.

### Step Four: Confirm The Dashboard Loads

- Open The Workflow Intelligence Dashboard.
- Confirm The Page Loads Without Template Or Namespace Errors.
- Confirm Report Generation Buttons Are Visible For Non-Terminal Use.

### Step Five: Allow Real Users To Use The System

- Normal User Traffic Will Start Aggregating Into Daily Route Usage Rows.
- Traffic Will Be Grouped By Route, Workflow, Username, Employee Type, And Department Context.

### Step Six: Generate Reports

#### From The UI

- Open The Workflow Intelligence Dashboard.
- Choose A Reference Date.
- Use Manual, EOD, Or Standup Report Generation Buttons.
- Open The Selected Report From The Recent Reports Panel.

#### From The CLI

##### Monday EOD Report

```powershell
python manage.py generate_workflow_intelligence_report --report-type eod --start-date 2026-04-27 --end-date 2026-04-27
```

##### Tuesday Standup Report

```powershell
python manage.py generate_workflow_intelligence_report --report-type standup --start-date 2026-04-27 --end-date 2026-04-27
```

## What To Expect From The First Few Days

### Day Zero

- Inventory Exists.
- Most Routes Still Show Zero Hits.
- Reports Are Structurally Useful But Not Yet Decision-Grade.

### Day One To Day Three

- High-Traffic Workflows Begin To Separate From Background Noise.
- Department And Employee-Type Patterns Become Visible.
- The Dashboard Becomes Useful For Prioritization Conversations.

### Day Three To Day Five

- The Team Can Begin Using Report Guidance To Rank Preserve-First, Refactor-Next, And Review-Later Work.
- Low-Hit But Business-Critical Flows Should Now Be Reviewed With Domain Owners.

## Current Output Model

### Database First

The Current Implementation Treats Database Persistence As The Primary Report Sink.

- Web-Generated Reports Persist To The Database.
- Scheduled Reports Persist To The Database.
- Report Detail Pages Read The Stored Database Snapshot.

### Optional File Export

File Output Is Still Possible From The Management Command, But It Is Not Required For The Dashboard Or Scheduled Flow. This Is Intentional Because Some Deployed Environments Do Not Allow Repository-Path Writes.

## Validation Checklist After Deployment

- Migration Completed Successfully.
- Dashboard Loads.
# Workflow Intelligence Real Data Runbook

## Plain Answer

Real Workflow Intelligence Data Appears Only When The Legacy System Is Running In An Environment Used By Real Users. The Feature Already Exists. The Goal Of This Runbook Is To Capture Current-System Usage So The Team Can Make Better Rebuild Decisions.

## What You Already Have Before Live Traffic

- Route Inventory.
- Workflow Bucket Classification.
- Dashboard And Report Surfaces.
- The Ability To Store Report Snapshots In The Database.

## What Becomes Valuable After Live Usage

- Hit Counts Per Route.
- Real User And Department Usage Patterns.
- Workflow Ranking By Operational Weight.
- Better Priority Signals For The New Build.

## Fastest Safe Path To Real Data

### Step One: Deploy The Current Workflow Intelligence Feature In A Real Legacy Environment

- Use The Normal Server Deployment Flow Or Docker-Based Runtime.
- Prefer The Environment That Matches The Current Project Runtime Closely.

### Step Two: Run The Workflow Intelligence Migration

```powershell
python manage.py migrate workflow_intelligence
```

### Step Three: Restart Runtime Components

- Restart The Django Application.
- Restart Celery Worker.
- Restart Celery Beat.

### Step Four: Confirm The Dashboard And Report Generation Work

- Open The Workflow Intelligence Dashboard.
- Confirm Buttons, Recent Reports, And Report Detail Screens Load.

### Step Five: Allow Real Users To Use The Current System

- Normal Legacy Traffic Will Begin Producing Daily Aggregates.

### Step Six: Generate Reports

- Use The Dashboard For Non-Terminal Users.
- Use The Management Command For Scripted Or Scheduled Runs.

## How To Use The Results In The Rebuild Program

- Use High-Traffic Workflows To Inform Early Delivery Priority.
- Use Low-Traffic And Zero-Hit Areas As Review Candidates, Not Deletion Candidates.
- Use Department And User-Type Patterns To Confirm Persona Importance In The New UX.
- Use The Results Again During Cutover To Compare Legacy And New Adoption.

## Validation Checklist

- Migration Completed Successfully.
- Dashboard Loads.
- Report Generation Creates Report Rows.
- Report Detail Page Opens.
- Daily Usage Rows Increase As Users Browse The Legacy System.
- Scheduled Tasks Stay Healthy.

## Historical Data Limitation

The Middleware Cannot Recreate Old Traffic That Was Never Captured. Historical Validation Requires Proxy Logs, Existing Access Logs, Or Other Prior Analytics Exports.

## Final Runbook Rule

Treat Workflow Intelligence Real Data As Discovery Evidence For The Rebuild. It Improves Sequencing And Validation, But It Does Not Replace Domain Review, Migration Analysis, Or Business Confirmation.