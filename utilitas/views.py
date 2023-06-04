import base64
import json
import csv

from django.core.exceptions import BadRequest
from drf_yasg.utils import swagger_auto_schema
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.views import APIView, Request, Response, status
from django.db.models import (
    QuerySet,
    CharField,
    TextField,
    BooleanField,
    BigAutoField,
    DateField,
    DateTimeField,
)
from django.http import HttpResponse

from utilitas.metadata import CustomMetadata
from utilitas.pagination import CustomPagination
from utilitas.renderer import CustomRenderer
from utilitas.serializers import FilterParamSerializer
from utilitas.swagger_serializers import FilterParamsSerializer
from utilitas.swagger_query_params import *

from utilitas.models import BaseModel
from utilitas.serializers import BaseSerializer, BaseModelSerializer

from django.db.models.base import ModelBase


def get_prefetchable_fields(instance):
    opts = instance._meta
    ret = []
    for field in opts.get_fields():
        if not isinstance(instance, ModelBase):
            rel_obj_descriptor = getattr(instance.__class__, field.name, None)
        else:
            rel_obj_descriptor = getattr(instance, field.name, None)
        if rel_obj_descriptor:
            if hasattr(rel_obj_descriptor, "get_prefetch_queryset"):
                ret.append(field.name)
            else:
                rel_obj = getattr(instance, field.name)
                if hasattr(rel_obj, "get_prefetch_queryset"):
                    ret.append(field.name)
    return ret


class BaseView(APIView, CustomPagination):
    name: str = "Base view (not cringe view)"
    description: str = ""

    authentication_classes = []
    permission_classes = []
    model: BaseModel = None
    serializer: BaseSerializer = None

    # query_params' names
    fields_param = "fields"
    sorts_param = "sorts"
    expand_param = "expand"
    # customizing the response format
    renderer_classes = [CustomRenderer, BrowsableAPIRenderer]

    # Some `expand` parameters cannot be present in the model's foreign keys (client's mistakes).
    # To avoid being a chatty API, we will just quietly ignore thier mistakes.
    def translate_expand_params(self, expand):
        translated_expand = []
        # Replacing dots with Django ORM's format.
        for i in expand:
            translated_expand.append(i.replace(".", "__"))
        return set(translated_expand).intersection(
            set(get_prefetchable_fields(self.model))
        )

    @classmethod
    def _validate_attributes(cls, **kwargs):
        for i in [
            {"var": "model", "parent_class": BaseModel},
            {
                "var": "serializer",
                "parent_class": (BaseSerializer, BaseModelSerializer),
            },
        ]:
            # making sure certain class variables are implemented.
            if not getattr(cls, i["var"]):
                raise NotImplementedError(
                    f"{cls} must implement the '{i['var']}' variable."
                )

            # making sure the implemented variables are of the right class.
            if not (
                hasattr(getattr(cls, i["var"]), "__dict__")
                and issubclass(getattr(cls, i["var"]), i["parent_class"])
            ):
                raise TypeError(
                    f"'{i['var']}' in {cls} must be a subclass {i['parent_class']} instead of a {type(getattr(cls,i['var']))}"
                )
        for i in ["sorts_param", "fields_param", "expand_param"]:
            if type(getattr(cls, i)) != str:
                raise TypeError(f"Variable '{i}' in {cls} must be a string.")

        return None

    # getting query_params
    def get_query_params(self, request: Request):
        dic = {}
        dic["sorts"] = self.get_sort_param(request)
        dic["expand"] = self.get_expand_param(request)
        dic["fields"] = self.get_fields_param(request)

        return dic

    # sending metadata
    def send_metadata(self, request: Request):
        if not hasattr(self, "metadata_class"):
            return self.get(request)
        data = self.metadata_class().determine_metadata(request, self)

        return self.send_response(
            False, "metadata", {"data": data}, status=status.HTTP_200_OK
        )

        # sending a csv file as response

    def send_csv(self, request: Request, data: QuerySet, fields):
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": "attachment; filename='data.csv'"},
        )

        if len(fields) == 0:
            fields = data.model.get_fields(data.model)

        writer = csv.writer(response)
        writer.writerow(data.model.get_user_friendly_fields(data.model, fields))
        for i in data:
            lst = []
            for j in fields:
                lst.append(getattr(i, j))
            writer.writerow(lst)
        return response

    def prepare_queryset(
        self,
        request: Request,
        filter_params=None,
        exclude_params=None,
        fields=None,
        sorts=None,
        expand=None,
    ):
        if filter_params is None:
            filter_params = {}

        if exclude_params is None:
            exclude_params = {}

        if fields is None:
            fields = []

        if expand is None:
            expand = []
        # query from the database

        translated_expand = self.translate_expand_params(expand)

        queryset = (
            self.model.objects.filter(**filter_params)
            .exclude(**exclude_params)
            .prefetch_related(*translated_expand)
            .all()
            .order_by(*sorts)
        )
        return queryset

    # querying data
    def get_queryset(
        self,
        request: Request,
        filter_params=None,
        exclude_params=None,
        is_csv=False,
        fields=None,
        sorts=None,
        expand=None,
    ):
        if filter_params is None:
            filter_params = {}

        if exclude_params is None:
            exclude_params = {}

        if fields is None:
            fields = []

        if expand is None:
            expand = []
        if not is_csv:
            # query from the database

            translated_expand = self.translate_expand_params(expand)

            queryset = (
                self.model.objects.filter(**filter_params)
                .exclude(**exclude_params)
                .prefetch_related(*translated_expand)
                .all()
                .order_by(*sorts)
            )

            # paginate the queryset
            paginated_data = self.paginate_queryset(queryset, request)

            # serialize the paginated data
            serialized_data = self.get_serializer(
                paginated_data,
                many=True,
                fields=fields,
                expand=expand,
                context={"model": self.model},
            )

            return serialized_data
        else:
            return (
                self.model.objects.filter(**filter_params)
                .exclude(**exclude_params)
                .all()
            )

    # make sure the fields are actually present in the model
    def fields_are_valid(self, fields: list) -> bool:
        return set(fields).issubset(self.model.get_filterable_fields(self.model))

    # get the "field" parameter form the request's body
    def get_fields_param(self, request: Request):
        fields = request.query_params.get(self.fields_param, [])
        if fields:
            fields = self.decode_query_param(fields, self.fields_param)
        return fields

    # get the "sort" query param
    def get_sort_param(self, request: Request):
        sorts = request.query_params.get(
            self.sorts_param, []
        )  # get base64 encoded string
        if sorts:
            sorts = self.decode_query_param(
                sorts, self.sorts_param
            )  # decode base64 string
            rmv_sign_sort = [sort.replace("-", "") for sort in sorts]
            if not self.fields_are_valid(rmv_sign_sort):
                raise BadRequest(
                    f"{sorts} is not present in {self.model.__name__}'s sortable fields"
                )

        return sorts

    # get the "expand" parameter from the request's body
    def get_expand_param(self, request: Request):
        expand = request.query_params.get(self.expand_param, [])
        if expand:
            expand = self.decode_query_param(expand, self.expand_param)

        return expand

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        return self.serializer

    def get_serializer_context(self):
        return {"request": self.request, "format": self.format_kwarg, "view": self}

    @staticmethod
    def send_response(is_error: bool, message: str, payload, **kwargs) -> Response:
        return Response({"isError": is_error, "message": message, **payload}, **kwargs)

    @staticmethod
    def decode_query_param(url_string: str, param_name: str):
        try:
            param = json.loads(
                base64.urlsafe_b64decode(url_string + "=" * (4 - len(url_string) % 4))
            )
        except Exception as e:
            raise BadRequest(f"Error decoding {param_name}: " + str(e))

        return param


class BaseListView(BaseView):
    name = "Base list view"
    metadata_class = CustomMetadata

    def __init_subclass__(cls, **kwargs):
        cls._validate_attributes(**kwargs)
        return super().__init_subclass__(**kwargs)

    # @swagger_auto_schema(
    #     manual_parameters=[size_param_getter(), page_param_getter(), sorts_param_getter(sorts_param), fields_param_getter(fields_param), expand_param_getter(expand_param)]
    # )
    def get(self, request: Request):
        self.description = self.model.__doc__

        # if meta query_param is present, return metadata of the current endpoint
        if request.GET.get("meta"):
            return self.send_metadata(request)
        
        try:
            query_params = self.get_query_params(request)
        except BadRequest as e:
            return self.send_response(
                True, "bad_request", {"details": str(e)}, status=400
            )

        if request.query_params.get("csv"):
            return self.send_csv(
                request,
                self.get_queryset(
                    request, None, None, True, **query_params
                ),
                fields=query_params["fields"],
            )



        serialized_data = self.get_queryset(request, **query_params)

        # return the serialized queryset in a standardized manner
        return self.send_response(
            False,
            "success",
            {**self.get_paginated_response(), "data": serialized_data.data},
            status=status.HTTP_200_OK,
        )
    

    # create
    def post(self, request: Request):
        if request.query_params.get("bulk", None):
            objs = request.data.get("objects", None)

            if objs is None:
                return self.send_response(
                    True, "Missing 'objects' parameter in request body.", {}
                )
            serialized_data = self.get_serializer(
                data=request.data["objects"], many=True
            )

            if serialized_data.is_valid():
                serialized_data.save()
                return self.send_response(
                    False,
                    "bulk-created",
                    {"data": serialized_data.data},
                    status=status.HTTP_201_CREATED,
                )

            return self.send_response(
                True,
                "creation failed because of some errors. 0 objects were created.",
                {"details": serialized_data.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )


        serialized_data = self.get_serializer(
            data=request.data,
        )
        if serialized_data.is_valid():
            serialized_data.save()
            return self.send_response(
                False,
                "created",
                {"data": serialized_data.data},
                status=status.HTTP_201_CREATED,
            )

        return self.send_response(
            True,
            "bad_request",
            {"details": serialized_data.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class BaseDetailsView(BaseView):
    _is_internal = True
    name = "Base details view"
    metadata_class = CustomMetadata

    def __init_subclass__(cls, **kwargs):
        cls._validate_attributes(**kwargs)
        return super().__init_subclass__(**kwargs)

    def _send_not_found(self, obj_id: int):
        return self.send_response(
            True,
            "not_found",
            {"details": f"{str(self.model)} with id {obj_id} does not exist."},
            status=status.HTTP_404_NOT_FOUND,
        )

    def _get_object(self, obj_id: int):
        obj = self.model.objects.filter(pk=obj_id).first()
        return obj

    # get-one
    # @swagger_auto_schema(
    #     manual_parameters=[fields_param, expand_param]
    # )
    def get(self, request: Request, obj_id: int):
        self.description = self.model.__doc__

        query_params = self.get_query_params(request)
        query_params.pop("sorts")
        obj = self._get_object(obj_id)
        if obj is None:
            return self._send_not_found(obj_id)
        serialized_data = self.get_serializer(obj, **query_params)
        return self.send_response(
            False, "success", {"data": serialized_data.data}, status=status.HTTP_200_OK
        )

    # update
    def put(self, request: Request, obj_id: int):
        obj = self._get_object(obj_id)
        if obj is None:
            return self._send_not_found(obj_id)
        serialized_data = self.get_serializer(obj, data=request.data, partial=True)
        serialized_data.is_valid(raise_exception=True)
        serialized_data.save()
        return self.send_response(
            False, "updated", {"data": serialized_data.data}, status=status.HTTP_200_OK
        )

    def delete(self, request: Request, obj_id: int):
        obj = self._get_object(obj_id)
        if obj is None:
            return self._send_not_found(obj_id)
        serialized_data = self.get_serializer(obj)
        obj.delete()
        return self.send_response(
            False, "deleted", {"data": serialized_data.data}, status=status.HTTP_200_OK
        )


class BaseSearchView(BaseView):
    _is_internal = True
    name = "Base search view"

    def __init_subclass__(cls, **kwargs):
        cls._validate_attributes(**kwargs)
        return super().__init_subclass__(**kwargs)

    def validate_body_params(self, to_be_validated):
        validated_data = []
        for i in to_be_validated:
            x = FilterParamSerializer(data=i, context={"model": self.model})
            if not x.is_valid(raise_exception=True):
                raise BadRequest(x.errors)
            validated_data.append(x.data)

        return validated_data

    @staticmethod
    def build_body_params(body_params):
        params_dict = {}
        for i in body_params:
            params_dict[i["field_name"] + "__" + i["operator"]] = (
                i["value"].split(",") if i["operator"] == "in" else i["value"]
            )

        return params_dict

    # validating with FilterParamSerializer to make sure the filter_params object is of the right format
    def get_filter_params(self, request: Request):
        filter_params = request.data.get("filter_params", {})
        validated_filter_params = self.validate_body_params(filter_params)
        return self.build_body_params(validated_filter_params)

    # building a filter_params dict to be used in querying
    @staticmethod
    def build_filter_params(filter_params):
        filter_dict = {}
        for i in filter_params:
            filter_dict[i["field_name"] + "__" + i["operator"]] = (
                i["value"].split(",") if i["operator"] == "in" else i["value"]
            )

        return filter_dict

    # get filter_params from the request
    def get_filter_params(self, request: Request):
        filter_params = request.data.get("filter_params", {})
        validated_filter_params = self.validate_body_params(filter_params)
        return self.build_body_params(validated_filter_params)

    # get exclude_params from the request
    def get_exclude_params(self, request: Request):
        exclude_params = request.data.get("exclude_params", {})
        validated_exclude_params = self.validate_body_params(exclude_params)
        return self.build_body_params(validated_exclude_params)

    # @swagger_auto_schema(
    #     request_body=FilterParamsSerializer,
    #     manual_parameters=[size_param, page_param, sorts_param, fields_param, expand_param],
    # )

    # search
    def post(self, request: Request):
        filter_params = {}
        try:
            query_params = self.get_query_params(request)
            filter_params = self.get_filter_params(request)
            exclude_params = self.get_exclude_params(request)
        except BadRequest as e:
            return self.send_response(
                True, "bad_request", {"details": str(e)}, status=400
            )

        if request.query_params.get("csv"):
            return self.send_csv(
                request,
                self.get_queryset(
                    request, filter_params, exclude_params, True, **query_params
                ),
                fields=query_params["fields"],
            )

        serialized_data = self.get_queryset(
            request, filter_params, exclude_params, **query_params
        )

        # return the serialized queryset in a standardized manner
        return self.send_response(
            False,
            "success",
            {**self.get_paginated_response(), "data": serialized_data.data},
            status=status.HTTP_200_OK,
        )
