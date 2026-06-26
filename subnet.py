"""
vpc_manager/core/subnet.py — Subnet create / describe / delete operations.
"""
from botocore.exceptions import ClientError
from vpc_manager.utils import get_ec2_client, get_logger, tag_spec, paginate

logger = get_logger(__name__)


class SubnetManager:
    """Handles subnet-level AWS operations within a VPC."""

    def __init__(self, client=None):
        self.client = client or get_ec2_client()

    # ------------------------------------------------------------------ #
    #  Create                                                               #
    # ------------------------------------------------------------------ #
    def create_subnet(
        self,
        vpc_id: str,
        cidr: str,
        az: str,
        name: str,
        public: bool = False,
    ) -> dict:
        """
        Create a subnet inside the given VPC.

        Args:
            vpc_id:  Parent VPC ID.
            cidr:    CIDR block for the subnet (e.g. '10.0.1.0/24').
            az:      Availability zone (e.g. 'us-east-1a').
            name:    Friendly name; stored as the 'Name' tag.
            public:  If True, enables auto-assign public IP on launch.

        Returns:
            The created Subnet dict from AWS.
        """
        logger.info("Creating subnet '%s' (%s) in AZ %s", name, cidr, az)
        try:
            response = self.client.create_subnet(
                VpcId=vpc_id,
                CidrBlock=cidr,
                AvailabilityZone=az,
                TagSpecifications=tag_spec("subnet", name, {"Tier": "public" if public else "private"}),
            )
            subnet = response["Subnet"]
            subnet_id = subnet["SubnetId"]

            if public:
                self.client.modify_subnet_attribute(
                    SubnetId=subnet_id,
                    MapPublicIpOnLaunch={"Value": True},
                )

            logger.info("[green]Subnet created:[/green] %s (%s)", subnet_id, name)
            return subnet

        except ClientError as exc:
            logger.error("Failed to create subnet %s: %s", name, exc)
            raise

    def create_public_subnets(self, vpc_id: str, subnet_configs: list[dict]) -> list[dict]:
        """Create multiple public subnets from a list of config dicts."""
        return [
            self.create_subnet(vpc_id, s["cidr"], s["az"], s["name"], public=True)
            for s in subnet_configs
        ]

    def create_private_subnets(self, vpc_id: str, subnet_configs: list[dict]) -> list[dict]:
        """Create multiple private subnets from a list of config dicts."""
        return [
            self.create_subnet(vpc_id, s["cidr"], s["az"], s["name"], public=False)
            for s in subnet_configs
        ]

    # ------------------------------------------------------------------ #
    #  Read / Describe                                                      #
    # ------------------------------------------------------------------ #
    def list_subnets(self, vpc_id: str) -> list[dict]:
        """List all subnets belonging to the given VPC."""
        subnets = paginate(
            self.client,
            "describe_subnets",
            "Subnets",
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}],
        )
        logger.info("Found %d subnet(s) in VPC %s.", len(subnets), vpc_id)
        return subnets

    def get_subnet_by_id(self, subnet_id: str) -> dict | None:
        """Fetch a single subnet by its ID."""
        subnets = paginate(
            self.client,
            "describe_subnets",
            "Subnets",
            Filters=[{"Name": "subnet-id", "Values": [subnet_id]}],
        )
        return subnets[0] if subnets else None

    # ------------------------------------------------------------------ #
    #  Delete                                                               #
    # ------------------------------------------------------------------ #
    def delete_subnet(self, subnet_id: str) -> bool:
        """Delete a subnet by ID."""
        logger.info("Deleting subnet: %s", subnet_id)
        try:
            self.client.delete_subnet(SubnetId=subnet_id)
            logger.info("[green]Subnet deleted:[/green] %s", subnet_id)
            return True
        except ClientError as exc:
            logger.error("Failed to delete subnet %s: %s", subnet_id, exc)
            raise

    def delete_all_subnets(self, vpc_id: str) -> int:
        """Delete every subnet in the given VPC. Returns count deleted."""
        subnets = self.list_subnets(vpc_id)
        for subnet in subnets:
            self.delete_subnet(subnet["SubnetId"])
        return len(subnets)