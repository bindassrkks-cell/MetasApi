import os
import io
import zipfile
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI(
    title="Premium Structural Automation Engine",
    description="FastAPI cloud parser providing proxy extraction pipelines and metadata listing",
    version="4.4.0"
)

# Environment Keys configuration via Render Dashboard
TG_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")
TG_API_BASE = f"https://api.telegram.org/bot{TG_BOT_TOKEN}"

class RepackPayload(BaseModel):
    telegram_file_ids: List[str]
    output_archive_name: str

@app.get("/")
async def framework_status():
    """
    Continuous keep-alive route target for cloud deployment environments.
    """
    return {
        "engine_status": "RUNNING",
        "version": "4.4.0-Production",
        "storage_bridge": "Telegram Cloud Object Stream Active"
    }

@app.post("/api/v4/patch/unpack")
async def unpack_archive_matrix(
    unpack_mode: int = Query(..., description="1: Folder Wise, 2: Only Files Flat"),
    file: UploadFile = File(...)
):
    """
    Unbundles uploaded archives, generates structural maps, and formats contents into JSON vectors.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid node reference target.")

    try:
        contents = await file.read()
        archive_stream = io.BytesIO(contents)
        discovered_files_metadata: List[Dict] = []
        
        if zipfile.is_zipfile(archive_stream):
            archive_stream.seek(0)
            with zipfile.ZipFile(archive_stream, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    if member.is_dir():
                        continue
                    
                    filename_output = member.filename if unpack_mode == 1 else os.path.basename(member.filename)
                    if not filename_output:
                        continue
                        
                    raw_data = zip_ref.read(member.filename)
                    
                    discovered_files_metadata.append({
                        "file_path": filename_output,
                        "size_bytes": len(raw_data),
                        "content_preview_hex": raw_data[:16].hex().upper()
                    })
        else:
            raise HTTPException(status_code=422, detail="Unsupported format stream layout. Expecting standard package archive.")

        return JSONResponse(
            status_code=200,
            content={
                "status": "UNPACK_COMPLETE",
                "target_package": file.filename,
                "extraction_mode_applied": "Folder Wise Structure" if unpack_mode == 1 else "Flat File Stream Extraction",
                "total_nodes_found": len(discovered_files_metadata),
                "payload_manifest": discovered_files_metadata
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal pipeline data error: {str(e)}")

@app.post("/api/v4/patch/search")
async def search_text_string_pattern(
    search_query: str = Query(..., description="Target string pattern to identify inside file layers"),
    file: UploadFile = File(...)
):
    """
    Traverses internal archive filenames asynchronously.
    """
    try:
        contents = await file.read()
        archive_stream = io.BytesIO(contents)
        matched_occurrences: List[str] = []

        if zipfile.is_zipfile(archive_stream):
            archive_stream.seek(0)
            with zipfile.ZipFile(archive_stream, 'r') as zip_ref:
                for name in zip_ref.namelist():
                    if search_query.lower() in name.lower():
                        matched_occurrences.append(f"File Path Anchor Match: {name}")
        
        return {
            "query": search_query,
            "matches_found": len(matched_occurrences),
            "results": matched_occurrences
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search workspace failure: {str(e)}")

@app.post("/api/v4/patch/repack")
async def repack_nodes_into_archive(payload: RepackPayload):
    """
    Rebundles file pieces back into a structural container.
    """
    if TG_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        raise HTTPException(status_code=500, detail="Cloud variables infrastructure map unconfigured.")

    try:
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for fid in payload.telegram_file_ids:
                path_res = requests.post(f"{TG_API_BASE}/getFile", data={"file_id": fid}, timeout=20)
                if path_res.ok and path_res.json().get("ok"):
                    file_path = path_res.json()["result"]["file_path"]
                    download_url = f"https://api.telegram.org/file/bot{TG_BOT_TOKEN}/{file_path}"
                    
                    file_bytes = requests.get(download_url, timeout=60).content
                    pure_name = file_path.split("/")[-1]
                    
                    zip_file.writestr(pure_name, file_bytes)

        zip_buffer.seek(0)
        
        upload_url = f"{TG_API_BASE}/sendDocument"
        files = {'document': (payload.output_archive_name, zip_buffer.getvalue(), 'application/zip')}
        data = {'chat_id': TG_CHAT_ID, 'caption': "Repacked package structure module deployment."}
        
        tg_res = requests.post(upload_url, data=data, files=files, timeout=120).json()
        
        if not tg_res.get("ok"):
            raise HTTPException(status_code=400, detail="Telegram cloud destination write failure.")

        return {
            "status": "REPACK_SUCCESS",
            "archive_identifier": payload.output_archive_name,
            "output_telegram_file_id": tg_res["result"]["document"]["file_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Repacking computation failure: {str(e)}")
