"""Upload generated data to S3 for use by agents.

Uploads all CSV files from data/output/ to configured S3 bucket.
"""

import boto3
import os
from pathlib import Path
import sys

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config


def upload_file(s3_client, file_path, bucket, s3_key):
    """Upload single file to S3.
    
    Args:
        s3_client: Boto3 S3 client
        file_path: Local file path
        bucket: S3 bucket name
        s3_key: S3 object key
        
    Returns:
        bool: Success status
    """
    try:
        s3_client.upload_file(
            str(file_path),
            bucket,
            s3_key,
            ExtraArgs={'ContentType': 'text/csv'}
        )
        print('  ✓ Uploaded {}'.format(s3_key))
        return True
    except Exception as e:
        print('  ✗ Failed to upload {}: {}'.format(s3_key, e))
        return False


def main():
    """Upload all data files to S3."""
    print('=' * 60)
    print('StormGuard S3 Upload')
    print('=' * 60)
    
    # Validate config
    bucket = config.S3_BUCKET
    if not bucket or bucket == 'stormguard-data':
        print('\nError: S3_BUCKET not configured!')
        print('Set environment variable or update .env file')
        print('Example: export S3_BUCKET=stormguard-data-yourname')
        return 1
    
    # Check AWS credentials
    try:
        session = boto3.Session(region_name=config.AWS_REGION)
        s3_client = session.client('s3')
        
        # Test connectivity
        s3_client.head_bucket(Bucket=bucket)
        print('\n✓ Connected to S3 bucket: {}'.format(bucket))
    except Exception as e:
        print('\nError: Cannot connect to S3: {}'.format(e))
        print('\nTroubleshooting:')
        print('1. Run: aws configure')
        print('2. Create bucket: aws s3 mb s3://{}'.format(bucket))
        return 1
    
    # Find files to upload
    output_dir = config.OUTPUT_DIR
    if not output_dir.exists():
        print('\nError: Output directory not found: {}'.format(output_dir))
        print('Run: python scripts/generate_all_data.py')
        return 1
    
    data_files = list(output_dir.glob('*.csv')) + list(output_dir.glob('*.json'))
    
    if not data_files:
        print('\nError: No data files found in {}'.format(output_dir))
        print('Run: python scripts/generate_all_data.py')
        return 1
    
    print('\nFound {} files to upload:'.format(len(data_files)))
    for f in data_files:
        print('  - {}'.format(f.name))
    
    # Upload files
    print('\nUploading to s3://{}/data/...'.format(bucket))
    
    success_count = 0
    for file_path in data_files:
        s3_key = 'data/{}'.format(file_path.name)
        if upload_file(s3_client, file_path, bucket, s3_key):
            success_count += 1
    
    print('\n' + '=' * 60)
    print('Upload complete: {}/{} files'.format(success_count, len(data_files)))
    print('=' * 60)
    
    if success_count == len(data_files):
        print('\n✓ All files uploaded successfully!')
        print('\nS3 URLs:')
        for f in data_files:
            s3_url = 's3://{}/data/{}'.format(bucket, f.name)
            print('  {}'.format(s3_url))
        
        print('\nNext steps:')
        print('1. Deploy infrastructure: cd infrastructure/terraform && terraform apply')
        print('2. Test agents: python agents/orchestrator.py')
        return 0
    else:
        print('\n✗ Some uploads failed. Check errors above.')
        return 1


if __name__ == '__main__':
    exit(main())
