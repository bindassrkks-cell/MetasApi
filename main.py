import requests
from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Village Data & Identity Generator API")

# CORS Configuration for Android App Connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebase Database Link
FIREBASE_DB_URL = "https://bindaas-715bf-default-rtdb.firebaseio.com"

class PinModel(BaseModel):
    pin: str

# --- DATA BASE RETRIEVAL HELPERS ---
def get_all_data():
    try:
        response = requests.get(f"{FIREBASE_DB_URL}/villagers.json", timeout=10)
        return response.json() or {} if response.status_code == 200 else {}
    except Exception:
        return {}

def get_member_by_id(member_id: str):
    try:
        response = requests.get(f"{FIREBASE_DB_URL}/villagers/{member_id}.json", timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception:
        return None

def update_member_data(member_id: str, data: dict):
    try:
        response = requests.patch(f"{FIREBASE_DB_URL}/villagers/{member_id}.json", json=data, timeout=10)
        return response.status_code == 200
    except Exception:
        return False


# --- 📱 APP COMPATIBLE API ENDPOINTS ---

@app.get("/api/members")
async def get_all_members_list():
    db_data = get_all_data()
    members_list = []
    for key, value in db_data.items():
        if isinstance(value, dict):
            members_list.append({
                "id": key,
                "name": value.get("name", "Unknown"),
                "has_pin": bool(value.get("pin"))
            })
    return members_list

@app.post("/api/members/{member_id}/verify")
async def verify_member_pin(member_id: str, data: PinModel):
    member = get_member_by_id(member_id)
    if not member: raise HTTPException(status_code=404, detail="Member not found")
    if member.get("pin") == data.pin:
        return {
            "status": "Access Granted",
            "data": {
                "name": member.get("name"),
                "address": member.get("address"),
                "dob": member.get("dob"),
                "father": member.get("father"),
                "documents": {
                    "aadhaar": member.get("aadhaar", ""),
                    "pan": member.get("pan", ""),
                    "voter_id": member.get("voter_id", "")
                }
            }
        }
    raise HTTPException(status_code=401, detail="Access Denied")

@app.post("/api/members/{member_id}/set-pin")
async def set_member_pin(member_id: str, data: PinModel):
    member = get_member_by_id(member_id)
    if not member or member.get("pin"): raise HTTPException(status_code=400, detail="Action prohibited")
    if update_member_data(member_id, {"pin": data.pin}): return {"message": "Success"}
    raise HTTPException(status_code=500, detail="Failed")


# --- 🪪 SERVER GRAPHICS GENERATION ENGINE (CARD & CERTIFICATE) ---

@app.get("/api/members/{member_id}/card", response_class=HTMLResponse)
async def generate_metal_card(member_id: str):
    """Generates an ultra-premium Matte Black & Gold Metallic Identity Card Layout"""
    member = get_member_by_id(member_id)
    if not member: return "<h1>Member Not Found</h1>"
    
    # Secure display formatting for document fields
    raw_aadhaar = member.get("aadhaar", "")
    masked_aadhaar = f"XXXX-XXXX-{raw_aadhaar[-4:]}" if len(raw_aadhaar) >= 4 else "XXXX-XXXX-XXXX"
    pan_display = member.get("pan", "N/A").upper()

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Premium Identity Card - {member.get('name')}</title>
        <style>
            body {{ background-color: #090A0F; font-family: 'Segoe UI', Roboto, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; }}
            .card-container {{ background: linear-gradient(135deg, #15161e 0%, #222431 100%); width: 450px; height: 270px; border-radius: 18px; position: relative; padding: 24px; box-shadow: 0 20px 40px rgba(0,0,0,0.6); border: 2px solid #d4af37; box-sizing: border-box; overflow: hidden; }}
            .card-container::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(rgba(255,255,255,0.03), transparent); pointer-events: none; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(212,175,55,0.3); padding-bottom: 10px; margin-bottom: 15px; }}
            .header h3 {{ color: #d4af37; margin: 0; font-size: 18px; letter-spacing: 1px; font-weight: 600; }}
            .header span {{ color: #8e8e93; font-size: 11px; font-weight: bold; }}
            .chip {{ width: 42px; height: 32px; background: linear-gradient(135deg, #e5c158 0%, #b89734 100%); border-radius: 6px; margin-bottom: 12px; position: relative; box-shadow: inset 0 1px 2px rgba(255,255,255,0.4); }}
            .info-grid {{ display: grid; grid-template-columns: 1f; gap: 6px; color: #f8fafc; }}
            .info-row {{ font-size: 13px; font-weight: 300; color: #cbd5e1; }}
            .info-row strong {{ color: #ffffff; font-weight: 500; margin-right: 4px; }}
            .footer-metrics {{ position: absolute; bottom: 20px; left: 24px; right: 24px; display: flex; justify-content: space-between; align-items: flex-end; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 8px; }}
            .id-number {{ color: #d4af37; font-family: 'Courier New', monospace; font-size: 18px; font-weight: bold; letter-spacing: 2px; }}
            .pan-number {{ color: #a1a1aa; font-size: 12px; font-weight: 500; }}
            .action-area {{ margin-top: 30px; }}
            .btn {{ background: #0A84FF; color: white; border: none; padding: 12px 28px; font-size: 15px; font-weight: bold; border-radius: 10px; cursor: pointer; box-shadow: 0 4px 12px rgba(10,132,255,0.3); transition: transform 0.2s; }}
            .btn:hover {{ transform: scale(1.03); }}
            @media print {{ .action-area {{ display: none; }} body {{ background: none; }} .card-container {{ box-shadow: none; }} }}
        </style>
    </head>
    <body>
        <div class="card-container" id="identity-card">
            <div class="header">
                <h3>VILLAGE METRIC CARD</h3>
                <span>RESIDENT RESIDENCE</span>
            </div>
            <div class="chip"></div>
            <div class="info-grid">
                <div class="info-row"><strong>NAME:</strong> {member.get('name').upper()}</div>
                <div class="info-row"><strong>FATHER:</strong> {member.get('father').upper()}</div>
                <div class="info-row"><strong>D.O.B:</strong> {member.get('dob')}</div>
                <div class="info-row"><strong>ADDRESS:</strong> {member.get('address')}</div>
            </div>
            <div class="footer-metrics">
                <div class="id-number">{masked_aadhaar}</div>
                <div class="pan-number">PAN: {pan_display}</div>
            </div>
        </div>
        <div class="action-area">
            <button class="btn" onclick="window.print()">Download Metal Card (PDF)</button>
        </div>
    </body>
    </html>
    """

@app.get("/api/members/{member_id}/certificate", response_class=HTMLResponse)
async def generate_certificate(member_id: str):
    """Generates an Official, Elegant Village Membership Certificate with borders and seals"""
    member = get_member_by_id(member_id)
    if not member: return "<h1>Member Not Found</h1>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Official Certificate - {member.get('name')}</title>
        <style>
            body {{ background-color: #0f172a; font-family: 'Georgia', serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; }}
            .cert-container {{ background-color: #ffffff; width: 750px; height: 530px; padding: 40px; border: 20px solid #1e293b; box-shadow: 0 25px 50px rgba(0,0,0,0.5); position: relative; box-sizing: border-box; color: #1e293b; text-align: center; }}
            .inner-border {{ border: 2px solid #d4af37; height: 100%; width: 100%; box-sizing: border-box; padding: 30px; position: relative; }}
            .badge {{ font-size: 45px; color: #d4af37; margin-bottom: 5px; }}
            h1 {{ font-size: 38px; margin: 0 0 10px 0; color: #1e293b; font-weight: normal; letter-spacing: 1px; }}
            h4 {{ font-size: 14px; text-transform: uppercase; letter-spacing: 4px; margin: 0 0 25px 0; color: #64748b; }}
            .certify-text {{ font-size: 18px; font-style: italic; color: #475569; margin-bottom: 10px; }}
            .member-name {{ font-size: 32px; font-weight: bold; color: #0f172a; border-bottom: 2px solid #cbd5e1; display: inline-block; padding: 0 30px 5px 30px; margin-bottom: 20px; font-family: sans-serif; }}
            .body-text {{ font-size: 16px; line-height: 26px; color: #334155; max-width: 580px; margin: 0 auto 40px auto; }}
            .signature-section {{ display: flex; justify-content: space-between; width: 80%; margin: 0 auto; position: absolute; bottom: 45px; left: 10%; right: 10%; }}
            .sig-block {{ width: 180px; border-top: 1px solid #94a3b8; padding-top: 6px; font-size: 13px; font-weight: bold; text-transform: uppercase; color: #475569; font-family: sans-serif; }}
            .action-area {{ margin-top: 30px; }}
            .btn {{ background: #10B981; color: white; border: none; padding: 12px 28px; font-size: 15px; font-weight: bold; border-radius: 10px; cursor: pointer; box-shadow: 0 4px 12px rgba(16,185,129,0.3); font-family: sans-serif; }}
            @media print {{ .action-area {{ display: none; }} body {{ background: none; }} .cert-container {{ box-shadow: none; }} }}
        </style>
    </head>
    <body>
        <div class="cert-container">
            <div class="inner-border">
                <div class="badge">🏡</div>
                <h1>CERTIFICATE OF RESIDENCE</h1>
                <h4>Official Village Record</h4>
                
                <p class="certify-text">This document officially recognizes</p>
                <div class="member-name">{member.get('name')}</div>
                
                <p class="body-text">
                    Son/Daughter of <strong>{member.get('father')}</strong>, residing permanently at 
                    <strong>{member.get('address')}</strong>. Registered under record index identifier code 
                    <em>{member_id}</em> as a verified resident holding full community compliance.
                </p>
                
                <div class="signature-section">
                    <div class="sig-block">Village Registrar</div>
                    <div class="sig-block">Authorized Signatory</div>
                </div>
            </div>
        </div>
        <div class="action-area">
            <button class="btn" onclick="window.print()">Download Certificate (PDF)</button>
        </div>
    </body>
    </html>
    """


# --- 🖥️ MANAGEMENT DASHBOARD (WITH VIEW & GENERATION REDIRECTS) ---

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    db_data = get_all_data()
    
    # Building live rows with direct view/download actions
    table_rows = ""
    for key, value in db_data.items():
        if isinstance(value, dict):
            table_rows += f"""
            <tr>
                <td>{value.get('name', 'N/A')}</td>
                <td>{value.get('address', 'N/A')}</td>
                <td>
                    <a href="/api/members/{key}/card" target="_blank" class="action-link card-link">🪪 Identity Card</a>
                    <a href="/api/members/{key}/certificate" target="_blank" class="action-link cert-link">📄 Certificate</a>
                </td>
            </tr>
            """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Village Admin Control Engine</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px; display: flex; flex-direction: column; align-items: center; }}
            .container {{ display: flex; gap: 24px; width: 100%; max-width: 1100px; margin-top: 20px; }}
            .card {{ background: #1e293b; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); flex: 1; height: fit-content; }}
            .list-card {{ flex: 1.5; }}
            h2 {{ text-align: center; color: #38bdf8; margin-top:0; }}
            label {{ display: block; margin: 10px 0 5px; color: #cbd5e1; font-size: 14px; }}
            input {{ width: 100%; padding: 10px; background: #0f172a; border: 1px solid #475569; border-radius: 6px; color: white; box-sizing: border-box; margin-bottom: 5px; }}
            .btn {{ width: 100%; background: #0284c7; color: white; border: none; padding: 12px; font-weight: bold; border-radius: 6px; cursor: pointer; margin-top: 15px; }}
            .btn:hover {{ background: #0369a1; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #334155; font-size: 14px; }}
            th {{ color: #38bdf8; background-color: #0f172a; }}
            .action-link {{ padding: 6px 12px; border-radius: 6px; font-size: 12px; text-decoration: none; font-weight: bold; margin-right: 5px; display: inline-block; }}
            .card-link {{ background-color: rgba(212,175,55,0.15); color: #d4af37; border: 1px solid #d4af37; }}
            .cert-link {{ background-color: rgba(16,185,129,0.15); color: #10b981; border: 1px solid #10b981; }}
        </style>
    </head>
    <body>
        <h1>🏡 Village Management & Identity Engine</h1>
        <div class="container">
            <div class="card">
                <h2>📝 New Entry</h2>
                <form action="/admin/add" method="POST">
                    <label>Full Name</label><input type="text" name="name" required>
                    <label>Address</label><input type="text" name="address" required>
                    <label>Date of Birth</label><input type="date" name="dob" required>
                    <label>Father's Name</label><input type="text" name="father" required>
                    <label>Aadhaar Number</label><input type="text" name="aadhaar">
                    <label>PAN Card</label><input type="text" name="pan">
                    <label>Voter ID</label><input type="text" name="voter_id">
                    <button type="submit" class="btn">Save & Register Member</button>
                </form>
            </div>
            
            <div class="card list-card">
                <h2>📋 Registered Residents</h2>
                <table>
                    <thead>
                        <tr><th>Name</th><th>Address</th><th>Identity Docs & Assets</th></tr>
                    </thead>
                    <tbody>
                        {table_rows if table_rows else "<tr><td colspan='3' style='text-align:center; color:gray;'>No records captured.</td></tr>"}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """

@app.post("/admin/add")
async def admin_add_member(
    name: str = Form(...), address: str = Form(...), dob: str = Form(...), father: str = Form(...),
    aadhaar: str = Form(None), pan: str = Form(None), voter_id: str = Form(None)
):
    payload = {
        "name": name, "address": address, "dob": dob, "father": father,
        "aadhaar": aadhaar if aadhaar else "", "pan": pan if pan else "", "voter_id": voter_id if voter_id else "",
        "pin": "" 
    }
    response = requests.post(f"{FIREBASE_DB_URL}/villagers.json", json=payload, timeout=10)
    if response.status_code == 200:
        return HTMLResponse("<script>alert('Member Registered Successfully!'); window.location.href='/admin';</script>")
    raise HTTPException(status_code=500, detail="Firebase insertion error")
