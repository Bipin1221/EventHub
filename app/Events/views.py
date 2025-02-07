from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated , AllowAny
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

from rest_framework.pagination import PageNumberPagination
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

from django.db.models import Q

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
        if self.request.user.role != 'organizer':
            raise PermissionDenied("Only organizers can create events.")
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

    @action(methods=['POST'], detail=True, url_path='show-interest')
    def show_interest(self, request, pk=None):
        """Allow attendees to show interest in an event."""
        event = self.get_object()
        user = request.user

        if user.role != 'attendee':
            raise PermissionDenied("Only attendees can show interest in events.")

        interest, created = Interest.objects.get_or_create(user=user, event=event)
        if not created:
            return Response({"message": "You have already shown interest in this event."}, status=status.HTTP_200_OK)

        return Response({"message": "Interest shown successfully."}, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=True, url_path='add-comment')
    def add_comment(self, request, pk=None):
        """Allow attendees to add comments to an event."""
        event = self.get_object()
        user = request.user

        if user.role != 'attendee':
            raise PermissionDenied("Only attendees can comment on events.")

        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user, event=event)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    @action(methods=['POST'], detail=True, url_path='rate-event')
    def rate_event(self, request, pk=None):
        """Allow attendees to rate an event."""
        event = self.get_object()
        user = request.user

        if user.role != 'attendee':
            raise PermissionDenied("Only attendees can rate events.")

        serializer = RatingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user, event=event)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    
    @action(methods=['POST'], detail=True, url_path='upload-images')
    def upload_images(self, request, pk=None):
        """Upload multiple images to an event."""
        event = self.get_object()
        images = request.FILES.getlist('images')  # Expect a list of images

        for image in images:
            EventImage.objects.create(event=event, image=image)

        return Response({"message": "Images uploaded successfully."}, status=status.HTTP_201_CREATED)

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


# from .custom_permission import readonly



class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10  # Number of events per page
    page_size_query_param = 'page_size'
    max_page_size = 100



class PublicEventsListView(generics.ListAPIView):
    """View for listing all events (no authentication required)."""
    serializer_class = serializers.PublicEventsSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Filter events by category and search query if provided."""
        queryset = Events.objects.all().order_by('-created_at')
        category = self.request.query_params.get('category')
        search_query = self.request.query_params.get('search')

        if category:
            category_ids = [int(id) for id in category.split(',')]
            queryset = queryset.filter(category__id__in=category_ids)

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | Q(description__icontains=search_query)
            )

        return queryset


class PublicEventsDetailView(generics.RetrieveAPIView):
    """View for retrieving a single event (no authentication required)."""
    serializer_class = serializers.PublicEventsDetailSerializer
    permission_classes = [AllowAny]
    
    queryset = Events.objects.all()



