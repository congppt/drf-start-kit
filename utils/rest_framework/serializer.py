from rest_framework import serializers

class AuditableModelSerializer(serializers.ModelSerializer):
    """
    The inner Meta class on serializers does not implicitly inherit from its parents' inner Meta classes.
    If you want to customize the Meta class, you must inherit from this class explicitly.
    """
    class Meta:
        read_only_fields = ['created', 'created_by', 'updated', 'updated_by', 'is_deleted', 'deleted', 'deleted_by']
    

class ExcludeDeleteFieldsSerializer(AuditableModelSerializer):
    """
    The inner Meta class on serializers does not implicitly inherit from its parents' inner Meta classes.
    If you want to customize the Meta class, you must inherit from this class explicitly.
    """
    class Meta(AuditableModelSerializer.Meta):
        exclude = ['is_deleted', 'deleted', 'deleted_by']

class ExcludeAuditFieldsSerializer(ExcludeDeleteFieldsSerializer):
    """
    The inner Meta class on serializers does not implicitly inherit from its parents' inner Meta classes.
    If you want to customize the Meta class, you must inherit from this class explicitly.
    """
    class Meta(ExcludeDeleteFieldsSerializer.Meta):
        exclude = ['created', 'created_by', 'updated', 'updated_by'] + ExcludeDeleteFieldsSerializer.Meta.exclude