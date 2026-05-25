import os
import uuid
import random
from datetime import datetime
import requests
from fastapi import FastAPI, Request, Form, HTTPException, status, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ---------- INITIALIZATION ----------
app = FastAPI(title="Village Identity & Document Server")

# CORS for mobile app / any client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebase RTDB endpoint
FIREBASE_DB_URL = "https://bindaas-715bf-default-rtdb.firebaseio.com"

# Upload directory for document images
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files to serve uploaded images
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ---------- MODELS ----------
class PinModel(BaseModel):
    pin: str

# ---------- HELPERS ----------
def generate_card_number():
    """Unique card ID like VIL-20250315-7891"""
    return f"VIL-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

def get_all_data():
    try:
        resp = requests.get(f"{FIREBASE_DB_URL}/villagers.json", timeout=10)
        return resp.json() or {} if resp.status_code == 200 else {}
    except:
        return {}

def get_member_by_id(member_id: str):
    try:
        resp = requests.get(f"{FIREBASE_DB_URL}/villagers/{member_id}.json", timeout=10)
        return resp.json() if resp.status_code == 200 else None
    except:
        return None

def update_member_data(member_id: str, data: dict):
    try:
        resp = requests.patch(f"{FIREBASE_DB_URL}/villagers/{member_id}.json", json=data, timeout=10)
        return resp.status_code == 200
    except:
        return False

def delete_member(member_id: str):
    try:
        resp = requests.delete(f"{FIREBASE_DB_URL}/villagers/{member_id}.json", timeout=10)
        return resp.status_code == 200
    except:
        return False

def save_document_file(member_id: str, doc_type: str, file: UploadFile):
    """Save uploaded file and return relative URL path"""
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    safe_filename = f"{member_id}/{doc_type}.{ext}"
    full_path = os.path.join(UPLOAD_DIR, safe_filename)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb") as buffer:
        buffer.write(file.file.read())
    return f"/uploads/{safe_filename}"

# ---------- APP API ENDPOINTS ----------
@app.get("/api/members")
async def get_all_members_list():
    db = get_all_data()
    members = []
    for key, val in db.items():
        if isinstance(val, dict):
            members.append({
                "id": key,
                "card_number": val.get("card_number", "N/A"),
                "name": val.get("name", "Unknown"),
                "has_pin": bool(val.get("pin"))
            })
    return members

@app.post("/api/members/{member_id}/verify")
async def verify_member_pin(member_id: str, data: PinModel):
    member = get_member_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.get("pin") == data.pin:
        return {
            "status": "Access Granted",
            "data": {
                "card_number": member.get("card_number"),
                "name": member.get("name"),
                "address": member.get("address"),
                "dob": member.get("dob"),
                "father": member.get("father"),
                "documents": {
                    "aadhaar": member.get("aadhaar", ""),
                    "pan": member.get("pan", ""),
                    "voter_id": member.get("voter_id", "")
                },
                "doc_images": {
                    "aadhaar": member.get("aadhaar_img", ""),
                    "pan": member.get("pan_img", ""),
                    "voter": member.get("voter_img", ""),
                    "photo": member.get("photo_img", "")
                }
            }
        }
    raise HTTPException(status_code=401, detail="Access Denied")

@app.post("/api/members/{member_id}/set-pin")
async def set_member_pin(member_id: str, data: PinModel):
    member = get_member_by_id(member_id)
    if not member or member.get("pin"):
        raise HTTPException(status_code=400, detail="Action prohibited")
    if update_member_data(member_id, {"pin": data.pin}):
        return {"message": "PIN set successfully"}
    raise HTTPException(status_code=500, detail="Update failed")

# ---------- METAL CARD GENERATION (now with unique number) ----------
@app.get("/api/members/{member_id}/card", response_class=HTMLResponse)
async def generate_metal_card(member_id: str):
    member = get_member_by_id(member_id)
    if not member:
        return HTMLResponse("<h1>Member Not Found</h1>", status_code=404)

    card_number = member.get("card_number", "VIL-XXXX-XXXX")
    masked_aadhaar = f"XXXX-XXXX-{member.get('aadhaar', '')[-4:]}" if len(member.get("aadhaar", "")) >= 4 else "XXXX-XXXX-XXXX"
    pan_display = member.get("pan", "N/A").upper()

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ID Card – {member.get('name')}</title>
        <style>
            body {{ background: #0a0a0f; font-family: 'Segoe UI', Roboto; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; }}
            .card {{ background: linear-gradient(145deg, #1a1c2a 0%, #12141e 100%); width: 450px; height: 290px; border-radius: 20px; padding: 24px; position: relative; border: 2px solid #d4af37; box-shadow: 0 20px 40px rgba(0,0,0,0.7); box-sizing: border-box; }}
            .chip {{ width: 45px; height: 35px; background: linear-gradient(135deg, #f1d77e, #b8942e); border-radius: 6px; margin-bottom: 15px; box-shadow: inset 0 1px 3px rgba(255,255,255,0.5); }}
            .card-id {{ font-family: 'Courier New', monospace; color: #d4af37; font-size: 22px; letter-spacing: 2px; position: absolute; top: 20px; right: 24px; font-weight: bold; }}
            .header {{ border-bottom: 1px solid rgba(212,175,55,0.3); padding-bottom: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; }}
            .header h3 {{ color: #d4af37; margin: 0; font-size: 16px; }}
            .header span {{ color: #aaa; font-size: 11px; }}
            .info {{ color: #f1f5f9; font-size: 14px; line-height: 1.6; }}
            .info strong {{ color: #ffffff; font-weight: 500; }}
            .bottom {{ position: absolute; bottom: 20px; left: 24px; right: 24px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px; }}
            .aadhaar-masked {{ color: #d4af37; font-family: 'Courier New', monospace; font-size: 16px; }}
            .pan {{ color: #94a3b8; font-size: 13px; }}
            .btn {{ margin-top: 25px; background: #0ea5e9; color: white; border: none; padding: 12px 30px; border-radius: 8px; font-weight: bold; cursor: pointer; }}
            .btn:hover {{ background: #0284c7; }}
            .view-docs {{ background: #10b981; margin-left: 10px; }}
            @media print {{ .btn {{ display: none; }} body {{ background: white; }} .card {{ box-shadow: none; border: 2px solid #000; }} }}
        </style>
    </head>
    <body>
        <div class="card" id="card">
            <div class="card-id">{card_number}</div>
            <div class="header">
                <h3>🏡 VILLAGE IDENTITY</h3>
                <span>RESIDENT</span>
            </div>
            <div class="chip"></div>
            <div class="info">
                <div><strong>NAME:</strong> {member.get('name').upper()}</div>
                <div><strong>FATHER:</strong> {member.get('father').upper()}</div>
                <div><strong>D.O.B:</strong> {member.get('dob')}</div>
                <div><strong>ADDRESS:</strong> {member.get('address')}</div>
            </div>
            <div class="bottom">
                <div class="aadhaar-masked">{masked_aadhaar}</div>
                <div class="pan">PAN: {pan_display}</div>
            </div>
        </div>
        <div>
            <button class="btn" onclick="window.print()">🖨️ Download Card</button>
            <button class="btn view-docs" onclick="window.open('/api/members/{member_id}/documents', '_blank')">📂 View Legal Documents</button>
        </div>
    </body>
    </html>
    """)

# ---------- DOCUMENT VIEWER (all uploaded images) ----------
@app.get("/api/members/{member_id}/documents", response_class=HTMLResponse)
async def view_member_documents(member_id: str):
    member = get_member_by_id(member_id)
    if not member:
        return HTMLResponse("<h1>Member Not Found</h1>", status_code=404)

    # Document image URLs stored in Firebase (relative paths)
    aadhaar_img = member.get("aadhaar_img")
    pan_img = member.get("pan_img")
    voter_img = member.get("voter_img")
    photo_img = member.get("photo_img")

    def doc_block(label, img_url):
        if not img_url:
            return f"<div class='doc-box empty'>{label}: Not uploaded</div>"
        return f"""
        <div class='doc-box'>
            <h4>{label}</h4>
            <img src="{img_url}" alt="{label}">
            <a href="{img_url}" download class="download-link">⬇ Download</a>
        </div>
        """

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Legal Documents – {member.get('name')}</title>
        <style>
            body {{ background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', sans-serif; padding: 20px; text-align: center; }}
            h1 {{ color: #d4af37; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 30px; max-width: 1000px; margin-left: auto; margin-right: auto; }}
            .doc-box {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 15px; }}
            .doc-box.empty {{ color: #94a3b8; font-style: italic; height: 150px; display: flex; align-items: center; justify-content: center; }}
            .doc-box img {{ max-width: 100%; max-height: 200px; border-radius: 8px; border: 1px solid #475569; }}
            .download-link {{ display: inline-block; margin-top: 8px; color: #38bdf8; text-decoration: none; }}
            .back-btn {{ margin-top: 25px; background: #475569; color: white; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; }}
        </style>
    </head>
    <body>
        <h1>📑 Legal Documents of {member.get('name')}</h1>
        <p>Card No: {member.get('card_number', 'N/A')}</p>
        <div class="grid">
            {doc_block("Aadhaar Card", aadhaar_img)}
            {doc_block("PAN Card", pan_img)}
            {doc_block("Voter ID", voter_img)}
            {doc_block("Photograph", photo_img)}
        </div>
        <button class="back-btn" onclick="history.back()">← Go Back</button>
    </body>
    </html>
    """)

# ---------- DARK PREMIUM CERTIFICATE ----------
@app.get("/api/members/{member_id}/certificate", response_class=HTMLResponse)
async def generate_certificate(member_id: str):
    member = get_member_by_id(member_id)
    if not member:
        return HTMLResponse("<h1>Member Not Found</h1>", status_code=404)

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Residence Certificate – {member.get('name')}</title>
        <style>
            body {{ background: #0a0a0f; font-family: 'Georgia', serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; }}
            .cert {{ background: #12141e; width: 780px; height: 540px; padding: 30px; border: 15px solid #1e293b; box-shadow: 0 20px 40px rgba(0,0,0,0.8); box-sizing: border-box; color: #f1f5f9; text-align: center; position: relative; }}
            .inner {{ border: 2px solid #d4af37; height: 100%; padding: 30px 20px; box-sizing: border-box; }}
            .badge {{ font-size: 50px; color: #d4af37; margin-bottom: 10px; }}
            h1 {{ font-size: 36px; color: #d4af37; margin: 0 0 10px 0; font-weight: normal; letter-spacing: 2px; }}
            .subtitle {{ color: #94a3b8; text-transform: uppercase; letter-spacing: 4px; font-size: 14px; margin-bottom: 25px; }}
            .name {{ font-size: 32px; font-weight: bold; color: #ffffff; border-bottom: 2px solid #d4af37; display: inline-block; padding: 0 30px 8px 30px; margin-bottom: 20px; }}
            .text {{ color: #cbd5e1; font-size: 16px; line-height: 1.6; max-width: 550px; margin: 0 auto 30px auto; }}
            .signatures {{ display: flex; justify-content: space-between; position: absolute; bottom: 50px; left: 10%; right: 10%; }}
            .sig {{ border-top: 1px solid #d4af37; padding-top: 5px; width: 180px; font-size: 13px; color: #94a3b8; text-transform: uppercase; font-family: sans-serif; }}
            .btn {{ margin-top: 30px; background: #10b981; color: white; border: none; padding: 12px 30px; border-radius: 8px; font-weight: bold; cursor: pointer; font-family: sans-serif; }}
            @media print {{ .btn {{ display: none; }} body {{ background: none; }} .cert {{ box-shadow: none; border: none; }} }}
        </style>
    </head>
    <body>
        <div class="cert">
            <div class="inner">
                <div class="badge">🏡</div>
                <h1>CERTIFICATE OF RESIDENCE</h1>
                <div class="subtitle">Official Village Record</div>
                <div class="name">{member.get('name')}</div>
                <div class="text">
                    Son/Daughter of <strong>{member.get('father')}</strong>, residing at <strong>{member.get('address')}</strong>,
                    is a verified resident of this community with record ID <strong>{member.get('card_number')}</strong>.
                </div>
                <div class="signatures">
                    <div class="sig">Village Registrar</div>
                    <div class="sig">Authorised Signatory</div>
                </div>
            </div>
        </div>
        <button class="btn" onclick="window.print()">📄 Download Certificate</button>
    </body>
    </html>
    """)

# ---------- ENHANCED ADMIN PANEL ----------
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    db = get_all_data()
    rows = ""
    for key, val in db.items():
        if isinstance(val, dict):
            card_no = val.get("card_number", "N/A")
            rows += f"""
            <tr>
                <td>{val.get('name', 'N/A')}</td>
                <td>{card_no}</td>
                <td>{val.get('address', 'N/A')}</td>
                <td style="text-align:center;">
                    <a href="/api/members/{key}/card" target="_blank" class="btn-sm card-btn">🪪 Card</a>
                    <a href="/api/members/{key}/certificate" target="_blank" class="btn-sm cert-btn">📄 Cert</a>
                    <a href="/admin/member/{key}" class="btn-sm edit-btn">✏️ Manage</a>
                    <a href="/admin/delete/{key}" onclick="return confirm('Delete this member?')" class="btn-sm del-btn">🗑️</a>
                </td>
            </tr>
            """
    if not rows:
        rows = "<tr><td colspan='4' style='text-align:center; color:gray;'>No residents registered.</td></tr>"

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Village Admin</title>
        <style>
            body {{ background: #0f172a; color: #f8fafc; font-family: sans-serif; padding: 20px; }}
            h1 {{ color: #38bdf8; text-align: center; }}
            .container {{ display: flex; gap: 20px; flex-wrap: wrap; max-width: 1200px; margin: auto; }}
            .card {{ background: #1e293b; border-radius: 12px; padding: 20px; flex: 1; min-width: 300px; }}
            .card h2 {{ color: #d4af37; margin-top: 0; }}
            label {{ display: block; margin-top: 10px; color: #cbd5e1; }}
            input {{ width: 100%; padding: 8px; background: #0f172a; border: 1px solid #475569; border-radius: 6px; color: white; margin-top: 4px; }}
            .btn {{ background: #0284c7; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; margin-top: 15px; width: 100%; }}
            .btn:hover {{ background: #0369a1; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ padding: 10px; border-bottom: 1px solid #334155; text-align: left; }}
            th {{ color: #38bdf8; }}
            .btn-sm {{ padding: 4px 12px; border-radius: 4px; text-decoration: none; font-size: 13px; margin: 0 2px; display: inline-block; }}
            .card-btn {{ background: #d4af37; color: black; }}
            .cert-btn {{ background: #10b981; color: white; }}
            .edit-btn {{ background: #6366f1; color: white; }}
            .del-btn {{ background: #ef4444; color: white; }}
        </style>
    </head>
    <body>
        <h1>🏡 Village Administration</h1>
        <div class="container">
            <div class="card">
                <h2>➕ Register New Resident</h2>
                <form action="/admin/add" method="POST">
                    <label>Full Name</label><input type="text" name="name" required>
                    <label>Address</label><input type="text" name="address" required>
                    <label>Date of Birth</label><input type="date" name="dob" required>
                    <label>Father's Name</label><input type="text" name="father" required>
                    <label>Aadhaar Number</label><input type="text" name="aadhaar">
                    <label>PAN Number</label><input type="text" name="pan">
                    <label>Voter ID</label><input type="text" name="voter_id">
                    <button type="submit" class="btn">Register</button>
                </form>
            </div>
            <div class="card" style="flex:2;">
                <h2>👥 Residents List</h2>
                <table>
                    <thead><tr><th>Name</th><th>Card No</th><th>Address</th><th style="text-align:center;">Actions</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """)

@app.post("/admin/add")
async def admin_add_member(
    name: str = Form(...), address: str = Form(...), dob: str = Form(...),
    father: str = Form(...), aadhaar: str = Form(None), pan: str = Form(None),
    voter_id: str = Form(None)
):
    card_number = generate_card_number()
    payload = {
        "card_number": card_number,
        "name": name,
        "address": address,
        "dob": dob,
        "father": father,
        "aadhaar": aadhaar or "",
        "pan": pan or "",
        "voter_id": voter_id or "",
        "pin": "",
        "aadhaar_img": "",
        "pan_img": "",
        "voter_img": "",
        "photo_img": ""
    }
    resp = requests.post(f"{FIREBASE_DB_URL}/villagers.json", json=payload, timeout=10)
    if resp.status_code == 200:
        return HTMLResponse("<script>alert('Member registered!'); window.location.href='/admin';</script>")
    raise HTTPException(status_code=500, detail="Firebase error")

@app.get("/admin/delete/{member_id}")
async def admin_delete_member(member_id: str):
    delete_member(member_id)
    return RedirectResponse("/admin", status_code=303)

@app.get("/admin/member/{member_id}", response_class=HTMLResponse)
async def admin_member_manage(member_id: str):
    member = get_member_by_id(member_id)
    if not member:
        return HTMLResponse("<h1>Member not found</h1>", status_code=404)

    # Build HTML for document images
    def img_preview(label, img_url):
        if not img_url:
            return f"<p>{label}: Not uploaded</p>"
        return f"<p>{label}: <img src='{img_url}' width='120' style='border-radius:6px;'></p>"

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>Manage {member.get('name')}</title>
        <style>
            body {{ background: #0f172a; color: #f8fafc; font-family: sans-serif; padding: 20px; max-width: 800px; margin: auto; }}
            h2 {{ color: #d4af37; }}
            label {{ display: block; margin-top: 12px; color: #94a3b8; }}
            input, textarea {{ width: 100%; padding: 8px; background: #1e293b; border: 1px solid #475569; border-radius: 6px; color: white; }}
            .btn {{ background: #0ea5e9; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; margin-top: 15px; }}
            .btn:hover {{ background: #0284c7; }}
            .upload-section {{ margin-top: 25px; }}
            hr {{ border-color: #334155; }}
            .back-link {{ color: #38bdf8; }}
        </style>
    </head>
    <body>
        <a href="/admin" class="back-link">← Back to Admin</a>
        <h2>✏️ Edit Member: {member.get('name')}</h2>
        <form action="/admin/member/{member_id}/edit" method="POST">
            <label>Name</label><input name="name" value="{member.get('name')}" required>
            <label>Address</label><input name="address" value="{member.get('address')}" required>
            <label>DOB</label><input name="dob" type="date" value="{member.get('dob')}" required>
            <label>Father</label><input name="father" value="{member.get('father')}" required>
            <label>Aadhaar No</label><input name="aadhaar" value="{member.get('aadhaar')}">
            <label>PAN No</label><input name="pan" value="{member.get('pan')}">
            <label>Voter ID</label><input name="voter_id" value="{member.get('voter_id')}">
            <button class="btn" type="submit">💾 Save Changes</button>
        </form>

        <div class="upload-section">
            <h3>📎 Upload Document Images</h3>
            <form action="/admin/member/{member_id}/upload/aadhaar" method="POST" enctype="multipart/form-data">
                <label>Aadhaar Image</label><input type="file" name="file" accept="image/*"><button class="btn">Upload</button>
            </form>
            <form action="/admin/member/{member_id}/upload/pan" method="POST" enctype="multipart/form-data">
                <label>PAN Image</label><input type="file" name="file" accept="image/*"><button class="btn">Upload</button>
            </form>
            <form action="/admin/member/{member_id}/upload/voter" method="POST" enctype="multipart/form-data">
                <label>Voter ID Image</label><input type="file" name="file" accept="image/*"><button class="btn">Upload</button>
            </form>
            <form action="/admin/member/{member_id}/upload/photo" method="POST" enctype="multipart/form-data">
                <label>Photograph</label><input type="file" name="file" accept="image/*"><button class="btn">Upload</button>
            </form>
        </div>

        <div style="margin-top:30px;">
            <h3>📸 Current Documents</h3>
            {img_preview("Aadhaar", member.get("aadhaar_img"))}
            {img_preview("PAN", member.get("pan_img"))}
            {img_preview("Voter ID", member.get("voter_img"))}
            {img_preview("Photo", member.get("photo_img"))}
        </div>
    </body>
    </html>
    """)

@app.post("/admin/member/{member_id}/edit")
async def admin_edit_member(
    member_id: str, name: str = Form(...), address: str = Form(...), dob: str = Form(...),
    father: str = Form(...), aadhaar: str = Form(""), pan: str = Form(""), voter_id: str = Form("")
):
    update_data = {
        "name": name, "address": address, "dob": dob, "father": father,
        "aadhaar": aadhaar, "pan": pan, "voter_id": voter_id
    }
    if update_member_data(member_id, update_data):
        return RedirectResponse(f"/admin/member/{member_id}", status_code=303)
    raise HTTPException(status_code=500, detail="Update failed")

@app.post("/admin/member/{member_id}/upload/{doc_type}")
async def admin_upload_document(member_id: str, doc_type: str, file: UploadFile = File(...)):
    allowed_types = ["aadhaar", "pan", "voter", "photo"]
    if doc_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid document type")
    url = save_document_file(member_id, doc_type, file)
    field = f"{doc_type}_img"
    if update_member_data(member_id, {field: url}):
        return RedirectResponse(f"/admin/member/{member_id}", status_code=303)
    raise HTTPException(status_code=500, detail="Failed to save file info")

# ---------- STARTUP ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)