import django_filters
from core.models import Events


class EventFilter(django_filters.FilterSet):
    vip_price__gte = django_filters.NumberFilter(field_name='vip_price', lookup_expr='gte')
    vip_price__lte = django_filters.NumberFilter(field_name='vip_price', lookup_expr='lte')
    common_price__gte = django_filters.NumberFilter(field_name='common_price', lookup_expr='gte')
    common_price__lte = django_filters.NumberFilter(field_name='common_price', lookup_expr='lte')
    venue_location = django_filters.CharFilter(lookup_expr='icontains')
    # user_name = django_filters.CharFilter(field_name='user__name', lookup_expr='icontains')
    category = django_filters.CharFilter(field_name='category__name', lookup_expr='exact')
    event_date = django_filters.DateFilter(field_name='event_date', lookup_expr='exact')  # adjust if needed
    organizer_name = django_filters.CharFilter(field_name='user__name', lookup_expr='icontains')
    class Meta:
        model = Events
        fields = []
