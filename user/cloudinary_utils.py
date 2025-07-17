import cloudinary
import cloudinary.uploader
from django.conf import settings

# Access values from settings.py
cloud_name = settings.CLOUDINARY_CLOUD_NAME
api_key = settings.CLOUDINARY_API_KEY
api_secret = settings.CLOUDINARY_API_SECRET

if not all([cloud_name, api_key, api_secret]):
    raise ValueError("Cloudinary credentials are not properly set in the environment variables.")

# Configure Cloudinary
cloudinary.config(
    cloud_name=cloud_name,
    api_key=api_key,
    api_secret=api_secret

)
def cloudinary_upload(file):
    try:
        response = cloudinary.uploader.upload(file)
        return response
    except Exception as e:
        print(f"Error uploading to Cloudinary: {e}")
        return None
