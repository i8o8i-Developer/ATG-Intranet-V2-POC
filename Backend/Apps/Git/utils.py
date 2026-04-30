def name_formatter(org, name):
    return f"{org} {name}".replace(" ", "_")


def build_full_name(organization, repository_name):
    return f"{organization}/{repository_name}" if organization else repository_name


def normalize_repository_payload(payload):
    organization = payload.get("organization") or payload.get("owner") or payload.get("org") or "atg"
    repository_name = payload.get("repository_name") or payload.get("name") or payload.get("repository") or ""
    return {
        "organization": organization,
        "repository_name": repository_name,
        "default_branch": payload.get("default_branch", ""),
        "latest_commit_sha": payload.get("latest_commit_sha", ""),
        "external_id": str(payload.get("external_id") or payload.get("id") or ""),
        "external_url": payload.get("external_url") or payload.get("html_url") or payload.get("url") or "",
        "metadata": payload.get("metadata", {}),
    }