from rest_framework.routers import DefaultRouter
from .views import MaintenanceEventViewSet

router = DefaultRouter()
router.register(r"maintenance", MaintenanceEventViewSet, basename="maintenance")

urlpatterns = router.urls
