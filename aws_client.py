"""
vpc_manager/utils/aws_client.py — Boto3 client / resource factory.
Returns a shared EC2 client or resource, configured from AWSConfig.
"""
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from config.settings import AWSConfig
from .logger import get_logger

logger = get_logger(__name__)


def get_ec2_client():
    """Return a boto3 EC2 *client* (low-level, full API access)."""
    try:
        kwargs = {"region_name": AWSConfig.REGION}
        if AWSConfig.ACCESS_KEY_ID:
            kwargs["aws_access_key_id"] = AWSConfig.ACCESS_KEY_ID
            kwargs["aws_secret_access_key"] = AWSConfig.SECRET_ACCESS_KEY
        if AWSConfig.SESSION_TOKEN:
            kwargs["aws_session_token"] = AWSConfig.SESSION_TOKEN

        client = boto3.client("ec2", **kwargs)
        # Lightweight connectivity check
        client.describe_availability_zones()
        logger.info("EC2 client initialised — region: %s", AWSConfig.REGION)
        return client

    except NoCredentialsError:
        logger.error("AWS credentials not found. Set env vars or configure ~/.aws/credentials.")
        raise
    except ClientError as exc:
        logger.error("AWS ClientError during client init: %s", exc)
        raise


def get_ec2_resource():
    """Return a boto3 EC2 *resource* (higher-level OO interface)."""
    kwargs = {"region_name": AWSConfig.REGION}
    if AWSConfig.ACCESS_KEY_ID:
        kwargs["aws_access_key_id"] = AWSConfig.ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = AWSConfig.SECRET_ACCESS_KEY
    if AWSConfig.SESSION_TOKEN:
        kwargs["aws_session_token"] = AWSConfig.SESSION_TOKEN
    return boto3.resource("ec2", **kwargs)