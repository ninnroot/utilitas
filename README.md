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

