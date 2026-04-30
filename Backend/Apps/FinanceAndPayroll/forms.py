from django import forms

from Backend.Apps.FinanceAndPayroll.models import CompensationPlan, PaymentOrder, PayrollRun, PayoutExecution


class CompensationPlanForm(forms.ModelForm):
    class Meta:
        model = CompensationPlan
        fields = ["employee", "plan_name", "base_amount", "currency", "frequency", "starts_on", "ends_on", "component_payload"]


class PayrollRunForm(forms.ModelForm):
    class Meta:
        model = PayrollRun
        fields = ["pay_period", "status", "metadata"]


class PayoutExecutionForm(forms.ModelForm):
    class Meta:
        model = PayoutExecution
        fields = ["payroll_run", "provider", "status", "amount", "currency", "external_id", "response_payload"]


class PaymentOrderForm(forms.ModelForm):
    class Meta:
        model = PaymentOrder
        fields = ["provider", "employee", "amount", "currency", "status", "receipt", "notes"]
