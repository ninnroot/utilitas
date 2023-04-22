# Django Utilitas
Django Utilitas is a library that contains many ready-to-use utility classes so that you can just focus on the business logic of your API.

Utilitas itself is built upon many other great Django packages such as drf-ff, drf-yasg and the Django REST Framework itself.


## Feature summary
Here is a summarized version of Utilitas' features:
- pagination
- sorting
- filtering (searching)
- swagger API support
- nested read serializers
- limiting the response' field
- bulk creation of models

## Installation
```bash
pip install django-utilitas
```

## Documentation
Docs are still in progress. I have assignments to do :(


## Setting up a simple CRUD endpoint
Utilitas provides `BaseListView`, `BaseDetails` and `BaseSearchView` which are a more sophisticated version of DRF's default views.
With them, you can set up a powerful API with about 9 lines of codes.
```python
# views.py
class AccountListView(BaseListView):
    name = "Account list view" # optional
    model = Account # subclass of BaseModel
    serializer = AccountSerializer # subclass of BaseModelSerializer


class AccountDetailsView(BaseDetailsView):
    name = "Account details view"
    model = Account
    serializer = AccountSerializer


class AccountSearchView(BaseSearchView):
    name = "Account search view"
    model = Account
    serializer = AccountSerializer
```
Then, setup the urls like this. Please note that the argument must be named `obj_id`.
```python
#urls.py
urlpatterns = [
    path("accounts/", views.AccountListView.as_view(), name="account-list"),
    path("accounts/<int:obj_id>", views.AccountDetailsView.as_view(), name="account-details"),
    path("accounts/search", views.AccountSearchView.as_view(), name="account-search"),
]
```

Then, when you go to your swagger endpoint, you should be able to see something like this:
![image](https://user-images.githubusercontent.com/70014160/206143080-2b73ff46-35b3-4241-8502-76262e8640da.png)

## Bulk Creation
When a POST request is made to list endpoints with the `bulk` query parameter set to a truthy value, a `ListSerializer` will be used to perform the creation process. 

### Request example
```python
import requests

requests.post(
    "api/books/?bulk=True",
    {
        # need to set this 'objects' parameter in the request body
        "objects": [
            {"title": "The Hobbit", "author": "J. R. R. Tolkein"},
            {"title": "History of Burma", "author": "G. E. Harvey"}
        ]
    }   
)
```

### Implementation
You can either inherit the Meta class from the `BaseModelSerializer` class
```python
class BookSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Book
        fields = "__all__"
```
Or, set the `list_serializer_class` option to `utilitas.serializers.BaseListSerializer`. (more information here: https://www.django-rest-framework.org/api-guide/serializers/#listserializer)
```python
from utilitas.serializers import BaseListSerializer

class BookSerializer(BaseModelSerializer):
    class Meta:
        model = Book
        fields = "__all__"
        list_serializer_class = BaseListSerializer
```

## Changelog

- 1.3.0
    - removed the need for `related_fields` parameter. Prefetching related fields is now done automatically using the `expand` parameter provided by the client.
- 1.2.9
    - renamed file from `migrations.py` to `middlewares.py` (my stupid mistake in the first place)
- 1.2.8
    - bug fixes
- 1.2.7
    - bug fixes
- 1.2.6
    - bug fixes
- 1.2.5
    - added `exclude_params` option in search endpoints.
- 1.2.4
    - fixed bug in pagination
- 1.2.3
    - lowered required Python version
- 1.2.2
    - increased character limit for `FilterParamSerializer`'s fields.
- 1.2.1
    - added a middleware for logging database queries in each request
    - bug fixes

- 1.2.0 
    - added bulk creation

- 1.1.4 
    - bug fixes

- 1.1.3 
    - bug fixes

- 1.1.2 (the first usable version)
    - bug fixes
