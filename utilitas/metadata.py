from rest_framework.metadata import BaseMetadata


class CustomMetadata(BaseMetadata):
    def determine_metadata(self, request, view):

        if not hasattr(view, "model"):
            return {
                "message": "no metadata in this endpoint.",
            }

        fields = []
        for i in view.model._meta.get_fields():
            if hasattr(i, "help_text"):
                fields.append(
                    {
                        "name": i.name,
                        "type": i.get_internal_type(),
                        "description": getattr(i, "help_text"),
                    }
                )

        return {
            "name": view.get_view_name(),
            "description": view.model.__doc__,
            "fields": fields,
        }