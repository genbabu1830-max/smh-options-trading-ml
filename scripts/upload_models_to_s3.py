"""
Upload Models to S3
===================

Syncs local models_storage/ directory to S3 bucket.

Usage:
    python scripts/upload_models_to_s3.py --bucket options-trading-models
    python scripts/upload_models_to_s3.py --bucket options-trading-models --dry-run
"""

import os
import argparse
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("❌ boto3 not installed. Install: pip install boto3")
    exit(1)


def upload_directory_to_s3(
    local_dir: str,
    bucket_name: str,
    s3_prefix: str = '',
    dry_run: bool = False
):
    """
    Upload directory to S3, preserving structure.
    
    Args:
        local_dir: Local directory path
        bucket_name: S3 bucket name
        s3_prefix: S3 key prefix (optional)
        dry_run: If True, only show what would be uploaded
    """
    s3 = boto3.client('s3')
    
    # Ensure bucket exists
    if not dry_run:
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket exists: {bucket_name}")
        except ClientError:
            print(f"Creating bucket: {bucket_name}")
            s3.create_bucket(Bucket=bucket_name)
            print(f"✅ Created bucket: {bucket_name}")
    
    # Walk through local directory
    local_path = Path(local_dir)
    uploaded_count = 0
    skipped_count = 0
    
    for file_path in local_path.rglob('*'):
        if file_path.is_file():
            # Calculate relative path
            relative_path = file_path.relative_to(local_path)
            s3_key = str(relative_path).replace('\\', '/')
            
            if s3_prefix:
                s3_key = f"{s3_prefix}/{s3_key}"
            
            # Get file size
            file_size = file_path.stat().st_size
            size_mb = file_size / (1024 * 1024)
            
            if dry_run:
                print(f"[DRY RUN] Would upload: {file_path} → s3://{bucket_name}/{s3_key} ({size_mb:.2f} MB)")
                uploaded_count += 1
            else:
                try:
                    # Check if file already exists in S3
                    try:
                        s3_obj = s3.head_object(Bucket=bucket_name, Key=s3_key)
                        s3_size = s3_obj['ContentLength']
                        
                        if s3_size == file_size:
                            print(f"⏭️  Skipping (unchanged): {s3_key}")
                            skipped_count += 1
                            continue
                    except ClientError:
                        pass  # File doesn't exist, will upload
                    
                    # Upload file
                    print(f"📤 Uploading: {file_path} → s3://{bucket_name}/{s3_key} ({size_mb:.2f} MB)")
                    
                    s3.upload_file(
                        str(file_path),
                        bucket_name,
                        s3_key,
                        ExtraArgs={
                            'Metadata': {
                                'source': 'local_upload',
                                'original_path': str(file_path)
                            }
                        }
                    )
                    
                    uploaded_count += 1
                    print(f"   ✅ Uploaded successfully")
                    
                except Exception as e:
                    print(f"   ❌ Error uploading {file_path}: {e}")
    
    return uploaded_count, skipped_count


def main():
    parser = argparse.ArgumentParser(description='Upload models to S3')
    parser.add_argument(
        '--bucket',
        type=str,
        default='options-trading-models',
        help='S3 bucket name (default: options-trading-models)'
    )
    parser.add_argument(
        '--local-dir',
        type=str,
        default='models_storage',
        help='Local directory to upload (default: models_storage)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be uploaded without actually uploading'
    )
    parser.add_argument(
        '--region',
        type=str,
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Upload Models to S3")
    print("=" * 60)
    print(f"Local directory: {args.local_dir}")
    print(f"S3 bucket: {args.bucket}")
    print(f"Region: {args.region}")
    print(f"Dry run: {args.dry_run}")
    print("=" * 60)
    
    # Check if local directory exists
    if not os.path.exists(args.local_dir):
        print(f"❌ Local directory not found: {args.local_dir}")
        return
    
    # Upload
    uploaded, skipped = upload_directory_to_s3(
        local_dir=args.local_dir,
        bucket_name=args.bucket,
        dry_run=args.dry_run
    )
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    if args.dry_run:
        print(f"Would upload: {uploaded} files")
    else:
        print(f"✅ Uploaded: {uploaded} files")
        print(f"⏭️  Skipped: {skipped} files (unchanged)")
        print(f"\nBucket URL: https://s3.console.aws.amazon.com/s3/buckets/{args.bucket}")
    print("=" * 60)


if __name__ == "__main__":
    main()
