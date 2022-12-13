# Third party imports
from rest_framework.response import Response
from rest_framework import status

# Module imports
from . import BaseViewSet, BaseAPIView
from plane.api.serializers import (
    ModuleWriteSerializer,
    ModuleSerializer,
    ModuleIssueSerializer,
)
from plane.api.permissions import ProjectEntityPermission
from plane.db.models import Module, ModuleIssue, Project


class ModuleViewSet(BaseViewSet):

    model = Module
    permission_classes = [
        ProjectEntityPermission,
    ]

    def get_serializer_class(self):
        return (
            ModuleWriteSerializer
            if self.action in ["create", "update", "partial_update"]
            else ModuleSerializer
        )

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(project_id=self.kwargs.get("project_id"))
            .filter(workspace__slug=self.kwargs.get("slug"))
            .select_related("project")
            .select_related("workspace")
            .select_related("lead")
            .prefetch_related("members")
        )

    def create(self, request, slug, project_id):
        try:
            project = Project.objects.get(workspace__slug=slug, pk=project_id)
            serializer = ModuleWriteSerializer(
                data=request.data, context={"project": project}
            )

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Project.DoesNotExist:
            return Response(
                {"error": "Project was not found"}, status=status.HTTP_404_NOT_FOUND
            )


class ModuleIssueViewSet(BaseViewSet):

    serializer_class = ModuleIssueSerializer
    model = ModuleIssue

    filterset_fields = [
        "issue__id",
        "workspace__id",
    ]

    permission_classes = [
        ProjectEntityPermission,
    ]

    def perform_create(self, serializer):
        serializer.save(
            project_id=self.kwargs.get("project_id"),
            module_id=self.kwargs.get("module_id"),
        )

    def get_queryset(self):
        return self.filter_queryset(
            super()
            .get_queryset()
            .filter(workspace__slug=self.kwargs.get("slug"))
            .filter(project_id=self.kwargs.get("project_id"))
            .filter(issue_id=self.kwargs.get("issue_id"))
            .filter(project__project_projectmember__member=self.request.user)
            .select_related("project")
            .select_related("workspace")
            .select_related("module")
            .select_related("issue")
            .distinct()
        )
