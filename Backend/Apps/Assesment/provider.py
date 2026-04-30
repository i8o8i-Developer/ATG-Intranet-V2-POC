from django.conf import settings

import requests


class ExternalAssessmentProviderClient:
    def __init__(self, base_url=None, timeout=15, session=None):
        self.base_url = (base_url or getattr(settings, "ASSESSMENT_PROVIDER_BASE_URL", "https://assessmntbackend.atg.world")).rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def generate_link(self, email, assessment_id):
        response = self.session.post(
            f"{self.base_url}/users/generate-links",
            json={"email": email, "assesment_id": assessment_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def send_link(self, payload):
        response = self.session.post(f"{self.base_url}/users/send-links", json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def fetch_status(self, external_user_id, assessment_id, assignment_id=None):
        response = self.session.get(
            f"{self.base_url}/users/user",
            params={"user_id": external_user_id, "assessment_id": assessment_id, "id": assignment_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
