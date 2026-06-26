"""
vpc_manager/core/internet_gateway.py — IGW attach / detach / delete operations.
"""
from botocore.exceptions import ClientError
from vpc_manager.utils import get_ec2_client, get_logger, tag_spec, paginate

logger = get_logger(__name__)


class InternetGatewayManager:
    """Handles Internet Gateway operations."""

    def __init__(self, client=None):
        self.client = client or get_ec2_client()

    # ------------------------------------------------------------------ #
    #  Create & Attach                                                      #
    # ------------------------------------------------------------------ #
    def create_and_attach(self, vpc_id: str, name: str) -> dict:
        """
        Create an Internet Gateway and attach it to the given VPC.

        Returns:
            The created InternetGateway dict.
        """
        logger.info("Creating Internet Gateway '%s' for VPC %s", name, vpc_id)
        try:
            response = self.client.create_internet_gateway(
                TagSpecifications=tag_spec("internet-gateway", name),
            )
            igw = response["InternetGateway"]
            igw_id = igw["InternetGatewayId"]

            self.client.attach_internet_gateway(
                InternetGatewayId=igw_id,
                VpcId=vpc_id,
            )
            logger.info("[green]IGW created and attached:[/green] %s → %s", igw_id, vpc_id)
            return igw

        except ClientError as exc:
            logger.error("Failed to create/attach IGW: %s", exc)
            raise

    # ------------------------------------------------------------------ #
    #  Read / Describe                                                      #
    # ------------------------------------------------------------------ #
    def get_igw_for_vpc(self, vpc_id: str) -> dict | None:
        """Return the Internet Gateway attached to the given VPC, or None."""
        igws = paginate(
            self.client,
            "describe_internet_gateways",
            "InternetGateways",
            Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}],
        )
        return igws[0] if igws else None

    # ------------------------------------------------------------------ #
    #  Detach & Delete                                                      #
    # ------------------------------------------------------------------ #
    def detach_and_delete(self, igw_id: str, vpc_id: str) -> bool:
        """Detach an IGW from its VPC and then delete it."""
        logger.info("Detaching IGW %s from VPC %s", igw_id, vpc_id)
        try:
            self.client.detach_internet_gateway(
                InternetGatewayId=igw_id,
                VpcId=vpc_id,
            )
            self.client.delete_internet_gateway(InternetGatewayId=igw_id)
            logger.info("[green]IGW detached and deleted:[/green] %s", igw_id)
            return True
        except ClientError as exc:
            logger.error("Failed to detach/delete IGW %s: %s", igw_id, exc)
            raise

    def cleanup_for_vpc(self, vpc_id: str) -> bool:
        """Find and clean up any IGW attached to the given VPC."""
        igw = self.get_igw_for_vpc(vpc_id)
        if not igw:
            logger.info("No IGW found for VPC %s — skipping.", vpc_id)
            return False
        return self.detach_and_delete(igw["InternetGatewayId"], vpc_id)