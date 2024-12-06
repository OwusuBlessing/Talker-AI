from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
import os
import shutil
from typing import Optional
import uuid
from dataclasses import dataclass
import asyncio
from fastapi.background import BackgroundTasks
from talker import LinlyTalker,TalkerConfig
import nest_asyncio
import time
import time
from PIL import Image
from TFG import SadTalker
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
import secrets
from fastapi.responses import JSONResponse
# ImageKit configuration
imagekit = ImageKit(
    private_key="private_BXnyXGjdhBpBs/sU7avdyLwPx1o=",
    public_key="public_hb1iwGN/UWT+aYg9mMkUQNeFh40=",
    url_endpoint="6pxd8st0ugi"
)

async def upload_to_imagekit(file_path: str, user_id: str = "default") -> str:
    """Upload file to ImageKit and return the URL"""
    try:
        hex_string = secrets.token_hex(16)
        file_name = f"{user_id}_{hex_string}.mp4"
        
        with open(file_path, 'rb') as file:
            upload = imagekit.upload_file(
                file=file,
                file_name=file_name,
                options=UploadFileRequestOptions(
                    response_fields=["is_private_file", "tags"],
                    tags=["tag1", "tag2"]
                )
            )
        
        return upload.response_metadata.raw["url"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to ImageKit: {str(e)}")
        

# Add new directory for SadTalker outputs
SADTALKER_OUTPUT_DIR = "sadtalker_outputs"
os.makedirs(SADTALKER_OUTPUT_DIR, exist_ok=True)
# Create required directories if they don't exist
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
CROP_DIR = "uploads"
REFERENCE_IMAGE_PATH = "inputs/boy.png"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CROP_DIR, exist_ok=True)

app = FastAPI()

def resize_to_reference(image_path, reference_image_path):
    print(f"Opening image: {image_path}")
    print(f"Opening reference image: {reference_image_path}")
    
    # Open the original and reference images
    img = Image.open(image_path)
    ref_img = Image.open(reference_image_path)
    
    # Get the size of the reference image
    ref_width, ref_height = ref_img.size
    print(f"Reference image size: {ref_width}x{ref_height}")
    
    # Resize the original image to match the reference image size
    resized_img = img.resize((ref_width, ref_height))
    print(f"Resized original image to match reference size: {ref_width}x{ref_height}")
    
    # Save the resized image back to the same location with the same name
    resized_img.save(image_path)
    return image_path

async def cleanup_files(*file_paths: str):
    """Background task to cleanup files after response is sent"""
    await asyncio.sleep(1)  
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                print(f"Successfully cleaned up {file_path}")
        except Exception as e:
            print(f"Error cleaning up file {file_path}: {str(e)}")

async def save_upload_file(upload_file: UploadFile, destination_dir: str = UPLOAD_DIR) -> str:
    """Save uploaded file and return the file path"""
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(destination_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return file_path

@app.post("/goodangel/api/v1/generate-avatar")
async def generate_talking_video(
    image: UploadFile,
    audio: UploadFile,
    background_tasks: BackgroundTasks
):
    """
    Generate a talking head video from uploaded image and audio files.
    Returns the generated video file and cleans up afterwards.
    """
    image_path = None
    audio_path = None
    output_path = None
    resized_image_path = None
    
    try:
        # Validate inputs
        if not image.filename or not audio.filename:
            raise HTTPException(status_code=400, detail="Both image and audio files are required")

        # Save uploaded files
        image_path = await save_upload_file(image, CROP_DIR)  # Save directly to crop directory
        audio_path = await save_upload_file(audio)
        
        # Resize image to match reference
        resized_image_path = resize_to_reference(image_path, REFERENCE_IMAGE_PATH)
        
        # Generate unique output video filename
        output_filename = f"{uuid.uuid4()}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # Configure the talker
        config = TalkerConfig(
            pic_path=image_path,
            crop_pic_path=resized_image_path,
            audio_path=audio_path
        )
        
        # Initialize the talker
        talker = LinlyTalker(config=config)
        
        # Generate the video
        video_path = talker.generate_talking_video(
            output_path=output_path
        )
        
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Failed to generate video")

        # Create a copy of the video file that will be served
        temp_output_path = f"{output_path}_temp.mp4"
        shutil.copy2(output_path, temp_output_path)
        
        # Schedule cleanup for all files
        background_tasks.add_task(
            cleanup_files, 
            image_path, 
            audio_path, 
            output_path, 
            temp_output_path
        )
        
        # Return the temporary video file
        #upload to image kit
        '''return FileResponse(
            path=temp_output_path,
            media_type="video/mp4",
            filename=f"talking_head_{output_filename}",
            background=background_tasks
        )'''
        video_url = await upload_to_imagekit(video_path)
        return JSONResponse(content={"url": video_url})
            
    except Exception as e:
        # Clean up files immediately in case of error
        for file_path in [image_path, audio_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as cleanup_error:
                    print(f"Error cleaning up file {cleanup_error}: {str(cleanup_error)}")
                    
        raise HTTPException(status_code=500,detail=f"Error generating video: {str(e)}")

# Periodic cleanup function to catch any missed files
@app.on_event("startup")
async def setup_periodic_cleanup():
    async def cleanup_old_files():
        while True:
            try:
                # Clean files older than 1 hour
                current_time = time.time()
                for directory in [UPLOAD_DIR, OUTPUT_DIR, CROP_DIR]:
                    for filename in os.listdir(directory):
                        filepath = os.path.join(directory, filename)
                        file_modified_time = os.path.getmtime(filepath)
                        if current_time - file_modified_time > 3600:  # 1 hour
                            try:
                                if os.path.isfile(filepath):
                                    os.remove(filepath)
                                elif os.path.isdir(filepath):
                                    shutil.rmtree(filepath)
                                print(f"Cleaned up old file: {filepath}")
                            except Exception as e:
                                print(f"Error cleaning up old file {filepath}: {str(e)}")
            except Exception as e:
                print(f"Error in periodic cleanup: {str(e)}")
            
            await asyncio.sleep(3600)  # Run every hour

    asyncio.create_task(cleanup_old_files())






@app.post("/goodangel/api/v1/map-scene-video")
async def generate_sadtalker_video(
    video: UploadFile,
    audio: UploadFile,
    background_tasks: BackgroundTasks,
    enhancer: bool = False,
    size_of_image: int = 512,
    fps: int = 24,
    pose_style: Optional[int] = None,
    use_idle_mode: bool = False,
    blink_every: bool = True
):
    """
    Generate a talking avatar video using SadTalker from uploaded video and audio files.
    Returns the generated video file and cleans up afterwards.
    """
    video_path = None
    audio_path = None
    output_path = None
    
    try:
        # Validate inputs
        if not video.filename or not audio.filename:
            raise HTTPException(status_code=400, detail="Both video and audio files are required")
        
        # Save uploaded files
        video_path = await save_upload_file(video, UPLOAD_DIR)
        audio_path = await save_upload_file(audio, UPLOAD_DIR)
        
        # Generate unique output filename
        output_filename = f"{uuid.uuid4()}.mp4"
        output_path = os.path.join(SADTALKER_OUTPUT_DIR, output_filename)
        
        # Initialize SadTalker
        sadtalker = SadTalker(lazy_load=True)
        
        # Generate the video using SadTalker
        result = sadtalker.test2(
            source_image=video_path,
            driven_audio=audio_path
        )
        
        if not result or not os.path.exists(result):
            raise HTTPException(status_code=400, detail="Failed to generate video using SadTalker")
        
        # Copy the result to our output directory
        shutil.copy2(result, output_path)
        
        # Create a temporary copy for serving
        temp_output_path = f"{output_path}_temp.mp4"
        shutil.copy2(output_path, temp_output_path)
        
        # Schedule cleanup for all files
        background_tasks.add_task(
            cleanup_files,
            video_path,
            audio_path,
            output_path,
            temp_output_path,
            result  # Also cleanup the original SadTalker output
        )
        
        # Return the video file
        '''return FileResponse(
            path=temp_output_path,
            media_type="video/mp4",
            filename=f"sadtalker_{output_filename}",
            background=background_tasks
        )'''

        video_url = await upload_to_imagekit(video_path)
        return JSONResponse(content={"url": video_url})
        
    except Exception as e:
        # Clean up files immediately in case of error
        for file_path in [video_path, audio_path, output_path]:
            if file_path and os.path.exists(file_path):
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as cleanup_error:
                    print(f"Error cleaning up file {cleanup_error}: {str(cleanup_error)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Error generating video with SadTalker: {str(e)}"
        )
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)