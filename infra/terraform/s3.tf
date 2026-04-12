resource "aws_s3_bucket" "artifacts" {
  count  = var.enable_s3 ? 1 : 0
  bucket = local.s3_bucket_name

  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "artifacts" {
  count  = var.enable_s3 ? 1 : 0
  bucket = aws_s3_bucket.artifacts[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  count  = var.enable_s3 ? 1 : 0
  bucket = aws_s3_bucket.artifacts[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
