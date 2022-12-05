from drf_yasg import openapi

size_param = openapi.Parameter(
    "size",
    openapi.IN_QUERY,
    type=openapi.TYPE_INTEGER,
    description="set -1 to get all data",
)

page_param = openapi.Parameter(
    "page",
    openapi.IN_QUERY,
    type=openapi.TYPE_INTEGER
)

sorts_param = openapi.Parameter(
    "sorts",
    openapi.IN_QUERY,
    type=openapi.TYPE_STRING,
    description="""base64 encode - eg: ["id","name"] => WyJpZCIsICJuYW1lIl0="""
)

fields_param = openapi.Parameter(
    "fields",
    openapi.IN_QUERY,
    type=openapi.TYPE_STRING,
    description="""base64 encode - eg: ["id","name"] => WyJpZCIsICJuYW1lIl0="""
)

expand_param = openapi.Parameter(
    "expand",
    openapi.IN_QUERY,
    type=openapi.TYPE_STRING,
    description="""base64 encode - eg: ["category"] => WyJjYXRlZ29yeSJd"""
)