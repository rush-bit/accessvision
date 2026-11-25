from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi import UploadFile, File, HTTPException
from PIL import Image, UnidentifiedImageError
from uuid import UUID
from pathlib import Path
from uuid import uuid4
from io import BytesIO


app = FastAPI(
    title="AccessVision API",
    description="AI-assisted accessibility assessment prototype",
    version="0.1.0"
)

# Allow the React development server to communicate with FastAPI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "AccessVision backend is running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "AccessVision API"
    }


# Upload configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_FORMATS = {
    "JPEG": {
        "extension": ".jpg",
        "content_type": "image/jpeg",
    },
    "PNG": {
        "extension": ".png",
        "content_type": "image/png",
    },
    "WEBP": {
        "extension": ".webp",
        "content_type": "image/webp",
    },
}


@app.post("/api/images/upload")
async def upload_image(file: UploadFile = File(...)):

    # 1. Check whether a file was provided
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was provided"
        )

    # 2. Read the file and enforce the size limit
    contents = await file.read(MAX_UPLOAD_SIZE + 1)

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds the 5 MB limit"
        )

    # 3. Verify that the file is a valid image
    try:
        with Image.open(BytesIO(contents)) as image:
            image_format = image.format

            if image_format not in ALLOWED_FORMATS:
                raise HTTPException(
                    status_code=415,
                    detail="Unsupported image format"
                )

            image.verify()

    except HTTPException:
        raise

    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid or corrupted image"
        )

    # 4. Generate a unique filename
    image_id = str(uuid4())

    image_info = ALLOWED_FORMATS[image_format]
    extension = image_info["extension"]
    content_type = image_info["content_type"]

    filename = f"{image_id}{extension}"
    file_path = UPLOAD_DIR / filename

    file_path.write_bytes(contents)

    # 6. Return upload details
    return {
        "status": "success",
        "image_id": image_id,
        "filename": filename,
        "content_type": content_type,
        "size_bytes": len(contents)
    }


@app.get("/api/images/{image_id}")
async def get_image(image_id: UUID):

    # Convert UUID to a safe string
    image_id = str(image_id)

    # Look for the uploaded image using supported extensions
    allowed_extensions = {
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    for extension, content_type in allowed_extensions.items():

        file_path = UPLOAD_DIR / f"{image_id}{extension}"

        if file_path.is_file():
            return FileResponse(
                path=file_path,
                media_type=content_type
            )

    # Image ID does not exist
    raise HTTPException(
        status_code=404,
        detail="Image not found"
    )
