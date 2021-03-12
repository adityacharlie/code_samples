
# SOME EXAMPLES OF THE REST ENDPOINTS DONE AT KAITONGO
# I HAVE IMPLEMENTED/MAINTAINED 90+ REST API ENDPOINTS
# WRITTEN IN DJANGO REST FRAMEWORK


# USING DJANGO REST FILTERS TO SEARCH DATA ACROSS CONNECTED
# OBJECTS

class NewsFilter(filters.FilterSet):
    dt_created = filters.BaseRangeFilter()

    class Meta:
        model = News
        fields = {'news__company': ['in'],
                  'subcategory': ['exact'],
                  'packages': ['exact'],
                  }

    @property
    def qs(self):
        parent = super().qs
        package = self.request.query_params.get('packages')
        publishable_deletable_or_archivable_news_pk = NewsPackage.objects.filter(
            package=package,
            archived=False,
            published=False).values_list('news__pk', flat=True)

        return parent.filter(
            pk__in=publishable_deletable_or_archivable_news_pk
        ).filter(
            Q(
                packages__analyst=self.request.user.analyst
            ) | Q(
                packages__project_manager=self.request.user.analyst
            )
        ).exclude(published=True).distinct()


# USAGE OF GENERIC CLASS BASED VIEWS IN DJANGO REST API
# CRUD OPERATION EXAMPLES


class RawNewsList(RawNewsAccessMixin, ListAPIView):
    """ Get list of raw news for company group X (if analyst has access) """

    def get_queryset(self):
        """
        return raw news that are in a company group for which the user has
        access, then filter again for raw news that are in the requested
        company groups
        """
        return super().get_queryset().filter(
            company__group__pk=self.kwargs.get('pk')).exclude(
            news__isnull=False)

    def list(self, request, *args, **kwargs):
        group_name = get_object_or_404(
            CompanyGroup, pk=self.kwargs.get('pk')).name
        queryset = self.filter_queryset(
            self.get_queryset().order_by('-date', 'pk'))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(
                {'group_name': group_name, 'data': serializer.data})
        serializer = self.get_serializer(queryset, many=True)
        return Response({'group_name': group_name, 'data': serializer.data})




class RawNewsDetails(RawNewsAccessMixin, RetrieveUpdateDestroyAPIView):
    """ Get details and update a single raw news (if analyst has access) """

    @superuser_access
    def get_queryset(self):
        return super().get_queryset().filter(
            company__group__in=self.request.user.analyst.company_groups.all())



class AddNews(CreateAPIView):
    """ Add news (if analyst has access) """
    queryset = News.objects.all()
    serializer_class = AddNewsSerializer
    permission_classes = IsAnalyst,
    pagination_class = None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
            headers=headers)



class ArchiveNews(NewsAccessMixin, RetrieveAPIView):
    """ archive the news `news_pk` in the package `package_pk` """

    lookup_url_kwarg = 'news_pk'

    @superuser_access
    def get_queryset(self):
        return super().get_queryset().filter(
            Q(packages__analyst=self.request.user.analyst) | Q(
                packages__project_manager=self.request.user.analyst)
        ).distinct()

    def retrieve(self, request, *args, **kwargs):
        """ set M2M through to archive on update """
        instance = self.get_object()
        package = get_object_or_404(
            Package,
            Q(analyst=self.request.user.analyst) | Q(
                project_manager=self.request.user.analyst),
            pk=self.kwargs.get('package_pk')
        )
        NewsPackage.objects.filter(news=instance, package=package).update(
            archived=True, published=False)
        return Response({'message': 'archived'})


#  A REST ENDPOINT TO CREATE A USER OF A CERTAIN TYPE IN THE WEBAPP

class CreateUserView(CreateAPIView):
    """ Create an end user/ Analyst """
    permission_classes = IsClientAdmin,
    serializer_class = EndUserCreationSerializer

    def perform_create(self, serializer, IsAnalyst):
        if IsAnalyst:
            user = serializer.save(
                firms=[self.request.user.clientadmin.firm] if hasattr(
                    self.request.user, 'clientadmin')
                else Firm.objects.first()
            )
        else:
            user = serializer.save(
                firm=self.request.user.clientadmin.firm if hasattr(
                    self.request.user, 'clientadmin')
                else Firm.objects.first()
            )

        return user

    def create(self, request, *args, **kwargs):
        if request.data.get('is_analyst'):
            IsAnalyst = True
        else:
            IsAnalyst = False

        if IsAnalyst:
            serializer = AnalystCreationSerializer(data=request.data)
        else:
            serializer = EndUserCreationSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        instance = self.perform_create(serializer, IsAnalyst)
        headers = self.get_success_headers(serializer.data)

        if instance.user_type == 'analyst':
            return Response(AnalystCreationSerializer(
                instance=instance).data,
                status=status.HTTP_201_CREATED,
                headers=headers)

        return Response(EndUserEditSerializer(
            instance=instance).data,
            status=status.HTTP_201_CREATED,
            headers=headers)
