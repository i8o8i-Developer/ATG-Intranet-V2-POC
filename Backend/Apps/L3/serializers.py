from rest_framework import serializers

from Backend.Apps.L3.models import CandidateProfile, CollegeAssignment, CollegeContact, CollegeEmailTemplate, CollegePipelineRecord, TalentAssignment, TalentEmail, TalentPerformanceSnapshot


class CollegePipelineRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollegePipelineRecord
        fields = "__all__"


class CollegeContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollegeContact
        fields = "__all__"


class CollegeAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollegeAssignment
        fields = "__all__"


class CollegeEmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollegeEmailTemplate
        fields = "__all__"


class CandidateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProfile
        fields = "__all__"


class TalentAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentAssignment
        fields = "__all__"


class TalentEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentEmail
        fields = "__all__"


class TalentPerformanceSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentPerformanceSnapshot
        fields = "__all__"
