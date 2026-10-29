from contextlib import contextmanager

from rest_framework import serializers


class AuditableModelSerializer(serializers.ModelSerializer):
    """
    Adds audit fields as read-only while preserving DRF's fields/exclude contract.
    """

    def get_field_names(self, declared_fields, info):
        with self._extend_meta_exclude([]):
            return super().get_field_names(declared_fields, info)

    def get_extra_kwargs(self):
        with self._extend_meta_read_only(
            [
                "created",
                "created_by",
                "updated",
                "updated_by",
                "is_deleted",
                "deleted",
                "deleted_by",
            ]
        ):
            return super().get_extra_kwargs()

    @contextmanager
    def _extend_meta_exclude(self, field_names):
        fields = getattr(self.Meta, "fields", None)
        exclude = getattr(self.Meta, "exclude", None)

        if fields is not None:
            yield
            return

        if exclude is None:
            yield
            return

        with self._temporary_meta_options(
            exclude=self._merge_field_names(exclude, field_names),
        ):
            yield

    @contextmanager
    def _extend_meta_read_only(self, field_names):
        read_only_fields = getattr(self.Meta, "read_only_fields", [])
        with self._temporary_meta_options(
            read_only_fields=self._merge_field_names(read_only_fields, field_names),
        ):
            yield

    @contextmanager
    def _temporary_meta_options(self, **options):
        meta = type("Meta", (self.Meta,), options)
        original_meta = self.__dict__.get("Meta")
        had_original_meta = "Meta" in self.__dict__
        self.Meta = meta
        try:
            yield
        finally:
            if had_original_meta:
                self.Meta = original_meta
            else:
                del self.Meta

    @staticmethod
    def _merge_field_names(*field_groups):
        fields = []
        for field_group in field_groups:
            for field_name in field_group or []:
                if field_name not in fields:
                    fields.append(field_name)
        return fields

    def update(self, instance, validated_data):
        performed_by = validated_data.pop("performed_by")
        serializers.raise_errors_on_nested_writes("update", self, validated_data)
        info = serializers.model_meta.get_field_info(instance)

        m2m_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                setattr(instance, attr, value)

        instance.save(performed_by=performed_by)

        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            field.set(value)

        return instance


class ExcludeDeleteModelSerializer(AuditableModelSerializer):
    """
    Excludes soft-delete fields from model serializer output.
    """

    def get_field_names(self, declared_fields, info):
        with self._extend_meta_exclude(["is_deleted", "deleted", "deleted_by"]):
            return super().get_field_names(declared_fields, info)


class ExcludeAuditableModelSerializer(ExcludeDeleteModelSerializer):
    """
    Excludes audit and soft-delete fields from model serializer output.
    """

    def get_field_names(self, declared_fields, info):
        with self._extend_meta_exclude(["created", "created_by", "updated", "updated_by"]):
            return super().get_field_names(declared_fields, info)
