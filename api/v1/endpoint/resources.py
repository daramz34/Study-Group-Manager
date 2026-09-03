from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends, Request, Response
from crud import upload_resource, get_group_resources, get_resource_by_id, delete_resource
from schemas import ResourceResponse, ResourceCreate
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from database import get_db
from models import User
from core.dependencies import get_current_user
from services.cloudinary import upload_file
from enums import FileType

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/resources", tags=["RESOURCES"])


@router.post("/groups/{group_id}", response_model=ResourceResponse, status_code=201)
@limiter.limit("10/day")
def upload_resource_endpoint(
    request: Request,
    group_id: int,
    title: str = Form(...),
    description: str = Form(None),
    file_type: FileType = Form(...),  
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Upload to Cloudinary
    upload_result = upload_file(file.file)

    # Build ResourceCreate
    resource = ResourceCreate(
        title=title,
        description=description,
        file_url=upload_result["url"],
        file_type=file_type
    )

    result = upload_resource(db, group_id, resource, current_user)
    if not result:
        raise HTTPException(status_code=403, detail="Not a group member")
    return result


@router.get("/groups/{group_id}", response_model=list[ResourceResponse])
def get_group_resources_endpoint(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    result = get_group_resources(db, group_id, current_user)
    if result is None:
        raise HTTPException(status_code=403, detail="Not a group member")
    return result


@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource_endpoint(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = get_resource_by_id(db, resource_id, current_user)
    if not result:
        raise HTTPException(status_code=404, detail="Resource not found")
    return result


@router.delete("/{resource_id}", status_code=204)
def delete_resource_endpoint(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = delete_resource(db, resource_id, current_user)
    if not result:
        raise HTTPException(status_code=403, detail="Only uploader/admin/owner can delete")
    return Response(status_code=204)
