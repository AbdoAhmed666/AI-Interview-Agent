import pytest
from pathlib import Path

if not Path("uploads/user_1").exists():
    pytest.skip(
        "legacy manual script: hardcodes a local (Windows) CV path and needs "
        "uncommitted fixtures under uploads/user_1/.",
        allow_module_level=True,
    )

from cv.storage import CVStorage

storage = CVStorage()

storage.save_cv(
    user_id=1,
    cv_file=Path(r"D:\projects\AI-Interview-Agent\backend\uploads\user_1\cv.pdf"),
)

print()

print(storage.get_active_cv(1))

print()

print(storage.list_versions(1))