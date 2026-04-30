# Payments And Payroll

## Domain Summary

The Current Finance Domain Combines Compensation Setup, Payroll Review, Manager Approval, Finance Approval, Payout Execution, And Payslip Rendering. The New Platform Must Rebuild This As A Tenant-Aware Finance Product With Clear Separation Between Calculation, Approval, Execution, And Reporting.

## Current Capability Map

| Capability | Current Implementation |
| --- | --- |
| Compensation Baseline | Paydata |
| Bank Setup | Bankdetails |
| Monthly Payment Record | Paymentdata |
| Manager Review | Payroll Manager Views |
| Finance Review | Finance Payment Views |
| Gateway Execution | Razorpay-Linked Payment Activity |
| Employee Self-Service | Payroll History And Payslip Rendering |

## Current Risks

- Workflow State, Payment State, And Gateway State Are Too Closely Mixed.
- Finance Logic Depends On Cross-Domain Reads More Than It Should.
- Payslip Rendering Is Too Loosely Coupled To Ledger Design.
- Financial Visibility And Approval Need Stronger Tenant-Aware Policy Controls.

## Target Finance Architecture

### Subdomains

- Compensation Policy.
- Payroll Calculation.
- Approval Workflow.
- Payout Execution.
- Employee Payroll Portal.
- Financial Reporting.

### Target Aggregate Roots

- CompensationPlan.
- PayPeriod.
- PayrollRun.
- PayrollLineItem.
- ApprovalDecision.
- PayoutInstruction.
- PayoutExecution.
- PayslipDocument.

### Multitenancy Rule

Payroll Data Must Be Tenant-Scoped, Workspace-Scoped Where Relevant, And Protected By Explicit Capability Grants. Finance Access Cannot Rely On Loose Group Checks Alone.

## Target UI Structure

- Payroll Review Queue.
- Finance Approval Board.
- Payout Console.
- Employee Payroll Center.
- Compensation Admin Surface.

## Testing Priorities For The Rebuild

- Payroll Calculation Correctness.
- Approval Lane Integrity.
- Payout Idempotency.
- Payslip Immutability.
- Tenant-Scoped Finance Visibility.

## Finance Rule For The Rewrite

The Internal Payroll Ledger Must Stay The Source Of Truth. External Gateways Confirm Execution, But They Must Never Become The Primary Business State Store.