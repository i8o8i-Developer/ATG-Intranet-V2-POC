from rest_framework import serializers

from Backend.Apps.AtgDocs.models import DocumentVersion, DriveFile, DriveFolder, KnowledgeActivity, KnowledgeDocument, KnowledgePermission


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
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
    document_type = serializers.CharField(default="Article")
    status = serializers.CharField(default="Draft")
    slug = serializers.SlugField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)


class DriveUploadSerializer(serializers.Serializer):
    folder_name = serializers.CharField(default="ATG Docs")
    make_public = serializers.BooleanField(default=False)


class KnowledgePermissionGrantSerializer(serializers.Serializer):
    subject_type = serializers.CharField(max_length=80)
    subject_id = serializers.CharField(max_length=120)
    permission = serializers.CharField(default="Read")
    email = serializers.EmailField(required=False, allow_blank=True)
