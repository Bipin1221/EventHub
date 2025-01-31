from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import (viewsets,
                            mixins,
                            status)
from core.models import (Events,
                        Category)
from Events import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'category',
                OpenApiTypes.STR,
                description='Comma separated list of category IDs to filter',
            )
            
        ]
    )
)


class EventsViewSet(viewsets.ModelViewSet):
    """View for managing event APIs."""
    serializer_class = serializers.EventsDetailSerializer
    queryset = Events.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve events for the authenticated user."""
        category = self.request.query_params.get('category')
        queryset = self.queryset
        if category:
            category_ids = self._params_to_ints(category)
            queryset = queryset.filter(category__id__in= category_ids)
        return queryset.filter(
            user=self.request.user
        ).order_by('-id').distinct()
       
       
       
       
        
    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(',')]






    def get_serializer_class(self):
        """Return the appropriate serializer class for the request."""
        if self.action == 'list':
            return serializers.EventsSerializer
        
        elif self.action=='upload_image':
            return serializers.EventsImageSerializer
        
        return self.serializer_class
        

    def perform_create(self, serializer):
        """Create a new event, associating it with the authenticated user."""
        serializer.save(user=self.request.user)


    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to events."""
        event = self.get_object()
        serializer = self.get_serializer(event, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to events.',
            ),
        ]
    )
)
   
class BaseEventAttrViewSet(mixins.ListModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin,
                      viewsets.GenericViewSet):
    """base viewset for events attributes"""
   
    authentication_classes=[TokenAuthentication]
    permission_classes=[IsAuthenticated]


    def get_queryset(self):
        """filter queryset to authenticated user"""
        
       
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(events__isnull=False)

        return queryset.filter(
            user=self.request.user
        ).order_by('-name').distinct()


class CategoryViewSet(BaseEventAttrViewSet):
    """Manage category in the database."""
    serializer_class = serializers.CategorySerializer
    queryset = Category.objects.all()