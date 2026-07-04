"""
自定义异常模块。

定义统一的异常基类 AppException 及其派生类，用于全局异常处理。
"""

from typing import Any, Optional


class AppException(Exception):
    """应用异常基类。

    所有业务异常应继承此类，以便全局异常处理器统一捕获并返回标准格式。

    Attributes:
        status_code: HTTP 状态码。
        error_code: 业务错误码（用于响应体 code 字段），对齐 SPEC §4.2。
        message: 面向用户的错误描述。
        detail: 额外的错误详情（可选），如字段级校验信息。
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        detail: Optional[Any] = None,
        error_code: int = 5000,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.detail = detail
        super().__init__(message)


class NotFoundError(AppException):
    """资源未找到 (404)。"""

    def __init__(
        self,
        message: str = "请求的资源不存在",
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(status_code=404, message=message, detail=detail, error_code=2001)


class UnauthorizedError(AppException):
    """未认证 (401)。"""

    def __init__(
        self,
        message: str = "未认证，请先登录",
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(status_code=401, message=message, detail=detail, error_code=1002)


class BadRequestError(AppException):
    """请求错误 (400)。"""

    def __init__(
        self,
        message: str = "请求参数错误",
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(status_code=400, message=message, detail=detail, error_code=1001)


class ForbiddenError(AppException):
    """无权限 (403)。"""

    def __init__(
        self,
        message: str = "无权限执行此操作",
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(status_code=403, message=message, detail=detail, error_code=1003)


class ValidationError(AppException):
    """请求参数校验失败 (422)。"""

    def __init__(
        self,
        message: str = "请求参数校验失败",
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(status_code=422, message=message, detail=detail, error_code=1005)


class ConflictError(AppException):
    """资源冲突 (409)。"""

    def __init__(
        self,
        message: str = "资源冲突，可能已存在",
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(status_code=409, message=message, detail=detail, error_code=2002)


class RateLimitError(AppException):
    """请求频率限制 (429)。"""

    def __init__(
        self,
        message: str = "请求过于频繁，请稍后再试",
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(status_code=429, message=message, detail=detail, error_code=1004)


class InternalError(AppException):
    """服务器内部错误 (500)。"""

    def __init__(
        self,
        message: str = "服务器内部错误",
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(status_code=500, message=message, detail=detail, error_code=5000)


class TokenRevokedError(AppException):
    """Token 已被撤销 (401)。"""

    def __init__(
        self,
        message: str = "Token 已被撤销，请重新登录",
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(status_code=401, message=message, detail=detail, error_code=1006)


class KeyingServiceError(AppException):
    """科应服务异常 (502)。"""

    def __init__(
        self,
        message: str = "科应服务暂时不可用",
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(status_code=502, message=message, detail=detail, error_code=3001)
