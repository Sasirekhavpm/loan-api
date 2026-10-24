from django.db.models import Sum
from rest_framework import serializers
from .models import LoanMaster, CollData


class LoanMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanMaster
        fields = '__all__'
        read_only_fields = ['pending_amount']


class CollDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollData
        fields = '__all__'


class LoanMasterDetailSerializer(serializers.ModelSerializer):
    """Includes nested collection entries — useful for a loan detail / statement screen."""
    collections = CollDataSerializer(many=True, read_only=True)
    total_collected = serializers.SerializerMethodField()

    class Meta:
        model = LoanMaster
        fields = '__all__'

    def get_total_collected(self, obj):
        total = obj.collections.aggregate(total=Sum('coll_amount'))['total']
        return total or 0
