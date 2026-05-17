from rest_framework import serializers

from Backend.Apps.AtgDocs.models import DocumentVersion, DriveFile, DriveFolder, KnowledgeActivity, KnowledgeDocument, KnowledgePermission


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()

    def get_owner_name(self, obj):
        return obj.owner.display_name if obj.owner else None

    def get_department_name(self, obj):
        return obj.department.name if obj.department else None

    class Meta:
        model = KnowledgeDocument
        fields = "__all__"


class KnowledgePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgePermission
        fields = "__all__"


class KnowledgeActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeActivity
        fields = "__all__"


class DriveFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriveFolder
        fields = "__all__"


class DriveFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriveFile
        fields = "__all__"


class DocumentVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentVersion
        fields = "__all__"


class KnowledgeDocumentCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=240)
    body = serializers.CharField(required=False, allow_blank=True)
    owner = serializers.IntegerField(required=False, allow_null=True)
    department = serializers.IntegerField(required=False, allow_null=True)
    document_type = serializers.CharField(default="Article")
    status = serializers.CharField(default="Draft")
    visibility = serializers.ChoiceField(choices=KnowledgeDocument.VISIBILITY_CHOICES, default=KnowledgeDocument.VISIBILITY_PRIVATE)
    slug = serializers.SlugField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)
    upload_to_drive = serializers.BooleanField(default=False)
    folder_name = serializers.CharField(required=False, allow_blank=True, default="Documents")
    make_public = serializers.BooleanField(required=False)


class KnowledgeDocumentUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=240, required=False)
    body = serializers.CharField(required=False, allow_blank=True)
    department = serializers.IntegerField(required=False, allow_null=True)
    document_type = serializers.CharField(required=False)
    status = serializers.CharField(required=False)
    visibility = serializers.ChoiceField(choices=KnowledgeDocument.VISIBILITY_CHOICES, required=False)
    slug = serializers.SlugField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)


class DriveUploadSerializer(serializers.Serializer):
    folder_name = serializers.CharField(default="Documents")
    make_public = serializers.BooleanField(required=False)


class KnowledgePermissionGrantSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    permission = serializers.CharField(default="Read")
    email = serializers.EmailField(required=False, allow_blank=True)
