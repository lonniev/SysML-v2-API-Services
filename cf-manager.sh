#!/bin/bash
# CloudFormation Management Script
# Provides shortcuts for common CloudFormation operations

# Configuration
STACK_NAME="sysml-v2-stack"
TEMPLATE_FILE="cloudformation-for-sysml2.yaml"
CHANGE_SET_NAME="sysml-v2-changes"
ECR_IMAGE="709825985650.dkr.ecr.us-east-1.amazonaws.com/sysml-at-your-service/sysml-at-your-service-image:0.1.0-20250606.1"
DOMAIN_NAME="sysml-v2-api.digitalthread.link"
HOSTED_ZONE_ID="Z05323903RWKM79BTU4Q5" # Replace with your actual Route 53 hosted zone ID
CREATE_DNS_RECORD="true"
ENABLE_COGNITO="true"
COGNITO_DOMAIN_PREFIX="sysml-saas-auth"
ADMIN_USERNAME="sysml2_admin"
ADMIN_EMAIL="admin@example.com" # Replace with your actual admin email

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to display usage information
show_usage() {
  echo -e "${YELLOW}CloudFormation Management Script${NC}"
  echo "Usage: $0 [command]"
  echo ""
  echo "Commands:"
  echo "  changeset create     - Create a new change set"
  echo "  changeset describe   - Describe the current change set"
  echo "  changeset execute    - Execute the current change set"
  echo "  stack describe       - Describe the current stack"
  echo "  stack events         - Show stack events"
  echo "  stack outputs        - Show stack outputs"
  echo "  stack update         - Update the stack directly"
  echo "  stack delete         - Delete the stack"
  echo "  validate             - Validate the CloudFormation template"
  echo "  help                 - Show this help message"
}

# Function to create a change set
create_changeset() {
  echo -e "${GREEN}Creating change set: $CHANGE_SET_NAME for stack: $STACK_NAME...${NC}"
  aws cloudformation create-change-set \
    --stack-name $STACK_NAME \
    --change-set-name $CHANGE_SET_NAME \
    --template-body file://$TEMPLATE_FILE \
    --parameters \
      ParameterKey=ECSImage,ParameterValue=$ECR_IMAGE \
      ParameterKey=DBInstanceClass,ParameterValue=db.t3.medium \
      ParameterKey=DomainName,ParameterValue=$DOMAIN_NAME \
      ParameterKey=HostedZoneId,ParameterValue=$HOSTED_ZONE_ID \
      ParameterKey=CreateDNSRecord,ParameterValue=$CREATE_DNS_RECORD \
      ParameterKey=EnableCognito,ParameterValue=$ENABLE_COGNITO \
      ParameterKey=CognitoDomainPrefix,ParameterValue=$COGNITO_DOMAIN_PREFIX \
      ParameterKey=AdminUsername,ParameterValue=$ADMIN_USERNAME \
      ParameterKey=AdminEmail,ParameterValue=$ADMIN_EMAIL \
      ParameterKey=CertificateOption,ParameterValue=New \
      ParameterKey=SecretsOption,ParameterValue=CreateNew \
    --capabilities CAPABILITY_IAM \
    --change-set-type CREATE
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Change set creation initiated. Use 'changeset describe' to check status.${NC}"
  else
    echo -e "${RED}Failed to create change set.${NC}"
  fi
}

# Function to update stack directly
update_stack() {
  echo -e "${YELLOW}WARNING: You are about to update the stack: $STACK_NAME${NC}"
  read -p "Are you sure you want to proceed? (y/n): " confirm
  
  if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    echo -e "${GREEN}Updating stack: $STACK_NAME...${NC}"
    aws cloudformation update-stack \
      --stack-name $STACK_NAME \
      --template-body file://$TEMPLATE_FILE \
      --parameters \
        ParameterKey=ECSImage,ParameterValue=$ECR_IMAGE \
        ParameterKey=DBInstanceClass,ParameterValue=db.t3.medium \
        ParameterKey=DomainName,ParameterValue=$DOMAIN_NAME \
        ParameterKey=HostedZoneId,ParameterValue=$HOSTED_ZONE_ID \
        ParameterKey=CreateDNSRecord,ParameterValue=$CREATE_DNS_RECORD \
        ParameterKey=EnableCognito,ParameterValue=$ENABLE_COGNITO \
        ParameterKey=CognitoDomainPrefix,ParameterValue=$COGNITO_DOMAIN_PREFIX \
        ParameterKey=AdminUsername,ParameterValue=$ADMIN_USERNAME \
        ParameterKey=AdminEmail,ParameterValue=$ADMIN_EMAIL \
        ParameterKey=CertificateOption,ParameterValue=New \
        ParameterKey=SecretsOption,ParameterValue=CreateNew \
      --capabilities CAPABILITY_IAM
    
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}Stack update initiated. Use 'stack describe' to check status.${NC}"
    else
      echo -e "${RED}Failed to update stack.${NC}"
    fi
  else
    echo -e "${YELLOW}Stack update cancelled.${NC}"
  fi
}

# Function to describe a change set
describe_changeset() {
  echo -e "${GREEN}Describing change set: $CHANGE_SET_NAME for stack: $STACK_NAME...${NC}"
  aws cloudformation describe-change-set \
    --stack-name $STACK_NAME \
    --change-set-name $CHANGE_SET_NAME
}

# Function to execute a change set
execute_changeset() {
  echo -e "${GREEN}Executing change set: $CHANGE_SET_NAME for stack: $STACK_NAME...${NC}"
  aws cloudformation execute-change-set \
    --stack-name $STACK_NAME \
    --change-set-name $CHANGE_SET_NAME
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}Change set execution initiated. Use 'stack describe' to check status.${NC}"
  else
    echo -e "${RED}Failed to execute change set.${NC}"
  fi
}

# Function to describe a stack
describe_stack() {
  echo -e "${GREEN}Describing stack: $STACK_NAME...${NC}"
  aws cloudformation describe-stacks \
    --stack-name $STACK_NAME
}

# Function to show stack events
show_stack_events() {
  echo -e "${GREEN}Showing events for stack: $STACK_NAME...${NC}"
  aws cloudformation describe-stack-events \
    --stack-name $STACK_NAME
}

# Function to show stack outputs
show_stack_outputs() {
  echo -e "${GREEN}Showing outputs for stack: $STACK_NAME...${NC}"
  aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs"
}

# Function to delete a stack
delete_stack() {
  echo -e "${YELLOW}WARNING: You are about to delete the stack: $STACK_NAME${NC}"
  read -p "Are you sure you want to proceed? (y/n): " confirm
  
  if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    echo -e "${GREEN}Deleting stack: $STACK_NAME...${NC}"
    aws cloudformation delete-stack \
      --stack-name $STACK_NAME
    
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}Stack deletion initiated. Use 'stack describe' to check status.${NC}"
    else
      echo -e "${RED}Failed to delete stack.${NC}"
    fi
  else
    echo -e "${YELLOW}Stack deletion cancelled.${NC}"
  fi
}

# Function to validate the template
validate_template() {
  echo -e "${GREEN}Validating template: $TEMPLATE_FILE...${NC}"
  aws cloudformation validate-template \
    --template-body file://$TEMPLATE_FILE
}

# Main command processing
if [ $# -lt 1 ]; then
  show_usage
  exit 1
fi

case "$1 $2" in
  "changeset create")
    create_changeset
    ;;
  "changeset describe")
    describe_changeset
    ;;
  "changeset execute")
    execute_changeset
    ;;
  "stack describe")
    describe_stack
    ;;
  "stack events")
    show_stack_events
    ;;
  "stack outputs")
    show_stack_outputs
    ;;
  "stack update")
    update_stack
    ;;
  "stack delete")
    delete_stack
    ;;
  "validate")
    validate_template
    ;;
  "help")
    show_usage
    ;;
  *)
    echo -e "${RED}Unknown command: $1 $2${NC}"
    show_usage
    exit 1
    ;;
esac

exit 0
