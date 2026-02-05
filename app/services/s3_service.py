import boto3
from botocore.exceptions import ClientError
from app.config.settings import settings
from typing import Optional
import uuid
from datetime import datetime
import io


class S3Service:
    """Handle file uploads/downloads to AWS S3"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    async def upload_audio(
        self,
        audio_bytes: bytes,
        meeting_id: str,
        turn_number: int,
        speaker: str
    ) -> str:
        """
        Upload audio file to S3
        
        Returns:
            S3 URL of uploaded file
        """
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"meetings/{meeting_id}/turns/turn_{turn_number:04d}_{speaker}_{timestamp}.mp3"
        
        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=audio_bytes,
                ContentType='audio/mpeg',
                Metadata={
                    'meeting_id': meeting_id,
                    'turn_number': str(turn_number),
                    'speaker': speaker
                }
            )
            
            # Generate URL
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
            return url
            
        except ClientError as e:
            print(f"Error uploading audio to S3: {e}")
            raise
    
    async def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        folder: str = "documents"
    ) -> str:
        """
        Upload document (PDF, PPTX, DOC, Image) to S3
        
        Returns:
            S3 URL of uploaded file
        """
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = filename.split('.')[-1]
        s3_filename = f"{folder}/{file_id}_{filename}"
        
        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_filename,
                Body=file_bytes,
                ContentType=content_type,
                Metadata={
                    'original_filename': filename
                }
            )
            
            # Generate URL
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_filename}"
            return url
            
        except ClientError as e:
            print(f"Error uploading document to S3: {e}")
            raise
    
    async def upload_full_meeting_audio(
        self,
        audio_bytes: bytes,
        meeting_id: str
    ) -> str:
        """Upload complete meeting audio recording"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"meetings/{meeting_id}/full_meeting_{timestamp}.mp3"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=audio_bytes,
                ContentType='audio/mpeg',
                Metadata={
                    'meeting_id': meeting_id,
                    'type': 'full_recording'
                }
            )
            
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
            return url
            
        except ClientError as e:
            print(f"Error uploading full meeting audio: {e}")
            raise
    
    async def download_file(self, s3_url: str) -> bytes:
        """Download file from S3 using URL"""
        
        # Extract key from URL
        key = s3_url.split(f"{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return response['Body'].read()
            
        except ClientError as e:
            print(f"Error downloading file from S3: {e}")
            raise
    
    async def delete_file(self, s3_url: str) -> bool:
        """Delete file from S3"""
        
        key = s3_url.split(f"{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
            
        except ClientError as e:
            print(f"Error deleting file from S3: {e}")
            return False
    
    def generate_presigned_url(self, s3_url: str, expiration: int = 3600) -> str:
        """Generate presigned URL for secure file access"""
        
        key = s3_url.split(f"{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            raise


# Singleton instance
s3_service = S3Service()