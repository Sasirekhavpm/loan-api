from django.db.models import Sum, Max
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import LoanMaster, CollData
from .serializers import (
    LoanMasterSerializer,
    LoanMasterDetailSerializer,
    CollDataSerializer,
)


class LoanMasterViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for LoanMaster.
    GET    /api/loans/            -> list all loans
    POST   /api/loans/            -> create a loan
    GET    /api/loans/{loan_no}/  -> retrieve one loan (with collections + total_collected)
    PUT    /api/loans/{loan_no}/  -> full update
    PATCH  /api/loans/{loan_no}/  -> partial update
    DELETE /api/loans/{loan_no}/  -> delete
    GET    /api/loans/pending/    -> report of loans with outstanding pending amount
    """
    #queryset = LoanMaster.objects.all().order_by('-loan_date')
    queryset = LoanMaster.objects.all().order_by('-loan_no')
    filter_backends = [filters.SearchFilter]
    search_fields = ['person_name', 'guarantor_name', 'loan_status']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LoanMasterDetailSerializer
        return LoanMasterSerializer

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Report: loans where PendingAmount > 0, ordered by highest pending first."""
        loans = self.get_queryset().filter(pending_amount__gt=0).order_by('-pending_amount')
        serializer = LoanMasterSerializer(loans, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def next_number(self, request):
        """
        Returns the next available LoanNo (MAX + 1).
        Table has no IDENTITY column, so this is computed on request rather than DB-assigned.
        Note: under concurrent access two clients could get the same number back-to-back;
        the client should still handle a duplicate-key error on save as a fallback.
        """
        max_loan_no = LoanMaster.objects.aggregate(m=Max('loan_no'))['m'] or 0
        return Response({'next_loan_no': max_loan_no + 1})

    def list(self, request, *args, **kwargs):
      queryset = self.filter_queryset(self.get_queryset())
      limit = request.query_params.get('limit')
      if limit and limit.isdigit():
          queryset = queryset[:int(limit)]
      serializer = self.get_serializer(queryset, many=True)
      return Response(serializer.data)

class CollDataViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for daily collection entries.
    GET    /api/collections/                -> list all entries
    POST   /api/collections/                -> add a collection entry
    GET    /api/collections/{entryno}/      -> retrieve one entry
    PUT    /api/collections/{entryno}/      -> full update
    PATCH  /api/collections/{entryno}/      -> partial update
    DELETE /api/collections/{entryno}/      -> delete
    GET    /api/collections/?loan_no=101    -> filter by loan number
    GET    /api/collections/?coll_date=2026-07-14  -> filter by date (day's collection report)
    """
    queryset = CollData.objects.all().order_by('-coll_date')
    serializer_class = CollDataSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        loan_no = self.request.query_params.get('loan_no')
        coll_date = self.request.query_params.get('coll_date')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
    
        if date_from:
            queryset = queryset.filter(coll_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(coll_date__lte=date_to)
        if loan_no:
            queryset = queryset.filter(loan_no=loan_no)
        
        return queryset

    # def perform_create(self, serializer):
    #     """
    #     Save the collection entry, then recalculate PendingAmount on the linked loan.
    #     """
    #     instance = serializer.save()
    #     self._recalculate_pending(instance.loan_no_id)

    # def perform_update(self, serializer):
    #     instance = serializer.save()
    #     self._recalculate_pending(instance.loan_no_id)

    # def perform_destroy(self, instance):
    #     loan_no = instance.loan_no_id
    #     instance.delete()
    #     self._recalculate_pending(loan_no)

    @action(detail=False, methods=['get'])
    def next_number(self, request):
        """
        Returns the next available Entryno (MAX + 1). Same caveat as LoanMaster.next_number
        regarding concurrent access — acceptable for a low-concurrency single/small-team app.
        """
        max_entryno = CollData.objects.aggregate(m=Max('entryno'))['m'] or 0
        return Response({'next_entryno': max_entryno + 1})

    # @staticmethod
    # def _recalculate_pending(loan_no):
    #     loan = LoanMaster.objects.get(pk=loan_no)
    #     total_collected = CollData.objects.filter(loan_no=loan_no).aggregate(
    #         total=Sum('coll_amount')
    #     )['total'] or 0
    #     loan.pending_amount = loan.loan_amount - total_collected
    #     loan.save(update_fields=['pending_amount'])
