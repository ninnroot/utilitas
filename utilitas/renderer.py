from rest_framework.renderers import JSONRenderer

class CustomRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None, **kwargs):

        if "message" not in data.keys():
            data["message"] = ""

        return super(CustomRenderer, self).render(
            data, accepted_media_type, renderer_context
        )