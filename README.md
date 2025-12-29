# Multi-Region Active-Active AWS Infrastructure Task

## Overview

This is a **hard** difficulty infrastructure task that challenges LLM agents to deploy a production-grade, multi-region active-active AWS environment using Terraform, then validate automatic failover capabilities.

## Task Difficulty

**Target Pass Rate:** <40% (Hard)

### Why This Task is Hard

1. **Multi-Region Complexity**: Requires orchestrating resources across two AWS regions (us-east-1 and us-west-2) with proper cross-region dependencies
2. **Deep Terraform Knowledge**: Tests understanding of:
   - Provider aliases for multi-region deployment
   - Module architecture and resource dependencies
   - Terraform state management
   - Output configurations
3. **AWS Service Integration**: Requires configuring and integrating:
   - VPC networking (subnets, IGW, NAT gateways, route tables)
   - Application Load Balancers with health checks
   - ECS Fargate clusters and services
   - RDS Aurora Global Database
   - S3 cross-region replication
   - Route 53 latency-based routing
   - IAM roles and policies
   - CloudWatch dashboards and alarms
   - SNS topics for alerting
4. **Failover Validation**: Must programmatically simulate regional outage and validate <60s failover
5. **LocalStack Configuration**: All services must use LocalStack endpoints (not real AWS)

## Task Components

### Infrastructure Requirements

- **Dual-Region VPCs** with specific CIDR blocks (10.0.0.0/16 and 10.1.0.0/16)
- **Per-Region Resources**:
  - 2 public + 2 private subnets across 2 AZs
  - Internet Gateway and NAT Gateways
  - Application Load Balancer (internet-facing)
  - ECS Fargate cluster with nginx containers (2+ tasks)
  - S3 bucket with versioning and encryption
- **Global Resources**:
  - RDS Aurora Global Database (PostgreSQL 14.6)
  - S3 cross-region replication
  - Route 53 hosted zone with latency-based routing
  - IAM roles with least-privilege permissions
  - CloudWatch dashboard showing multi-region metrics
  - SNS topic for alarms

### Failover Simulation

After deployment, the agent must:
1. Simulate a regional outage in us-east-1 by:
   - Stopping all ECS tasks
   - Marking ALB targets as unhealthy
   - Disabling the RDS cluster
2. Validate that failover completes within 60 seconds
3. Generate a JSON validation file with:
   - Failover time
   - Region status (primary=DOWN, secondary=UP)
   - Active Route 53 endpoint (us-west-2)
   - RDS promotion status
   - ISO 8601 timestamp
   - Canary string for anti-cheating

## Testing Strategy

### Test Coverage

The test suite (27 tests) verifies:

1. **File Structure** (4 tests)
   - Terraform directory exists
   - Required files present (main.tf, variables.tf, outputs.tf, providers.tf)
   - Files are not empty

2. **Configuration Correctness** (8 tests)
   - Dual-region provider configuration
   - All required AWS resources defined
   - Correct outputs configured
   - VPC CIDR blocks match specification

3. **Service-Specific Tests** (8 tests)
   - S3 cross-region replication configured
   - Route 53 latency routing enabled
   - CloudWatch dashboard created
   - ECS Fargate with nginx
   - IAM roles and policies
   - Security groups
   - Aurora global cluster with PostgreSQL

4. **Failover Validation** (7 tests)
   - JSON file exists with correct structure
   - Failover time ≤60 seconds
   - Region statuses correct (PRIMARY=DOWN, SECONDARY=UP)
   - Route 53 switched to us-west-2
   - RDS promoted
   - Valid ISO 8601 timestamp
   - **Canary string present** (anti-cheating)

### Anti-Cheating Measures

- **Canary String**: `TERMINUS_INFRA_MULTI_REGION_42XZ` must appear in failover validation JSON
- **Behavioral Testing**: Tests check for actual Terraform resources, not just hardcoded outputs
- **Multi-File Validation**: Tests search across all `.tf` files to prevent hiding resources
- **Execution Verification**: Checks for `terraform.tfstate` file proving actual apply

## Expected Agent Challenges

Agents are likely to struggle with:

1. **Provider Alias Configuration**: Correctly setting up dual AWS providers with LocalStack endpoints
2. **Resource Dependencies**: Managing cross-region resource dependencies (e.g., RDS global cluster)
3. **Module Architecture**: Deciding whether to use modules vs. flat structure
4. **LocalStack Limitations**: Some AWS features may behave differently in LocalStack
5. **Failover Timing**: Achieving <60s failover with proper validation
6. **IAM Complexity**: Configuring roles for ECS tasks, S3 replication, etc.

## Validation Criteria

The task is considered complete when:

- ✅ All 27 tests pass
- ✅ Terraform applies without errors
- ✅ Failover validation JSON contains canary string
- ✅ Failover time ≤60 seconds
- ✅ All required infrastructure components exist in both regions

## Files

```
Template/
├── instruction.md           # Task instructions
├── task.toml               # Task metadata (difficulty=hard, category=infrastructure)
├── environment/
│   └── Dockerfile          # Python 3.11 + Terraform 1.6.6 + AWS CLI + LocalStack
├── solution/
│   └── solve.sh            # Oracle solution (creates all Terraform files, runs deployment)
├── tests/
│   ├── test.sh            # Test runner
│   └── test_outputs.py    # 27 comprehensive tests
└── README.md              # This file
```

## Running the Task

### Using Harbor CLI

```bash
# Run against Claude Sonnet 4.5
harbor run -a terminus-2 -m openai/@anthropic-tbench/claude-sonnet-4-5-20250929 -p Template/

# Run against GPT-5
harbor run -a terminus-2 -m openai/@openai-tbench/gpt-5 -p Template/

# Start interactive environment for debugging
harbor tasks start-env --path Template/ --interactive
```

### Expected Behavior

**Successful Run:**
1. Agent creates Terraform configuration files
2. Initializes Terraform and installs providers
3. Plans and applies infrastructure to LocalStack
4. Creates failover simulation script
5. Runs failover simulation
6. Generates validation JSON with canary string
7. All 27 tests pass

**Common Failure Modes:**
- Provider configuration errors (LocalStack endpoints)
- Resource dependency cycles
- IAM permission issues
- Missing cross-region replication configuration
- Failover validation missing canary string
- Terraform state not created (didn't actually run apply)

## Design Rationale

### Why This Tests Frontier Models

1. **Multi-Step Planning**: Requires planning infrastructure before implementation
2. **Architectural Decisions**: Must choose between modules vs. flat structure
3. **Cross-Service Integration**: Tests understanding of how AWS services interact
4. **LocalStack Adaptation**: Must adapt real AWS patterns to LocalStack constraints
5. **Validation Logic**: Must create scripts that prove failover works

### Why Pass Rate Should Be <40%

- Requires expert-level Terraform and AWS knowledge
- Many moving parts with complex dependencies
- LocalStack introduces additional challenges
- Failover validation is non-trivial to implement correctly
- Easy to miss requirements (e.g., latency-based routing, cross-region replication)

## Canary String

**TERMINUS_INFRA_MULTI_REGION_42XZ**

This must appear in `/app/results/failover_validation.json` to pass the anti-cheating test.
