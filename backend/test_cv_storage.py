from pathlib import Path

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