from rest_framework.pagination import PageNumberPagination


class FormationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def paginated_response(request, queryset, serializer_class):
    paginator = FormationPagination()
    if not queryset.ordered:
        queryset = queryset.order_by("pk")
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(page, many=True)
    return paginator.get_paginated_response(serializer.data)
