"""
config/settings.py — Centralised configuration loader.
Reads from environment variables or a .env file via python-dotenv.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class AWSConfig:
    """AWS connection settings."""
    REGION: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    ACCESS_KEY_ID: str | None = os.getenv("AWS_ACCESS_KEY_ID")
    SECRET_ACCESS_KEY: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")
    SESSION_TOKEN: str | None = os.getenv("AWS_SESSION_TOKEN")


class VPCConfig:
    """Default VPC topology settings."""
    VPC_CIDR: str = os.getenv("VPC_CIDR", "10.0.0.0/16")
    VPC_NAME: str = os.getenv("VPC_NAME", "my-vpc")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")
    PROJECT: str = os.getenv("PROJECT", "vpc-manager")

    # Subnet CIDRs — extend as needed
    PUBLIC_SUBNETS: list[dict] = [
        {"cidr": "10.0.1.0/24", "az": "us-east-1a", "name": "public-subnet-1a"},
        {"cidr": "10.0.2.0/24", "az": "us-east-1b", "name": "public-subnet-1b"},
    ]
    PRIVATE_SUBNETS: list[dict] = [
        {"cidr": "10.0.10.0/24", "az": "us-east-1a", "name": "private-subnet-1a"},
        {"cidr": "10.0.11.0/24", "az": "us-east-1b", "name": "private-subnet-1b"},
    ]

    # Security group defaults
    DEFAULT_INGRESS_RULES: list[dict] = [
        {
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22,
            "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SSH"}],
        },
        {
            "IpProtocol": "tcp",
            "FromPort": 80,
            "ToPort": 80,
            "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "HTTP"}],
        },
        {
            "IpProtocol": "tcp",
            "FromPort": 443,
            "ToPort": 443,
            "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "HTTPS"}],
        },
    ]