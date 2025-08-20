from fastapi import FastAPI, Depends, HTTPException, Query, Body
from typing import Optional, List
from datetime import datetime
from models import Complaint, ComplaintCreate, User
from complaint_storage import load_complaints, save_complaints
from auth_utils import get_current_user, require_role
from user_routes import router as user_router

app = FastAPI(title="Complaint Management API")

# include user routes at /users
app.include_router(user_router, prefix="/users")
complaints = []


# -------------------------
# Public endpoint (no auth)
# -------------------------
@app.get("/complaints", response_model=List[Complaint])
def public_get_complaint(ticket: Optional[int] = Query(None), email: Optional[str] = Query(None)):
    """
    Public: must provide both ticket and email to look up a complaint.
    If Authorization header present, the protected endpoints below will shadow this route for logged-in users.
    """
    if ticket is None or email is None:
        raise HTTPException(status_code=400, detail="Both ticket and email are required for public lookup")
    complaints = load_complaints()
    found = [c for c in complaints if c.id == ticket and c.customer.email.lower() == email.lower()]
    if not found:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return found


# -------------------------
# Customer (logged in)
# -------------------------
@app.get("/user/complaints", response_model=List[Complaint])
def get_customer_complaints(
    ticket: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_role("customer"))
):
    """
    Customer can:
    - GET /user/complaints  -> list their complaints
    - GET /user/complaints?ticket= -> get their complaint by id
    - GET /user/complaints?status=open
    """
    complaints = load_complaints()
    user_email = current_user.email.lower()
    complaints = [c for c in complaints if c.customer.email.lower() == user_email]

    if ticket is not None:
        complaints = [c for c in complaints if c.id == ticket]
        if not complaints:
            raise HTTPException(status_code=404, detail="Complaint not found")
        return complaints

    if status:
        complaints = [c for c in complaints if c.status.lower() == status.lower()]

    return complaints


@app.get("/complaints/me", response_model=List[Complaint])
def get_my_complaints(current_user: User = Depends(require_role("customer"))):
    """alias to list customer's complaints"""
    complaints = load_complaints()
    return [c for c in complaints if c.customer.email.lower() == current_user.email.lower()]


@app.post("/complaints", response_model=Complaint, status_code=201)
def create_complaint(new_complaint: ComplaintCreate, current_user: User = Depends(require_role("customer"))):
    """
    Customer creates a complaint. The customer object in payload is validated,
    but we enforce that the customer.email in the payload matches the logged-in user's email.
    """
    if new_complaint.customer.email.lower() != current_user.email.lower():
        raise HTTPException(status_code=403, detail="You can only create complaints for your own account")

    complaints = load_complaints()
    new_id = max((c.id for c in complaints), default=0) + 1
    complaint = Complaint(
        id=new_id,
        title=new_complaint.title,
        description=new_complaint.description,
        status="open",
        customer=new_complaint.customer,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    complaints.append(complaint)
    save_complaints(complaints)
    return complaint


@app.put("/complaints/{complaint_id}", response_model=Complaint)
def update_customer_complaint(
    complaint_id: int,
    updated_data: ComplaintCreate,
    current_user: User = Depends(require_role("customer"))
):
    complaints = load_complaints()
    for idx, c in enumerate(complaints):
        if c.id == complaint_id:
            if c.customer.email.lower() != current_user.email.lower():
                raise HTTPException(status_code=403, detail="You can only update your own complaints")
            # Update allowed fields
            c.title = updated_data.title
            c.description = updated_data.description
            c.updated_at = datetime.utcnow()
            complaints[idx] = c
            save_complaints(complaints)
            return c
    raise HTTPException(status_code=404, detail="Complaint not found")


@app.delete("/complaints/{complaint_id}")
def delete_customer_complaint(
    complaint_id: int,
    current_user: User = Depends(require_role("customer"))
):
    complaints = load_complaints()
    for idx, c in enumerate(complaints):
        if c.id == complaint_id and c.customer.email.lower() == current_user.email.lower():
            complaints.pop(idx)
            save_complaints(complaints)
            return {"message": f"Complaint {complaint_id} deleted"}
    raise HTTPException(status_code=404, detail="Complaint not found or not yours")


# -------------------------
# Admin endpoints
# -------------------------
@app.get("/admin/complaints", response_model=List[Complaint])
def admin_list_all_complaints(current_user: User = Depends(require_role("admin"))):
    return load_complaints()


@app.get("/admin/complaints/search", response_model=List[Complaint])
def admin_get_by_ticket_or_status(
    ticket: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_role("admin"))
):
    complaints = load_complaints()
    if ticket is not None:
        found = [c for c in complaints if c.id == ticket]
        if not found:
            raise HTTPException(status_code=404, detail="Complaint not found")
        return found
    if status is not None:
        return [c for c in complaints if c.status.lower() == status.lower()]
    return complaints


@app.post("/admin/complaints", response_model=Complaint)
def admin_create_complaint(new_complaint: ComplaintCreate, current_user: User = Depends(require_role("admin"))):
    complaints = load_complaints()
    new_id = max((c.id for c in complaints), default=0) + 1
    complaint = Complaint(
        id=new_id,
        title=new_complaint.title,
        description=new_complaint.description,
        status="open",
        customer=new_complaint.customer,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    complaints.append(complaint)
    save_complaints(complaints)
    return complaint


@app.put("/admin/complaints/{complaint_id}", response_model=Complaint)
def admin_update_complaint(
    complaint_id: int,
    updated_data: ComplaintCreate,
    current_user: User = Depends(require_role("admin"))
):
    complaints = load_complaints()
    for idx, c in enumerate(complaints):
        if c.id == complaint_id:
            c.title = updated_data.title
            c.description = updated_data.description
            c.updated_at = datetime.utcnow()
            complaints[idx] = c
            save_complaints(complaints)
            return c
    raise HTTPException(status_code=404, detail="Complaint not found")


@app.delete("/admin/complaints/{complaint_id}")
def admin_delete_complaint(complaint_id: int, current_user: User = Depends(require_role("admin"))):
    complaints = load_complaints()
    for idx, c in enumerate(complaints):
        if c.id == complaint_id:
            complaints.pop(idx)
            save_complaints(complaints)
            return {"message": f"Complaint {complaint_id} deleted"}
    raise HTTPException(status_code=404, detail="Complaint not found")


@app.put("/admin/complaints/{complaint_id}/resolve", response_model=Complaint)
def admin_resolve_complaint(
    complaint_id: int,
    payload: dict = Body(...),
    current_user: User = Depends(require_role("admin"))
):
    """
    payload example:
    {
      "type": "closed",
      "comment": "no comment"
    }
    """
    complaints = load_complaints()
    for idx, c in enumerate(complaints):
        if c.id == complaint_id:
            if c.status.lower() == "closed":
                raise HTTPException(status_code=400, detail="Complaint already closed")
            c.status = payload.get("type", "closed")
            c.comment = payload.get("comment")
            c.updated_at = datetime.utcnow()
            complaints[idx] = c
            save_complaints(complaints)
            return c
    raise HTTPException(status_code=404, detail="Complaint not found")



# -------------------------
# helper route to inspect current user (for testing)
# -------------------------
@app.get("/me")
def who_am_i(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "username": current_user.username, "role": current_user.role}
