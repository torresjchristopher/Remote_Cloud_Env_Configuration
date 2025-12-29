# Multi-Region Active-Active AWS Infrastructure with Failover Validation

Deploy a production-grade, multi-region active-active AWS infrastructure using Terraform with automatic failover capabilities.

## Objective

Use Terraform to provision a complete multi-region AWS environment, then simulate a regional outage and validate that failover occurs within 60 seconds with zero manual intervention.

## Requirements

### 1. Infrastructure Components

Deploy the following resources across **two regions** (us-east-1 and us-west-2):

#### Per-Region Resources

- **VPC** with CIDR blocks:
  - us-east-1: 10.0.0.0/16
  - us-west-2: 10.1.0.0/16
- **Subnets**: 2 public subnets and 2 private subnets per VPC (across 2 AZs)
- **Internet Gateway** and **NAT Gateways** for each VPC
- **Application Load Balancer** (internet-facing) in public subnets
- **ECS Fargate Cluster** with a service running nginx containers (2 tasks minimum)
- **Target Groups** connecting ALB to ECS services
- **Security Groups** with proper ingress/egress rules
- **S3 Bucket** for application data with versioning enabled

#### Global Resources

- **RDS Aurora Global Database** with primary cluster in us-east-1 and secondary cluster in us-west-2
- **S3 Cross-Region Replication** from us-east-1 bucket to us-west-2 bucket
- **Route 53 Hosted Zone** with latency-based routing policy pointing to both ALBs
- **IAM Roles** for ECS tasks with S3 and RDS access permissions
- **CloudWatch Dashboard** displaying metrics from both regions (ALB requests, ECS CPU/memory, RDS connections)
- **SNS Topic** for CloudWatch alarms with email subscription endpoint
- **CloudWatch Alarms** for unhealthy targets and high error rates

### 2. Terraform Structure

Your Terraform code must be organized in `/app/terraform/`:

```text
/app/terraform/
├── main.tf           # Root module
├── variables.tf      # Input variables
├── outputs.tf        # Output values (ALB URLs, Route53 domain)
├── providers.tf      # AWS provider configuration
└── modules/          # Reusable modules (optional but recommended)
```

### 3. Configuration Requirements

- Use **Terraform version 1.5+**
- Pin all provider versions explicitly
- Use variables for all region-specific values
- Output the following values:
  - `route53_domain_name` - The Route 53 domain name
  - `primary_alb_dns` - us-east-1 ALB DNS name
  - `secondary_alb_dns` - us-west-2 ALB DNS name
  - `primary_s3_bucket` - us-east-1 S3 bucket name
  - `secondary_s3_bucket` - us-west-2 S3 bucket name
  - `aurora_global_cluster_id` - Aurora global cluster identifier

### 4. Failover Simulation

After successful deployment, you must:

1. **Simulate a regional outage** in us-east-1 by:
   - Stopping all ECS tasks in the primary region
   - Setting the primary ALB target group to unhealthy
   - Disabling the primary RDS cluster

2. **Validate automatic failover** by verifying:
   - Route 53 automatically routes traffic to us-west-2 ALB
   - us-west-2 ECS services handle incoming requests
   - RDS Aurora promotes secondary cluster to primary
   - Failover completes within **60 seconds** of outage detection

3. **Write failover results** to `/app/results/failover_validation.json` with this exact structure:

```json
{
  "failover_time_seconds": <float>,
  "primary_region_status": "DOWN",
  "secondary_region_status": "UP",
  "route53_active_endpoint": "us-west-2",
  "rds_promoted": true,
  "timestamp": "<ISO 8601 timestamp>",
  "canary_string": "TERMINUS_INFRA_MULTI_REGION_42XZ"
}
```

### 5. Deployment Steps

1. Initialize Terraform: `cd /app/terraform && terraform init`
2. Validate configuration: `terraform validate`
3. Plan deployment: `terraform plan -out=tfplan`
4. Apply infrastructure: `terraform apply tfplan`
5. Run failover simulation script: `/app/scripts/simulate_failover.sh`
6. Generate validation results: Write to `/app/results/failover_validation.json`

### 6. Constraints

- All resources must use **LocalStack** (not real AWS) via LocalStack endpoints
- ECS tasks must run nginx:alpine image
- RDS Aurora must use PostgreSQL engine (version 14.6)
- S3 buckets must have server-side encryption enabled (AES256)
- All CloudWatch alarms must have evaluation period ≤ 60 seconds
- Route 53 health checks must have check interval ≤ 10 seconds
- IAM roles must follow least-privilege principle
- No hardcoded credentials (use IAM roles only)

### 7. Validation Criteria

Your solution will be tested for:

- ✅ Terraform applies successfully without errors
- ✅ All required resources exist in both regions
- ✅ ECS services are running and healthy
- ✅ Route 53 resolves to healthy ALB endpoints
- ✅ S3 replication is configured correctly
- ✅ RDS global cluster has primary and secondary
- ✅ CloudWatch dashboard displays multi-region metrics
- ✅ Failover completes within 60 seconds
- ✅ Failover validation JSON contains canary string
- ✅ Secondary region handles traffic after failover

## Files

- **Input**: None (you create all infrastructure)
- **Output**:
  - `/app/terraform/` - All Terraform code
  - `/app/results/failover_validation.json` - Failover test results
  - `/app/scripts/simulate_failover.sh` - Failover simulation script

## Notes

- LocalStack must be running at `http://localhost:4566`
- Use `awslocal` CLI or configure AWS SDK endpoints to point to LocalStack
- Document any assumptions in `/app/README.md`
- Ensure idempotency - running terraform apply twice should not cause errors
