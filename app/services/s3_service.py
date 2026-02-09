# import boto3
# from botocore.exceptions import ClientError
# from app.config.settings import settings
# from typing import Optional
# import uuid
# from datetime import datetime
# import io


# class S3Service:
#     """Handle file uploads/downloads to AWS S3"""
    
#     def __init__(self):
#         self.s3_client = boto3.client(
#             's3',
#             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#             region_name=settings.AWS_REGION
#         )
#         self.bucket_name = settings.S3_BUCKET_NAME
    
#     async def upload_audio(
#         self,
#         audio_bytes: bytes,
#         meeting_id: str,
#         turn_number: int,
#         speaker: str
#     ) -> str:
#         """
#         Upload audio file to S3
        
#         Returns:
#             S3 URL of uploaded file
#         """
        
#         # Generate unique filename
#         timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
#         filename = f"meetings/{meeting_id}/turns/turn_{turn_number:04d}_{speaker}_{timestamp}.mp3"
        
#         try:
#             # Upload to S3
#             self.s3_client.put_object(
#                 Bucket=self.bucket_name,
#                 Key=filename,
#                 Body=audio_bytes,
#                 ContentType='audio/mpeg',
#                 Metadata={
#                     'meeting_id': meeting_id,
#                     'turn_number': str(turn_number),
#                     'speaker': speaker
#                 }
#             )
            
#             # Generate URL
#             url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
#             return url
            
#         except ClientError as e:
#             print(f"Error uploading audio to S3: {e}")
#             raise
    
#     async def upload_document(
#         self,
#         file_bytes: bytes,
#         filename: str,
#         content_type: str,
#         folder: str = "documents"
#     ) -> str:
#         """
#         Upload document (PDF, PPTX, DOC, Image) to S3
        
#         Returns:
#             S3 URL of uploaded file
#         """
        
#         # Generate unique filename
#         file_id = str(uuid.uuid4())
#         file_extension = filename.split('.')[-1]
#         s3_filename = f"{folder}/{file_id}_{filename}"
        
#         try:
#             # Upload to S3
#             self.s3_client.put_object(
#                 Bucket=self.bucket_name,
#                 Key=s3_filename,
#                 Body=file_bytes,
#                 ContentType=content_type,
#                 Metadata={
#                     'original_filename': filename
#                 }
#             )
            
#             # Generate URL
#             url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_filename}"
#             return url
            
#         except ClientError as e:
#             print(f"Error uploading document to S3: {e}")
#             raise
    
#     async def upload_full_meeting_audio(
#         self,
#         audio_bytes: bytes,
#         meeting_id: str
#     ) -> str:
#         """Upload complete meeting audio recording"""
        
#         timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
#         filename = f"meetings/{meeting_id}/full_meeting_{timestamp}.mp3"
        
#         try:
#             self.s3_client.put_object(
#                 Bucket=self.bucket_name,
#                 Key=filename,
#                 Body=audio_bytes,
#                 ContentType='audio/mpeg',
#                 Metadata={
#                     'meeting_id': meeting_id,
#                     'type': 'full_recording'
#                 }
#             )
            
#             url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
#             return url
            
#         except ClientError as e:
#             print(f"Error uploading full meeting audio: {e}")
#             raise
    
#     async def download_file(self, s3_url: str) -> bytes:
#         """Download file from S3 using URL"""
        
#         # Extract key from URL
#         key = s3_url.split(f"{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]
        
#         try:
#             response = self.s3_client.get_object(
#                 Bucket=self.bucket_name,
#                 Key=key
#             )
#             return response['Body'].read()
            
#         except ClientError as e:
#             print(f"Error downloading file from S3: {e}")
#             raise
    
#     async def delete_file(self, s3_url: str) -> bool:
#         """Delete file from S3"""
        
#         key = s3_url.split(f"{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]
        
#         try:
#             self.s3_client.delete_object(
#                 Bucket=self.bucket_name,
#                 Key=key
#             )
#             return True
            
#         except ClientError as e:
#             print(f"Error deleting file from S3: {e}")
#             return False
    
#     def generate_presigned_url(self, s3_url: str, expiration: int = 3600) -> str:
#         """Generate presigned URL for secure file access"""
        
#         key = s3_url.split(f"{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]
        
#         try:
#             url = self.s3_client.generate_presigned_url(
#                 'get_object',
#                 Params={
#                     'Bucket': self.bucket_name,
#                     'Key': key
#                 },
#                 ExpiresIn=expiration
#             )
#             return url
            
#         except ClientError as e:
#             print(f"Error generating presigned URL: {e}")
#             raise


# # Singleton instance
# s3_service = S3Service()







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
        self.enabled = False
        self.s3_client = None
        self.bucket_name = settings.S3_BUCKET_NAME
        
        # Only initialize if credentials exist
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
                # Test connection
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                self.enabled = True
                print(f"✅ S3 Service initialized - Bucket: {self.bucket_name}")
            except Exception as e:
                print(f"⚠️ S3 Service initialization failed: {e}")
                print(f"⚠️ Audio will NOT be saved to S3")
                self.enabled = False
        else:
            print("⚠️ S3 credentials not found - audio will not be saved to S3")
    
    async def upload_audio(
        self,
        audio_bytes: bytes,
        meeting_id: str,
        turn_number: int,
        speaker: str
    ) -> Optional[str]:
        """
        Upload audio file to S3
        
        Returns:
            S3 URL of uploaded file or None if S3 disabled
        """
        
        # If S3 not enabled, return None (don't fail)
        if not self.enabled:
            print(f"⚠️ S3 disabled - Skipping audio upload for turn {turn_number}")
            return None
        
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
            print(f"✅ Audio uploaded to S3: {filename}")
            return url
            
        except ClientError as e:
            print(f"❌ Error uploading audio to S3: {e}")
            # Don't raise - just return None so conversation continues
            return None
        except Exception as e:
            print(f"❌ Unexpected error uploading to S3: {e}")
            return None
    
    async def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        folder: str = "documents"
    ) -> Optional[str]:
        """
        Upload document (PDF, PPTX, DOC, Image) to S3
        
        Returns:
            S3 URL of uploaded file or None if failed
        """
        
        if not self.enabled:
            print(f"⚠️ S3 disabled - Cannot upload document: {filename}")
            return None
        
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
            print(f"✅ Document uploaded to S3: {s3_filename}")
            return url
            
        except ClientError as e:
            print(f"❌ Error uploading document to S3: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    async def upload_full_meeting_audio(
        self,
        audio_bytes: bytes,
        meeting_id: str
    ) -> Optional[str]:
        """Upload complete meeting audio recording"""
        
        if not self.enabled:
            print(f"⚠️ S3 disabled - Cannot upload full meeting audio")
            return None
        
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
            print(f"✅ Full meeting audio uploaded: {filename}")
            return url
            
        except ClientError as e:
            print(f"❌ Error uploading full meeting audio: {e}")
            return None
    
    async def download_file(self, s3_url: str) -> Optional[bytes]:
        """Download file from S3 using URL"""
        
        if not self.enabled:
            print(f"⚠️ S3 disabled - Cannot download file")
            return None
        
        # Extract key from URL
        try:
            key = s3_url.split(f"{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]
        except:
            print(f"❌ Invalid S3 URL: {s3_url}")
            return None
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return response['Body'].read()
            
        except ClientError as e:
            print(f"❌ Error downloading file from S3: {e}")
            return None
    
    async def delete_file(self, s3_url: str) -> bool:
        """Delete file from S3"""
        
        if not self.enabled:
            return False
        
        try:
            key = s3_url.split(f"{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]
        except:
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
            
        except ClientError as e:
            print(f"❌ Error deleting file from S3: {e}")
            return False
    
    def generate_presigned_url(self, s3_url: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL for secure file access"""
        
        if not self.enabled:
            return None
        
        try:
            key = s3_url.split(f"{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]
        except:
            return None
        
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
            print(f"❌ Error generating presigned URL: {e}")
            return None


# Singleton instance
s3_service = S3Service()