"""The existing v1 garden allowlist is deny-by-default, including empty lists."""


def permits_publication(policy: dict, *, kind: str, domains: list[str], topics: list[str]) -> bool:
    try:
        if (policy["default_action"] != "deny" or "public" not in policy["allowed_visibilities"]
                or "approved" not in policy["required_review_states"] or policy["raw_sources"] != "exclude"):
            return False
        for field, values in (("kinds", [kind]), ("domains", domains), ("topics", topics)):
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                return False
            if not set(values) <= set(policy["allow"][field]):
                return False
        return True
    except (KeyError, TypeError):
        return False
