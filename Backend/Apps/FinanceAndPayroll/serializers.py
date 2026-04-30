from rest_framework import serializers

from Backend.Apps.FinanceAndPayroll.models import (
    ApprovalDecision,
    BankAccount,
    CompensationPlan,
    PaymentOrder,
    PaymentWebhookEvent,
    PayPeriod,
    PayrollLineItem,
    PayrollRun,
    PayoutExecution,
    PayslipDocument,
)


class CompensationPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompensationPlan
        fields = "__all__"


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = "__all__"


class PayPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayPeriod
        fields = "__all__"


class PayrollRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRun
        fields = "__all__"


class PayrollLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollLineItem
        fields = "__all__"


class ApprovalDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalDecision
        fields = "__all__"


class PayoutExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutExecution
        fields = "__all__"


class PayslipDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayslipDocument
        fields = "__all__"


class PaymentOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentOrder
        fields = "__all__"


class PaymentWebhookEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentWebhookEvent
        fields = "__all__"


class PayrollCalculationQuerySerializer(serializers.Serializer):
    employee = serializers.IntegerField(required=False)
    user = serializers.IntegerField(required=False)
    month = serializers.IntegerField(required=False, min_value=1, max_value=12)
    year = serializers.IntegerField(required=False, min_value=2000)


class PaymentOrderCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=16, decimal_places=2)
    currency = serializers.CharField(default="INR")
    receipt = serializers.CharField(required=False, allow_blank=True)
    employee = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.JSONField(required=False)
    live = serializers.BooleanField(default=False)


class EmployeePayoutRequestSerializer(serializers.Serializer):
    payment_snapshot = serializers.IntegerField()
    live = serializers.BooleanField(default=False)
