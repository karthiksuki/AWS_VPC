"""
vpc_manager/core/vpc.py — VPC create / describe / delete operations.
"""
from botocore.exceptions import ClientError
from vpc_manager.utils import get_ec2_client, get_logger, tag_spec, paginate, get_tag
from config.settings import VPCConfig

logger = get_logger(__name__)


class VPCManager:
    """Handles all VPC-level AWS operations."""

    def __init__(self, client=None):
        self.client = client or get_ec2_client()

    # ------------------------------------------------------------------ #
    #  Create                                                               #
    # ------------------------------------------------------------------ #
    def create_vpc(
        self,
        cidr: str = VPCConfig.VPC_CIDR,
        name: str = VPCConfig.VPC_NAME,
        enable_dns_support: bool = True,
        enable_dns_hostnames: bool = True,
    ) -> dict:
        """
        Create a new VPC with DNS support and hostnames enabled.

        Returns:
            The created VPC dict from AWS.
        """
        logger.info("Creating VPC — CIDR: %s  Name: %s", cidr, name)
        try:
            response = self.client.create_vpc(
                CidrBlock=cidr,
                TagSpecifications=tag_spec("vpc", name),
            )
            vpc = response["Vpc"]
            vpc_id = vpc["VpcId"]

            # Enable DNS features
            self.client.modify_vpc_attribute(
                VpcId=vpc_id,
                EnableDnsSupport={"Value": enable_dns_support},
            )
            self.client.modify_vpc_attribute(
                VpcId=vpc_id,
                EnableDnsHostnames={"Value": enable_dns_hostnames},
            )

            logger.info("[green]VPC created:[/green] %s", vpc_id)
            return vpc

        except ClientError as exc:
            logger.error("Failed to create VPC: %s", exc)
            raise

    # ------------------------------------------------------------------ #
    #  Read / Describe                                                      #
    # ------------------------------------------------------------------ #
    def get_vpc_by_id(self, vpc_id: str) -> dict | None:
        """Fetch a single VPC by its ID."""
        vpcs = paginate(
            self.client,
            "describe_vpcs",
            "Vpcs",
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}],
        )
        return vpcs[0] if vpcs else None

    def get_vpc_by_name(self, name: str) -> dict | None:
        """Fetch the first VPC whose 'Name' tag matches."""
        vpcs = paginate(
            self.client,
            "describe_vpcs",
            "Vpcs",
            Filters=[{"Name": "tag:Name", "Values": [name]}],
        )
        return vpcs[0] if vpcs else None

    def list_vpcs(self) -> list[dict]:
        """Return all VPCs in the current region."""
        vpcs = paginate(self.client, "describe_vpcs", "Vpcs")
        logger.info("Found %d VPC(s) in region.", len(vpcs))
        return vpcs

    # ------------------------------------------------------------------ #
    #  Delete                                                               #
    # ------------------------------------------------------------------ #
    def delete_vpc(self, vpc_id: str) -> bool:
        """
        Delete a VPC. AWS requires all dependencies (subnets, IGW, etc.)
        to be detached / deleted first.
        """
        logger.info("Deleting VPC: %s", vpc_id)
        try:
            self.client.delete_vpc(VpcId=vpc_id)
            logger.info("[green]VPC deleted:[/green] %s", vpc_id)
            return True
        except ClientError as exc:
            logger.error("Failed to delete VPC %s: %s", vpc_id, exc)
            raise

    # ------------------------------------------------------------------ #
    #  Helpers                                                              #
    # ------------------------------------------------------------------ #
    def print_summary(self, vpc: dict) -> None:
        """Pretty-print key VPC attributes to the console."""
        logger.info(
            "VPC Summary — ID: %s | CIDR: %s | State: %s | Name: %s",
            vpc.get("VpcId"),
            vpc.get("CidrBlock"),
            vpc.get("State"),
            get_tag(vpc, "Name"),
        )