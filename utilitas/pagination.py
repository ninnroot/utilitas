import math

from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):

    page_size_query_param = "size"
    page_size = 10

    def get_page_size(self, request):
        if int(request.query_params.get(self.page_size_query_param, 0)) == -1:
            p_size = self.model.objects.count()
            if p_size != 0:
                return self.model.objects.count()
        return super().get_page_size(request)

    def get_count_per_page(self):
        return len(list(self.page))

    def get_total_pages(self):
        return math.ceil(self.page.paginator.count / self.get_page_size(self.request))

    def get_paginated_response(self, *args, **kwargs):
        return {
            "links": {
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
            },
            "count": self.page.paginator.count,
            "count_per_page": self.get_count_per_page(),
            "total_pages": self.get_total_pages(),
        }