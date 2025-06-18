from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPageNumberPagination(PageNumberPagination):
    """
    ✅ КАСТОМНАЯ ПАГИНАЦИЯ
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'pagination': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
                'page_size': self.page_size,
            },
            'results': data
        })


class LargeResultsSetPagination(PageNumberPagination):
    """Пагинация для больших наборов данных"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 200


class SmallResultsSetPagination(PageNumberPagination):
    """Пагинация для маленьких наборов данных"""
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 50