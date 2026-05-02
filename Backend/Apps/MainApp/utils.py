import os
import re
import shlex

from django.conf import settings


def is_user_allowed(user, allowed_groups):
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return user.groups.filter(name__in=allowed_groups).exists()


def search_user(queryset, keyword=""):
    if not keyword:
        return queryset
    return queryset.filter(username__icontains=keyword) | queryset.filter(email__icontains=keyword)


class PartyRemoteAutomationError(Exception):
    """Raised when the legacy remote automation target is not configured or fails."""


class PartyRemoteAutomationProvider:
    def __init__(self, live=False, host=None, username=None, key_path=None, repo_path=None, test_path=None, session_factory=None):
        self.live = live
        self.host = host or getattr(settings, "PARTY_REMOTE_HOST", "") or os.getenv("PARTY_REMOTE_HOST", "")
        self.username = username or getattr(settings, "PARTY_REMOTE_USERNAME", "ubuntu") or os.getenv("PARTY_REMOTE_USERNAME", "ubuntu")
        self.key_path = key_path or getattr(settings, "PARTY_REMOTE_KEY_PATH", "") or os.getenv("PARTY_REMOTE_KEY_PATH", "")
        self.repo_path = repo_path or getattr(settings, "PARTY_REMOTE_REPO_PATH", "/var/www/html/atg/public_html") or os.getenv("PARTY_REMOTE_REPO_PATH", "/var/www/html/atg/public_html")
        self.test_path = test_path or getattr(settings, "PARTY_API_TEST_PATH", "atg_api_testing") or os.getenv("PARTY_API_TEST_PATH", "atg_api_testing")
        self.session_factory = session_factory

    def _ssh_command(self, command):
        if not self.live:
            return {"dry_run": True, "command": command, "stdout": ""}
        if not self.host or not self.key_path:
            raise PartyRemoteAutomationError("PARTY_REMOTE_HOST and PARTY_REMOTE_KEY_PATH Are Required For Live Remote Automation.")
        try:
            import paramiko
        except ImportError as exc:
            raise PartyRemoteAutomationError("paramiko is Required For Live Remote Automation.") from exc
        key = paramiko.RSAKey.from_private_key_file(self.key_path)
        client = self.session_factory() if self.session_factory else paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=self.host, username=self.username, pkey=key)
            _stdin, stdout, stderr = client.exec_command(command)
            output = "".join(stdout.readlines())
            error_output = "".join(stderr.readlines())
            if error_output:
                raise PartyRemoteAutomationError(error_output.strip())
            return {"dry_run": False, "command": command, "stdout": output}
        finally:
            client.close()

    def change_branch(self, branch_name="master"):
        branch = shlex.quote(branch_name or "master")
        repo_path = shlex.quote(self.repo_path)
        command = f"cd {repo_path} && sudo git fetch --all && sudo git reset --hard origin/master && sudo git checkout {branch} && sudo git pull"
        return self._ssh_command(command)

    def run_api_automation(self):
        test_path = shlex.quote(self.test_path)
        command = f"cd {test_path} && sudo git checkout -f master && sudo git pull && python3 api_testing.py"
        result = self._ssh_command(command)
        failed = []
        for index, chunk in enumerate(result.get("stdout", "").split("----------"), start=1):
            if re.search("FAILED", chunk):
                failed.append(f"{index}{chunk}")
        return {**result, "failed_count": len(failed), "failed_api": failed}

    def run_branch_api_tests(self, branch_name="master"):
        branch_result = self.change_branch(branch_name)
        test_result = self.run_api_automation()
        reset_result = self.change_branch("master")
        return {"branch": branch_name, "change_branch": branch_result, "api_testing": test_result, "reset_branch": reset_result}