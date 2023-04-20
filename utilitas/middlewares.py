import logging

from django.conf import settings
from django.db import connection


class QueryLoggerMiddleware:
    def __init__(self, get_response):
        self.logger = logging.getLogger("django")
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if settings.DEBUG:
            self.logger.info(f"Total number of queries: {len(connection.queries)}")
            for i, j in enumerate(connection.queries):
                self.logger.info(f"{i}:{float(j['time'])*1000}ms| {j['sql']}")
        return response
