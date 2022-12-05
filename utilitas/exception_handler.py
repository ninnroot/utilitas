from rest_framework.views import Response, exception_handler


def custom_handler(exc, ctx):
    response = exception_handler(exc, ctx)
    custom_response = {"isError": True}
    if hasattr(exc, "status_code"):
        custom_response["details"] = response.data

        return Response(custom_response, status=exc.status_code)

    return response