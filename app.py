from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

DB = "Clinic.db"

def db():
    return sqlite3.connect(DB)

# ========= UNIVERSAL CRUD ==============
def load_table(table, keyword=None, search_fields=None): # MODIFIED: Added keyword and search_fields
    conn = db()
    query = f"SELECT * FROM {table} WHERE deleted = 0"
    params = []

    if keyword and search_fields:
        # Construct a WHERE clause to search across multiple specified fields
        search_conditions = [f"{field} LIKE ?" for field in search_fields]
        query += " AND (" + " OR ".join(search_conditions) + ")"
        # Add a wildcarded keyword parameter for each search field
        params.extend([f"%{keyword}%"] * len(search_fields))

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows

def get_record(table, pk, value):
    conn = db()
    row = conn.execute(f"SELECT * FROM {table} WHERE {pk}=?", (value,)).fetchone()
    conn.close()
    return row

def insert_record(table, fields, values):
    conn = db()
    conn.execute(
        f"INSERT INTO {table} ({','.join(fields)}) VALUES ({','.join(['?'] * len(values))})",
        values
    )
    conn.commit()
    conn.close()

def update_record(table, fields, values, pk, idval):
    conn = db()
    conn.execute(
        f"UPDATE {table} SET {', '.join([f + '=?' for f in fields])} WHERE {pk}=?",
        values + [idval]
    )
    conn.commit()
    conn.close()

def delete_record(table, pk, idval):
    conn = db()
    conn.execute(f"UPDATE {table} SET deleted = 1 WHERE {pk}=?", (idval,))
    conn.commit()
    conn.close()

def id_exists(table, pk, value): # NEW HELPER FUNCTION
    conn = db()
    # Check if ANY record (deleted or not) exists with this PK
    count = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {pk}=?", (value,)).fetchone()[0]
    conn.close()
    return count > 0

# ========== ROUTES PER ENTITY ==========

# --------- Veterinarian Module ----------
@app.route("/vet")
def vet_list():
    fields = ["vetID","vetFName","vetLName","vetAddress","vetSpecial"]
    search_fields = ["vetID", "vetFName", "vetLName"] # Fields to search in
    keyword = request.args.get("keyword", "") # Get the search keyword from the URL

    # MODIFIED: Pass keyword and search_fields to load_table
    rows = load_table("Veterinarian", keyword=keyword, search_fields=search_fields)
    
    # MODIFIED: Pass the keyword back to the template to pre-fill the search box
    return render_template("crud_list.html", rows=rows, fields=fields, module="vet", keyword=keyword)

@app.route("/vet/add", methods=["GET","POST"])
def vet_add():
    fields = ["vetID","vetFName","vetLName","vetAddress","vetSpecial"]
    if request.method == "POST":
        # 1. Get the values and the specific ID value
        values = [request.form[f] for f in fields]
        vet_id = values[0] # Assuming vetID is the first field

        # 2. Check if ID exists (even if soft deleted)
        if id_exists("Veterinarian", "vetID", vet_id):
            # Pass an error message back to the form
            error_message = f"VET ID {vet_id} is already in use. Please choose a new ID."
            return render_template("crud_form.html", fields=fields, module="vet", action="Add", error=error_message)

        # 3. If ID is unique, proceed with insert
        insert_record("Veterinarian", fields, values)
        return redirect("/vet")
    return render_template("crud_form.html", fields=fields, module="vet", action="Add")

@app.route("/vet/edit/<id>", methods=["GET","POST"])
def vet_edit(id):
    fields = ["vetID","vetFName","vetLName","vetAddress","vetSpecial"]
    row = get_record("Veterinarian","vetID", id)
    if request.method == "POST":
        values = [request.form[f] for f in fields]
        update_record("Veterinarian", fields, values, "vetID", id)
        return redirect("/vet")
    return render_template("crud_form.html", fields=fields, module="vet", row=row, action="Edit")

@app.route("/vet/delete/<id>")
def vet_delete(id):
    delete_record("Veterinarian", "vetID", id)
    return redirect("/vet")

# --------------- PET OWNER -----------------
@app.route("/owner")
def owner_list():
    fields = ["petOwnerID","petOwnerFName","petOwnerLName","petOwnerBDate","petOwnerTelNo"]
    search_fields = ["petOwnerID","petOwnerFName","petOwnerLName","petOwnerBDate","petOwnerTelNo"] # Fields to search in
    keyword = request.args.get("keyword", "") # Get the search keyword from the URL

    # MODIFIED: Pass keyword and search_fields to load_table
    rows = load_table("PetOwner", keyword=keyword, search_fields=search_fields)
    
    # MODIFIED: Pass the keyword back to the template to pre-fill the search box
    return render_template("crud_list.html", rows=rows, fields=fields, module="owner", keyword=keyword)

@app.route("/owner/add", methods=["GET","POST"])
def owner_add():
    fields = ["petOwnerID","petOwnerFName","petOwnerLName","petOwnerBDate","petOwnerTelNo"]
    if request.method == "POST":
        # 1. Get the values and the specific ID value
        values = [request.form[f] for f in fields]
        petOwner_id = values[0]

        # 2. Check if ID exists (even if soft deleted)
        if id_exists("PetOwner", "petOwnerID", petOwner_id):
            # Pass an error message back to the form
            error_message = f"OWNER ID {petOwner_id} is already in use. Please choose a new ID."
            return render_template("crud_form.html", fields=fields, module="owner", action="Add", error=error_message)

        # 3. If ID is unique, proceed with insert
        insert_record("PetOwner", fields, values)
        return redirect("/owner")
    return render_template("crud_form.html", fields=fields, module="owner", action="Add")

@app.route("/owner/edit/<id>", methods=["GET","POST"])
def owner_edit(id):
    fields = ["petOwnerID","petOwnerFName","petOwnerLName","petOwnerBDate","petOwnerTelNo"]
    row = get_record("PetOwner","petOwnerID", id)
    if request.method == "POST":
        values = [request.form[f] for f in fields]
        update_record("PetOwner", fields, values, "petOwnerID", id)
        return redirect("/owner")
    return render_template("crud_form.html", fields=fields, module="owner", row=row, action="Edit")

@app.route("/owner/delete/<id>")
def owner_delete(id):
    delete_record("PetOwner", "petOwnerID", id)
    return redirect("/owner")

# --------------- PET -----------------------
@app.route("/pet")
def pet_list():
    fields = ["petID","petName","petType","petBreed","petBDate", "petOwnerID"]
    search_fields = ["petID","petName","petType","petBreed","petBDate", "petOwnerID"] # Fields to search in
    keyword = request.args.get("keyword", "") # Get the search keyword from the URL

    # MODIFIED: Pass keyword and search_fields to load_table
    rows = load_table("Pet", keyword=keyword, search_fields=search_fields)
    
    # MODIFIED: Pass the keyword back to the template to pre-fill the search box
    return render_template("crud_list.html", rows=rows, fields=fields, module="pet", keyword=keyword)

@app.route("/pet/add", methods=["GET","POST"])
def pet_add():
    fields = ["petID","petName","petType","petBreed","petBDate", "petOwnerID"]
    if request.method == "POST":
        # 1. Get the values and the specific ID value
        values = [request.form[f] for f in fields]
        pet_id = values[0] 
        owner_id = values[5]

        # 2. Check if ID exists (even if soft deleted)
        if id_exists("Pet", "petID", pet_id):
            # Pass an error message back to the form
            error_message = f"PET ID {pet_id} is already in use. Please choose a new ID."
            return render_template("crud_form.html", fields=fields, module="pet", action="Add", error=error_message)

        # 2. Check if foreign key ID exists
        if not id_exists("PetOwner", "petOwnerID", owner_id):
            error_message = f"Owner ID '{owner_id}' does not exist. Please add the owner first."
            return render_template(
                "crud_form.html",
                fields=fields,
                module="pet",
                action="Add",
                error=error_message
            )
        
        # 3. If ID is unique, proceed with insert
        insert_record("Pet", fields, values)
        return redirect("/pet")
    return render_template("crud_form.html", fields=fields, module="pet", action="Add")

@app.route("/pet/edit/<id>", methods=["GET","POST"])
def pet_edit(id):
    fields = ["petID","petName","petType","petBreed","petBDate", "petOwnerID"]
    row = get_record("Pet","petID", id)
    if request.method == "POST":
        values = [request.form[f] for f in fields]
        update_record("Pet", fields, values, "petID", id)
        return redirect("/pet")
    return render_template("crud_form.html", fields=fields, module="pet", row=row, action="Edit")

@app.route("/pet/delete/<id>")
def pet_delete(id):
    delete_record("Pet", "petID", id)
    return redirect("/pet")

# --------------- CONSULTATION -----------------
@app.route("/consultation")
def consultation_list():
    fields = ["consultID","petID","vetID","consultDate","diagnoses", "prescription"]
    search_fields = ["consultID","petID","vetID","consultDate","diagnoses", "prescription"] # Fields to search in
    keyword = request.args.get("keyword", "") # Get the search keyword from the URL

    # MODIFIED: Pass keyword and search_fields to load_table
    rows = load_table("Consultation", keyword=keyword, search_fields=search_fields)
    
    # MODIFIED: Pass the keyword back to the template to pre-fill the search box
    return render_template("crud_list.html", rows=rows, fields=fields, module="consultation", keyword=keyword)

@app.route("/consultation/add", methods=["GET","POST"])
def consultation_add():
    fields = ["consultID","petID","vetID","consultDate","diagnoses", "prescription"]
    if request.method == "POST":
        # 1. Get the values and the specific ID value
        values = [request.form[f] for f in fields]
        consult_id = str(values[0])
        pet_id = values[1]
        vet_id = values[2]

        # 2. Check if ID exists (even if soft deleted)
        if id_exists("Consultation", "consultID", consult_id):
            # Pass an error message back to the form
            error_message = f"CONSULT ID {consult_id} is already in use. Please choose a new ID."
            return render_template("crud_form.html", fields=fields, module="consultation", action="Add", error=error_message)

        # 2. Check if foreign key ID exists
        if not id_exists("Pet", "petID", pet_id) or not id_exists("Veterinarian", "vetID", vet_id):
            missing = []
            if not id_exists("Pet", "petID", pet_id):
                missing.append(f"PET ID '{pet_id}'")
            if not id_exists("Veterinarian", "vetID", vet_id):
                missing.append(f"VET ID '{vet_id}'")
            
            error_message = " and ".join(missing) + " does not exist. Please add them first."
            
            return render_template(
                "crud_form.html",
                fields=fields,
                module="consultation",
                action="Add",
                error=error_message
            )
     
        # 3. If ID is unique, proceed with insert
        insert_record("Consultation", fields, values)
        return redirect("/consultation")
    return render_template("crud_form.html", fields=fields, module="consultation", action="Add")

@app.route("/consultation/edit/<id>", methods=["GET","POST"])
def consultation_edit(id):
    fields = ["consultID","petID","vetID","consultDate","diagnoses", "prescription"]
    row = get_record("Consultation","consultID", id)
    if request.method == "POST":
        values = [request.form[f] for f in fields]
        update_record("Consultation", fields, values, "consultID", id)
        return redirect("/consultation")
    return render_template("crud_form.html", fields=fields, module="consultation", row=row, action="Edit")

@app.route("/consultation/delete/<id>")
def consultation_delete(id):
    delete_record("Consultation", "consultID", id)
    return redirect("/consultation")

@app.route("/consultation/inquiry", methods=["GET","POST"])
def consultation_inquiry():
    conn = db()
    query = """
    SELECT c.consultID, c.petID, c.vetID, c.consultDate, c.diagnoses, c.prescription
    FROM Consultation c
    JOIN Pet p ON c.petID = p.petID
    JOIN Veterinarian v ON c.vetID = v.vetID
    WHERE c.deleted=0
    """
    params = []

    # Get search inputs
    vet_special = request.args.get("vetSpecial", "").strip()
    pet_id = request.args.get("petID", "").strip()
    owner_id = request.args.get("petOwnerID", "").strip()
    vet_id = request.args.get("vetID", "").strip()
    start_date = request.args.get("startDate", "").strip()
    end_date = request.args.get("endDate", "").strip()

    # Filters
    if vet_special:
        query += " AND v.vetSpecial LIKE ?"
        params.append(f"%{vet_special}%")
    if pet_id:
        query += " AND c.petID = ?"
        params.append(pet_id)
    if owner_id:
        query += " AND p.petOwnerID = ?"
        params.append(owner_id)
    if vet_id:
        query += " AND c.vetID = ?"
        params.append(vet_id)
    if start_date and end_date:
        query += " AND c.consultDate BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    consultations = conn.execute(query, params).fetchall()
    conn.close()

    return render_template("consultation_inquiry.html", consultations=consultations)

# --------------- HOME MENU -----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/back")
def back():
    module = request.args.get("module", "vet")  # default to vet
    # Redirect to the proper list route
    if module == "vet":
        return redirect("/vet")
    elif module == "owner":
        return redirect("/owner")
    elif module == "pet":
        return redirect("/pet")
    elif module == "consultation":
        return redirect("/consultation")
    else:
        return redirect("/")  # fallback

if __name__ == "__main__":
    app.run(debug=True)
