from rest_framework.routers import DefaultRouter
from .views import LoanMasterViewSet, CollDataViewSet

router = DefaultRouter()
router.register(r'loans', LoanMasterViewSet, basename='loanmaster')
router.register(r'collections', CollDataViewSet, basename='colldata')

urlpatterns = router.urls
