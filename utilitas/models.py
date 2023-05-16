from django.db import models
from typing import Collection
RELATION_FIELDS = ["ForeignKey", "OneToOneField"]

class BaseModel(models.Model):
    valid_operators = ["exact", "iexact", "in", "lt", "gt", "lte", "gte", "icontains"]

    def __init__(self, *args, **kwargs):
        chosen_set = set(self.chosen_one_fields)
        field_set = set([i.name for i in self._meta.get_fields()])
        if not chosen_set.issubset(field_set):
            raise AttributeError(
                str(chosen_set.difference(field_set))
                + f" are not present in {self.__class__.__name__}'s fields"
            )
        super().__init__(*args, **kwargs)

    # model fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # only one row can be True throughout the entire table.
    chosen_one_fields = []

    # alias for the field names
    user_friendly_fields = {

    }

    # provided a list of untransformed field, this function will return a list (in the same order)
    # of fields translated with user-friendly names.
    def get_user_friendly_fields(self, fields: Collection[str]):
        # the 'fields' parameter can contain fields that are not in the 'self.user_firendly_fields' list.
        # if that's the case, just return the field name as is.
        lst = []
        for i in fields:
            lst.append(self.user_friendly_fields.get(i, i))
        return lst


    # get the field of the model
    def get_fields(self, include_foreign_fields=False):
        if not include_foreign_fields:
            # TODO: clean this up
            return [i.name for i in self._meta.get_fields() if isinstance(i, (models.CharField, models.TextField, models.BigAutoField, models.DateField, models.DateTimeField, models.BooleanField))]
        return [i.name for i in self._meta.get_fields()]


    def save(self, *args, **kwargs):
        for i in self.chosen_one_fields:
            if getattr(self, i):
                try:
                    obj = self.__class__.objects.get(**{i: True})
                    if obj != self:
                        setattr(obj, i, False)
                        obj.save()
                except self.__class__.DoesNotExist:
                    pass
        return super().save(*args, **kwargs)

    class Meta:
        abstract = True
        ordering = ["id"]

    def get_filterable_fields(self) -> set:
        return set([i.name for i in self._meta.get_fields()])