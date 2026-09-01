from enum import Enum

class GroupRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    OWNER = "owner"


class FileType(str, Enum):
    pdf = "pdf"
    image = "image"
    doc = "doc"