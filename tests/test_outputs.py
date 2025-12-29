"""Tests for multi-region AWS infrastructure deployment and failover validation."""

import json
import subprocess
from pathlib import Path
from datetime import datetime

# Canary string for anti-cheating
CANARY_STRING = "TERMINUS_INFRA_MULTI_REGION_42XZ"


def test_terraform_directory_exists():
    """Verify that the Terraform directory was created."""
    terraform_dir = Path("/app/terraform")
    assert terraform_dir.exists(), "Terraform directory does not exist at /app/terraform"
    assert terraform_dir.is_dir(), "/app/terraform is not a directory"


def test_terraform_required_files_exist():
    """Verify all required Terraform configuration files exist."""
    required_files = [
        "/app/terraform/main.tf",
        "/app/terraform/variables.tf",
        "/app/terraform/outputs.tf",
        "/app/terraform/providers.tf"
    ]

    for file_path in required_files:
        path = Path(file_path)
        assert path.exists(), f"Required Terraform file {file_path} does not exist"
        assert path.is_file(), f"{file_path} is not a file"
        assert path.stat().st_size > 0, f"{file_path} is empty"


def test_terraform_providers_configuration():
    """Verify Terraform providers are configured for multi-region deployment."""
    providers_path = Path("/app/terraform/providers.tf")
    content = providers_path.read_text()

    # Check for dual provider configuration
    assert 'provider "aws"' in content, "AWS provider not configured"
    assert "us-east-1" in content, "Primary region (us-east-1) not configured"
    assert "us-west-2" in content, "Secondary region (us-west-2) not configured"
    assert "localhost:4566" in content or "localstack" in content.lower(), \
        "LocalStack endpoints not configured"


def test_terraform_main_has_required_resources():
    """Verify main.tf contains all required infrastructure resources."""
    main_path = Path("/app/terraform/main.tf")
    content = main_path.read_text()

    required_resources = [
        "aws_vpc",
        "aws_subnet",
        "aws_internet_gateway",
        "aws_nat_gateway",
        "aws_lb",  # Application Load Balancer
        "aws_ecs_cluster",
        "aws_ecs_service",
        "aws_rds",
        "aws_s3_bucket",
        "aws_route53",
        "aws_iam_role",
        "aws_cloudwatch",
        "aws_sns_topic"
    ]

    for resource_type in required_resources:
        assert resource_type in content, \
            f"Required resource type '{resource_type}' not found in main.tf"


def test_terraform_outputs_configured():
    """Verify Terraform outputs are properly configured."""
    outputs_path = Path("/app/terraform/outputs.tf")
    content = outputs_path.read_text()

    required_outputs = [
        "route53_domain_name",
        "primary_alb_dns",
        "secondary_alb_dns",
        "primary_s3_bucket",
        "secondary_s3_bucket",
        "aurora_global_cluster_id"
    ]

    for output_name in required_outputs:
        assert output_name in content, \
            f"Required output '{output_name}' not found in outputs.tf"


def test_terraform_state_exists():
    """Verify Terraform was initialized and applied successfully."""
    state_file = Path("/app/terraform/terraform.tfstate")
    assert state_file.exists(), "Terraform state file does not exist - terraform may not have been applied"


def test_failover_validation_json_exists():
    """Verify failover validation results file was created."""
    results_file = Path("/app/results/failover_validation.json")
    assert results_file.exists(), \
        "Failover validation file does not exist at /app/results/failover_validation.json"


def test_failover_validation_json_structure():
    """Verify failover validation JSON has the correct structure."""
    results_file = Path("/app/results/failover_validation.json")

    with open(results_file, 'r') as f:
        data = json.load(f)

    required_fields = [
        "failover_time_seconds",
        "primary_region_status",
        "secondary_region_status",
        "route53_active_endpoint",
        "rds_promoted",
        "timestamp",
        "canary_string"
    ]

    for field in required_fields:
        assert field in data, f"Required field '{field}' missing from failover validation JSON"


def test_failover_time_within_limit():
    """Verify failover completed within 60 seconds."""
    results_file = Path("/app/results/failover_validation.json")

    with open(results_file, 'r') as f:
        data = json.load(f)

    failover_time = data["failover_time_seconds"]
    assert isinstance(failover_time, (int, float)), \
        f"failover_time_seconds must be a number, got {type(failover_time)}"
    assert 0 <= failover_time <= 60, \
        f"Failover time {failover_time}s exceeds 60-second requirement"


def test_primary_region_marked_down():
    """Verify primary region status is correctly marked as DOWN."""
    results_file = Path("/app/results/failover_validation.json")

    with open(results_file, 'r') as f:
        data = json.load(f)

    assert data["primary_region_status"] == "DOWN", \
        f"Primary region should be DOWN, got {data['primary_region_status']}"


def test_secondary_region_marked_up():
    """Verify secondary region status is correctly marked as UP."""
    results_file = Path("/app/results/failover_validation.json")

    with open(results_file, 'r') as f:
        data = json.load(f)

    assert data["secondary_region_status"] == "UP", \
        f"Secondary region should be UP, got {data['secondary_region_status']}"


def test_route53_active_endpoint_correct():
    """Verify Route53 active endpoint switched to secondary region."""
    results_file = Path("/app/results/failover_validation.json")

    with open(results_file, 'r') as f:
        data = json.load(f)

    assert data["route53_active_endpoint"] == "us-west-2", \
        f"Active endpoint should be us-west-2, got {data['route53_active_endpoint']}"


def test_rds_promoted_to_primary():
    """Verify RDS secondary cluster was promoted to primary."""
    results_file = Path("/app/results/failover_validation.json")

    with open(results_file, 'r') as f:
        data = json.load(f)

    assert data["rds_promoted"] is True, \
        "RDS secondary cluster should be promoted to primary"


def test_timestamp_valid_format():
    """Verify timestamp is in valid ISO 8601 format."""
    results_file = Path("/app/results/failover_validation.json")

    with open(results_file, 'r') as f:
        data = json.load(f)

    timestamp = data["timestamp"]

    # Try to parse as ISO 8601
    try:
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except ValueError:
        assert False, f"Timestamp '{timestamp}' is not in valid ISO 8601 format"


def test_canary_string_present():
    """Verify canary string is present in failover validation (anti-cheating measure)."""
    results_file = Path("/app/results/failover_validation.json")

    with open(results_file, 'r') as f:
        data = json.load(f)

    assert data["canary_string"] == CANARY_STRING, \
        f"Canary string mismatch. Expected '{CANARY_STRING}', got '{data.get('canary_string')}'"


def test_simulate_failover_script_exists():
    """Verify failover simulation script was created."""
    script_path = Path("/app/scripts/simulate_failover.sh")
    assert script_path.exists(), \
        "Failover simulation script does not exist at /app/scripts/simulate_failover.sh"
    assert script_path.is_file(), "/app/scripts/simulate_failover.sh is not a file"


def test_simulate_failover_script_executable():
    """Verify failover simulation script has execute permissions."""
    script_path = Path("/app/scripts/simulate_failover.sh")
    import os
    assert os.access(script_path, os.X_OK), \
        "Failover simulation script is not executable"


def test_vpc_cidr_blocks_correct():
    """Verify VPC CIDR blocks are correctly configured in Terraform."""
    # Check if terraform output command works
    try:
        # This will work if terraform was applied successfully
        result = subprocess.run(
            ["terraform", "show", "-json"],
            cwd="/app/terraform",
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            state = json.loads(result.stdout)
            # Look for VPC resources with correct CIDR blocks
            found_primary = False
            found_secondary = False

            if "values" in state and "root_module" in state["values"]:
                resources = state["values"]["root_module"].get("resources", [])
                for resource in resources:
                    if resource.get("type") == "aws_vpc":
                        cidr = resource.get("values", {}).get("cidr_block")
                        if cidr == "10.0.0.0/16":
                            found_primary = True
                        elif cidr == "10.1.0.0/16":
                            found_secondary = True

            assert found_primary or found_secondary, \
                "VPC CIDR blocks not configured correctly (expected 10.0.0.0/16 and 10.1.0.0/16)"
    except Exception:
        # If terraform show fails, check the configuration files directly
        main_path = Path("/app/terraform/main.tf")
        content = main_path.read_text()
        assert "10.0.0.0/16" in content, "Primary VPC CIDR 10.0.0.0/16 not found"
        assert "10.1.0.0/16" in content, "Secondary VPC CIDR 10.1.0.0/16 not found"


def test_s3_cross_region_replication_configured():
    """Verify S3 cross-region replication is configured."""
    main_path = Path("/app/terraform/main.tf")
    content = main_path.read_text()

    assert "aws_s3_bucket_replication" in content or "replication_configuration" in content, \
        "S3 cross-region replication not configured in Terraform"


def test_route53_latency_routing_configured():
    """Verify Route53 latency-based routing policy is configured."""
    main_path = Path("/app/terraform/main.tf")
    content = main_path.read_text()

    assert "aws_route53_record" in content, "Route53 records not configured"
    assert "latency_routing_policy" in content or "latency" in content, \
        "Route53 latency-based routing not configured"


def test_cloudwatch_dashboard_configured():
    """Verify CloudWatch dashboard is configured for multi-region monitoring."""
    main_path = Path("/app/terraform/main.tf")
    content = main_path.read_text()

    assert "aws_cloudwatch_dashboard" in content, \
        "CloudWatch dashboard not configured in Terraform"


def test_ecs_service_configuration():
    """Verify ECS Fargate services are configured."""
    main_path = Path("/app/terraform/main.tf")
    content = main_path.read_text()

    assert "aws_ecs_cluster" in content, "ECS cluster not configured"
    assert "aws_ecs_service" in content, "ECS service not configured"
    assert "FARGATE" in content or "fargate" in content.lower(), \
        "ECS Fargate launch type not configured"
    assert "nginx" in content.lower(), "nginx container not configured"


def test_iam_roles_configured():
    """Verify IAM roles are configured with appropriate permissions."""
    main_path = Path("/app/terraform/main.tf")
    content = main_path.read_text()

    assert "aws_iam_role" in content, "IAM roles not configured"
    assert "aws_iam_role_policy" in content or "aws_iam_policy" in content, \
        "IAM policies not configured"


def test_security_groups_configured():
    """Verify security groups are configured for ALB and ECS."""
    # Check in main.tf or module files
    terraform_dir = Path("/app/terraform")
    found_sg = False

    for file_path in terraform_dir.rglob("*.tf"):
        content = file_path.read_text()
        if "aws_security_group" in content:
            found_sg = True
            break

    assert found_sg, "Security groups not configured in Terraform files"


def test_aurora_global_cluster_configured():
    """Verify RDS Aurora global cluster is configured."""
    main_path = Path("/app/terraform/main.tf")
    content = main_path.read_text()

    assert "aws_rds_global_cluster" in content or "global_cluster_identifier" in content, \
        "RDS Aurora global cluster not configured"
    assert "aurora-postgresql" in content or "postgres" in content.lower(), \
        "Aurora PostgreSQL engine not configured"
