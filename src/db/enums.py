import enum

class BranchEnum(str, enum.Enum):
    IT = "IT"
    VIDEO_EDITING = "VIDEO_EDITING"
    TRAINER = "TRAINER"
    TEACHER = "TEACHER"
    DESIGN = "DESIGN"

class OrderStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"