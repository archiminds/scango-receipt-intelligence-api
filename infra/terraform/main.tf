#############################################
# Root module data sources and dependencies #
#############################################

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

data "aws_region" "current" {}

# These data sources are referenced across IAM policies and outputs.
