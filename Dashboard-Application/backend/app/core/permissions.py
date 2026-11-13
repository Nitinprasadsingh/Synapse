from enum import Enum
from typing import List
from fastapi import HTTPException, status


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    ANALYST = "analyst"


class RoleChecker:
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user_role: str):
        if user_role not in [role.value for role in self.allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {[r.value for r in self.allowed_roles]}"
            )
        return True


# Pre-defined permission guards
require_admin = RoleChecker([UserRole.ADMIN])
require_operator_or_admin = RoleChecker([UserRole.ADMIN, UserRole.OPERATOR])
require_analyst_or_admin = RoleChecker([UserRole.ADMIN, UserRole.ANALYST])
require_any_role = RoleChecker([UserRole.ADMIN, UserRole.OPERATOR, UserRole.ANALYST])
