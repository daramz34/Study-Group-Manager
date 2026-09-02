import cloudinary
import cloudinary.uploader
from core.config import settings


cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)



def upload_file(file, folder:str = "study-group-resources"):
    """Upload file to Cloudinary, return URL"""

    result = cloudinary.uploader.upload(file, folder=folder, resource_type="auto")

    return {
        "url": result["secure_url"],
        "type": result["resource_type"],  # image, video, raw
        "format": result.get("format")
    }