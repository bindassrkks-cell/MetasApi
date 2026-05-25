import requests
from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Village Data Passcode API")

# CORS Enable karein taaki aapka android/iOS app isse bina kisi dikkat ke connect ho sake
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebase Realtime Database URL
FIREBASE_DB_URL = "https://bindaas-715bf-default-rtdb.firebaseio.com"

# --- PYDANTIC SCHEMAS FOR APP INTERACTION ---
class PinModel(BaseModel):
    pin: str

# --- HELPER FUNCTIONS ---
def get_all_data():
    response = requests.get(f"{FIREBASE_DB_URL}/villagers.json")
    return response.json() or {} if response.status_code == 200 else {}

def get_member_by_id(member_id: str):
    response = requests.get(f"{FIREBASE_DB_URL}/villagers/{member_id}.json")
    return response.json() if response.status_code == 200 else None

def update_member_data(member_id: str, data: dict):
    response = requests.patch(f"{FIREBASE_DB_URL}/villagers/{member_id}.json", json=data)
    return response.status_code == 200


# --- 🚀 APP COUPLING API ENDPOINTS ---

@app.get("/api/members")
async def get_all_members_list():
    """
    1. App Open hote hi is url ko call karein.
    Yeh village ke sabhi members ki list dega (Sirf Name aur ID, koi sensitive data nahi).
    Isme 'has_pin' batayega ki member ne passcode lock lagaya hai ya nahi.
    """
    db_data = get_all_data()
    members_list = []
    
    for key, value in db_data.items():
        members_list.append({
            "id": key,
            "name": value.get("name"),
            "has_pin": bool(value.get("pin"))  # True agar passcode set hai, False agar nahi hai
        })
    return members_list


@app.post("/api/members/{member_id}/verify")
async def verify_member_pin(member_id: str, data: PinModel):
    """
    2. Agar 'has_pin' True hai, toh app me 4-digit prompt kholein aur is endpoint par POST request bhejein.
    Sahi PIN hone par 'Access Granted' message aur Full Details milengi.
    """
    member = get_member_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    input_pin = data.pin
    if not (input_pin.isdigit() and len(input_pin) == 4):
        raise HTTPException(status_code=400, detail="PIN must be exactly 4 digits")
        
    db_pin = member.get("pin")
    
    if db_pin == input_pin:
        # Access Granted: Pura data return karega
        return {
            "status": "Access Granted",
            "data": {
                "name": member.get("name"),
                "address": member.get("address"),
                "dob": member.get("dob"),
                "father": member.get("father"),
                "documents": {
                    "aadhaar": member.get("aadhaar"),
                    "pan": member.get("pan"),
                    "voter_id": member.get("voter_id")
                }
            }
        }
    else:
        raise HTTPException(status_code=401, detail="Access Denied: Incorrect Passcode")


@app.post("/api/members/{member_id}/set-pin")
async def set_member_pin(member_id: str, data: PinModel):
    """
    3. Agar 'has_pin' False hai, toh app me 'Set Passcode' ka option dein aur is endpoint par 4-digit pin bhejein.
    """
    member = get_member_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
        
    # Check if PIN is already set
    if member.get("pin"):
        raise HTTPException(status_code=400, detail="Passcode is already configured for this user")
        
    new_pin = data.pin
    if not (new_pin.isdigit() and len(new_pin) == 4):
        raise HTTPException(status_code=400, detail="PIN must be exactly 4 digits")
        
    success = update_member_data(member_id, {"pin": new_pin})
    if success:
        return {"message": "Passcode set successfully! Data is now locked."}
    raise HTTPException(status_code=500, detail="Failed to update passcode in database")


# --- 🖥️ ADMIN PANEL FOR DATA ENTRY (/admin) ---

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    """Admin interface jahan se aap villagers ka data system me entry karenge"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Village Admin Panel</title>
        <style>
            body { font-family: -apple-system, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px; display: flex; justify-content: center; }
            .card { background: #1e293b; padding: 30px; border-radius: 12px; width: 100%; max-width: 500px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
            h2 { text-align: center; color: #38bdf8; margin-top:0; }
            label { display: block; margin: 10px 0 5px; color: #cbd5e1; font-size: 14px; }
            input { width: 100%; padding: 10px; background: #0f172a; border: 1px solid #475569; border-radius: 6px; color: white; box-sizing: border-box; }
            input:focus { border-color: #38bdf8; outline: none; }
            .btn { width: 100%; background: #0284c7; color: white; border: none; padding: 12px; font-weight: bold; border-radius: 6px; cursor: pointer; margin-top: 20px; }
            .btn:hover { background: #0369a1; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>📝 Add New Villager Member</h2>
            <form action="/admin/add" method="POST">
                <label>Full Name</label>
                <input type="text" name="name" required placeholder="e.g. Raja Ansari">
                
                <label>Address</label>
                <input type="text" name="address" required placeholder="Village, Block, Dist">
                
                <label>Date of Birth</label>
                <input type="date" name="dob" required>
                
                <label>Father's Name</label>
                <input type="text" name="father" required>
                
                <label>Aadhaar Number</label>
                <input type="text" name="aadhaar" placeholder="12 Digit Aadhaar No">
                
                <label>PAN Card</label>
                <input type="text" name="pan" placeholder="PAN Card No">
                
                <label>Voter ID</label>
                <input type="text" name="voter_id" placeholder="Voter ID No">
                
                <button type="submit" class="btn">Save Member to Firebase</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/admin/add")
async def admin_add_member(
    name: str = Form(...),
    address: str = Form(...),
    dob: str = Form(...),
    father: str = Form(...),
    aadhaar: str = Form(None),
    pan: str = Form(None),
    voter_id: str = Form(None)
):
    payload = {
        "name": name,
        "address": address,
        "dob": dob,
        "father": father,
        "aadhaar": aadhaar if aadhaar else "",
        "pan": pan if pan else "",
        "voter_id": voter_id if voter_id else "",
        "pin": ""  # Shuruat me koi passcode nahi hoga, app se set hoga
    }
    
    response = requests.post(f"{FIREBASE_DB_URL}/villagers.json", json=payload)
    if response.status_code == 200:
        return HTMLResponse("<script>alert('Member Added!'); window.location.href='/admin';</script>")
    raise HTTPException(status_code=500, detail="Firebase insertion failed")
