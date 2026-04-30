from Backend.Apps.Users.models import EmployeePaymentSnapshot


class EmployeePaymentSnapshotResource:
    fields = ["employee_id", "month", "year", "normal_pay", "bonus", "deduction", "bounty", "payment_status", "payout_id", "utr_number"]

    def export_rows(self, queryset):
        queryset = queryset or EmployeePaymentSnapshot.objects.none()
        return [{field: getattr(item, field) for field in self.fields} for item in queryset]
