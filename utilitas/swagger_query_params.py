from drf_yasg import openapi

def parameter_getter(param_name: str, param_type, description = ""):
    return openapi.Parameter(
        param_name,
        openapi.IN_QUERY,
        type=param_type,
        description=description
    )

def size_param_getter():
    return parameter_getter("size",openapi.TYPE_INTEGER,"set -1 to get all data")

def page_param_getter():
    return parameter_getter("page", openapi.TYPE_INTEGER)


def sorts_param_getter(name: str):
    return parameter_getter(name, type=openapi.TYPE_STRING,description="""base64 encode - eg: ["id","name"] => WyJpZCIsICJuYW1lIl0=""")

def fields_param_getter(name: str):
    return parameter_getter(name, type=openapi.TYPE_STRING,description="""base64 encode - eg: ["id","name"] => WyJpZCIsICJuYW1lIl0=""")

def expand_param_getter(name: str):
    return parameter_getter(name, type=openapi.TYPE_STRING,description="""base64 encode - eg: ["category"] => WyJjYXRlZ29yeSJd""")

