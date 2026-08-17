import importlib.util
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from security import get_current_user
from models import User
import logging
from config import RUNTIME_DIR


def _load_module(module_name: str, module_path: Path):
    """Load a Python module from a file path without relying on package imports."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {module_name} from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cv_schemas = _load_module(
    "backend_cv_schemas",
    Path(__file__).resolve().parent.parent / "schemas" / "cv.py",
)
CVAnalysisResponse = cv_schemas.CVAnalysisResponse
CVListResponse = cv_schemas.CVListResponse
CVUploadResponse = cv_schemas.CVUploadResponse

CVService = _load_module(
    "backend_cv_service",
    Path(__file__).resolve().parent.parent / "services" / "cv_service.py",
).CVService

router = APIRouter(
    prefix="/cv",
    tags=["CV"],
)


def get_cv_service() -> CVService:
    """Create a CV service instance for dependency injection."""
    return CVService()

logger = logging.getLogger("api.cv")


def _save_upload_file(file: UploadFile) -> Path:
    """Persist an uploaded file to a temporary location."""
    temp_dir = RUNTIME_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_file = temp_dir / Path(file.filename or "cv.pdf").name

    with temp_file.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return temp_file


@router.post("/upload", response_model=CVUploadResponse)
async def upload_cv(
    file: UploadFile = File(...),
    service: CVService = Depends(get_cv_service),
    current_user: User = Depends(get_current_user),
) -> CVUploadResponse:
    if file.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    try:
        result = service.process_uploaded_cv(
            user_id=current_user.id,
            uploaded_file=_save_upload_file(file),
        )

        return CVUploadResponse(
            uploaded=True,
            filename=result["cv_path"].name,
            detected_skills=result["analysis"].skills,
            recommended_roles=[
                role.role
                for role in result["recommendations"]
            ],
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        # If any processing step failed after the file was saved, return
        # uploaded=True with the active filename so the frontend can show it.
        logger.exception("process_uploaded_cv failed for user_id=%s: %s", current_user.id, exc)

        summary = service.get_cv_summary(user_id=current_user.id)
        filename = summary.get("active_cv")

        if filename is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Uploaded but analysis failed and active CV not found.",
            )

        return CVUploadResponse(
            uploaded=True,
            filename=filename,
            detected_skills=[],
            recommended_roles=[],
        )


@router.get("", response_model=CVListResponse)
def get_cv(
    service: CVService = Depends(get_cv_service),
    current_user: User = Depends(get_current_user),
) -> CVListResponse:
    logger.debug("GET /cv for user_id=%s", current_user.id)
    summary = service.get_cv_summary(user_id=current_user.id)
    logger.debug("GET /cv summary for user_id=%s -> %s", current_user.id, summary)
    return summary


@router.get("/analysis", response_model=CVAnalysisResponse)
def get_cv_analysis(
    service: CVService = Depends(get_cv_service),
    current_user: User = Depends(get_current_user),
) -> CVAnalysisResponse:
    try:
        return service.get_cv_analysis(user_id=current_user.id)
    except Exception as exc:
        # Parser/analyzer errors should not cause GET /cv to break.
        # Return a clear HTTP error indicating analysis failed.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"CV analysis failed: {str(exc)}",
        ) from exc
   
