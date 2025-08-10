from typing import Callable

import pydantic
from fastapi import (
    Request,
    status,
)
from fastapi.responses import JSONResponse


async def handle_broad_exception(request: Request, call_next: Callable):
    try:
        return await call_next(request)
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
        

async def handle_pydantic_validation_errors(request: Request, exc: pydantic.ValidationError):
    errors = exc.errors()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": [
                {"msg": error["msg"], "input": error["input"]}
                for error in errors
            ]
        },
    )