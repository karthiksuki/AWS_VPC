"""
vpc_manager/utils/helpers.py — Reusable helper functions.
"""
from config.settings import VPCConfig


def build_tags(name: str, extra: dict | None = None) -> list[dict]:
    """
    Build a standard AWS TagSpecification-compatible tag list.

    Args:
        name:  Value for the 'Name' tag.
        extra: Optional dict of additional {key: value} pairs.

    Returns:
        List of {"Key": ..., "Value": ...} dicts.
    """
    tags = [
        {"Key": "Name",        "Value": name},
        {"Key": "Environment", "Value": VPCConfig.ENVIRONMENT},
        {"Key": "Project",     "Value": VPCConfig.PROJECT},
        {"Key": "ManagedBy",   "Value": "vpc-manager-python"},
    ]
    if extra:
        tags.extend({"Key": k, "Value": v} for k, v in extra.items())
    return tags


def tag_spec(resource_type: str, name: str, extra: dict | None = None) -> list[dict]:
    """
    Build a TagSpecification block for use in create_* API calls.

    Example:
        ec2.create_vpc(CidrBlock="10.0.0.0/16",
                       TagSpecifications=tag_spec("vpc", "my-vpc"))
    """
    return [{"ResourceType": resource_type, "Tags": build_tags(name, extra)}]


def paginate(client, method: str, key: str, **kwargs) -> list:
    """
    Generic paginator wrapper.

    Args:
        client: boto3 EC2 client.
        method: Paginator method name (e.g. 'describe_vpcs').
        key:    Top-level key to collect from each page (e.g. 'Vpcs').

    Returns:
        Flat list of all items across pages.
    """
    paginator = client.get_paginator(method)
    results = []
    for page in paginator.paginate(**kwargs):
        results.extend(page.get(key, []))
    return results


def get_tag(resource: dict, key: str, default: str = "") -> str:
    """Extract a tag value from an AWS resource dict by key."""
    for tag in resource.get("Tags", []):
        if tag["Key"] == key:
            return tag["Value"]
    return default