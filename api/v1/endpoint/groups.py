from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from crud import (get_group_by_id, get_group_members,promote_to_admin,demote_to_member, transfer_ownership, send_group_invite, create_group,
                  get_group_by_id, leave_group, delete_group, join_group,  get_my_groups, update_group)
from schemas import GroupCreate, GroupResponse, PostionRequest, JoinGroupRequest, GroupMemberResponse, GroupUpdate, InviteUserRequest
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from database import get_db
from models import User
from core.dependencies import get_current_user


limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/groups", tags=["GROUPS"])


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED, description="Create Group")
@limiter.limit("5/day")
def create_group_endpoint(request: Request, group: GroupCreate, db:Session = Depends(get_db), current_user: User= Depends(get_current_user)):
    return create_group(db, group, current_user)


@router.get("/", response_model=list[GroupResponse], status_code=status.HTTP_200_OK, description="Get my Groups")
def get_my_groups_endpoint(db:Session = Depends(get_db), current_user:User = Depends(get_current_user)):
    groups = get_my_groups(db, current_user)
    if not groups:
        raise HTTPException(
            status_code=404,
            detail="No  Groups found"
        )
    return groups

@router.get("/{group_id}", response_model=GroupResponse, status_code=200, description="Get group Details")
def get_group_by_id_endpoint(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = get_group_by_id(db, group_id, current_user)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    return group

@router.put("/{group_id}", response_model=GroupResponse, status_code=200, description="Update group")
@limiter.limit("5/hour")
def update_group_endpoint(request: Request, group_id:int, group_update: GroupUpdate, db:Session=Depends(get_db), current_user:User = Depends(get_current_user)):
    update = update_group(db, group_id,group_update, current_user)

    if not update:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to update you are not an admin/owner"
        )
    return update

@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT, description="Delete group (admin/owner only)")
def delete_group_endpoint(group_id: int, db:Session= Depends(get_db), current_user: User=Depends(get_current_user)):
    db_delete = delete_group(db, group_id, current_user)

    if not db_delete:
        raise HTTPException(
            status_code= status.HTTP_403_FORBIDDEN,
            detail="Only admin/owner can delete"
        )

    return Response(status_code=204)


@router.post("/join", response_model=GroupMemberResponse, status_code=status.HTTP_201_CREATED, description="Invite code")
@limiter.limit("10/day")
def join_group_endpoint(request: Request,body: JoinGroupRequest, db:Session = Depends(get_db), current_user: User= Depends(get_current_user)):
    db_group = join_group(db, body.invite_code, current_user)

    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect Invite code or user already in group"
        )
    return db_group

@router.post("/groups/{group_id}/invite", status_code=200)
@limiter.limit("10/day")
def invite_user_endpoint(
    request: Request,
    group_id: int,
    body: InviteUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result, error = send_group_invite(db, group_id, body.email, current_user)
    
    if error:
        status_code = 403 if "owner/admin" in error else 404
        raise HTTPException(status_code=status_code, detail=error)
    
    return result

@router.get("/{group_id}/members", response_model=list[GroupMemberResponse], status_code=200, description="Get group Details")
def list_members_endpoint(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = get_group_members(db, group_id, current_user)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    return group


@router.post("/{group_id}/promote", response_model=GroupMemberResponse, status_code=status.HTTP_200_OK)
def promote_endpoint(group_id: int, body: PostionRequest, db:Session=Depends(get_db), current_user:User = Depends(get_current_user)):
    db_promote = promote_to_admin(db, group_id, body.user_id, current_user)

    if not db_promote:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail= "Only Owner can Promote"
        )
    return db_promote

@router.post("/{group_id}/demote", response_model=GroupMemberResponse, status_code=status.HTTP_200_OK)
def demote_endpoint(group_id: int, body: PostionRequest, db:Session=Depends(get_db), current_user:User= Depends(get_current_user)):
    db_demote = demote_to_member(db, group_id, body.user_id, current_user)
    if not db_demote:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Owner can demote"
        )
    return db_demote


@router.post("/{group_id}/transfer-ownership", response_model=GroupMemberResponse, status_code=200)
def transfer_ownership_endpoint(group_id:int, body: PostionRequest, db:Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    db_transfer = transfer_ownership(db, group_id, body.user_id, current_user)

    if not db_transfer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can transfer, new owner must be admin"
        )

    return db_transfer


@router.delete("/{group_id}/leave_group", status_code=204)
def leave_group_endpoint(group_id: int, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    db_leave= leave_group(db, group_id, current_user)
    if not db_leave:
        raise HTTPException(
            status_code=403,
            detail="Cannot leave — you are the owner or not a member"
        )

    return Response(status_code=204)

