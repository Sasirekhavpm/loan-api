from decimal import Decimal

from django.db import models
from django.db.models import Sum


class LoanMaster(models.Model):
    # Same field names as before, so existing serializers/views/UI keep working.
    # Tables are now created and managed by Django migrations (PostgreSQL).
    loan_no = models.IntegerField(primary_key=True)
    loan_date = models.DateField()
    discharge_date = models.DateField()
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    person_name = models.CharField(max_length=150)
    person_address = models.CharField(max_length=200, null=True, blank=True)
    guarantor_name = models.CharField(max_length=150, null=True, blank=True)
    guarantor_address = models.CharField(max_length=200, null=True, blank=True)
    loan_status = models.CharField(max_length=10)
    remarks = models.CharField(max_length=500, null=True, blank=True)
    daily_amount = models.DecimalField(max_digits=12, decimal_places=2)
    pending_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "loan_master"

    def __str__(self):
        return f"{self.loan_no} - {self.person_name}"

    def recalc_pending(self):
        """Replaces the old SQL Server trigger: pending = loan amount - total collected."""
        collected = self.collections.aggregate(t=Sum("coll_amount"))["t"] or Decimal("0")
        self.pending_amount = Decimal(str(self.loan_amount)) - collected
        LoanMaster.objects.filter(pk=self.pk).update(pending_amount=self.pending_amount)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.recalc_pending()


class CollData(models.Model):
    entryno = models.IntegerField(primary_key=True)
    loan_no = models.ForeignKey(
        LoanMaster,
        on_delete=models.CASCADE,
        related_name="collections",
    )
    coll_date = models.DateField()
    coll_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "coll_data"
        indexes = [models.Index(fields=["loan_no", "coll_date"])]

    def __str__(self):
        return f"Entry {self.entryno} - Loan {self.loan_no_id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.loan_no.recalc_pending()

    def delete(self, *args, **kwargs):
        loan = self.loan_no
        result = super().delete(*args, **kwargs)
        loan.recalc_pending()
        return result