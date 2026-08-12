import streamlit as st
import pandas as pd
import requests
import time
from supabase import create_client, Client
from datetime import datetime, date
from streamlit_option_menu import option_menu

# Page configuration
st.set_page_config(page_title="Enasalkanda Estate", page_icon="🌱", layout="wide")

# -------------------------------------------------------------------
# 🔒 AUTHENTICATION SYSTEM
# -------------------------------------------------------------------
def check_password():
    """Returns `True` if the user enters the correct password."""
    
    if st.session_state.get("password_correct", False):
        return True

    # Use columns to center the login box
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Add some spacing from the top
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Display a high-quality tea estate cover image

        
        # Centered Welcome Text
        st.markdown("<h1 style='text-align: center;'>🌱 Enasalkanda Estate</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray; margin-bottom: 20px;'>Secure Estate Management System</p>", unsafe_allow_html=True)
        
        # Interactive Login Form
        with st.form("login_form", clear_on_submit=False):
            entered_password = st.text_input(
                "Passcode", 
                type="password", 
                placeholder="Enter your secure passcode...",
                label_visibility="collapsed" # Hides the label for a cleaner look
            )
            
            # Full-width submit button
            submit_button = st.form_submit_button("Secure Login", use_container_width=True)
            
            if submit_button:
                if entered_password == st.secrets["APP_PASSWORD"]:
                    st.success("✅ Access Granted! Loading dashboard...")
                    time.sleep(1)  # Pause for 1 second so the user sees the success message
                    st.session_state["password_correct"] = True
                    st.rerun()
                elif entered_password:
                    st.error("😕 Incorrect Passcode. Please try again.")
                else:
                    st.warning("⚠️ Please enter a passcode to continue.")
                    
    return False

# If the password is not correct, stop the script here!
if not check_password():
    st.stop()
    
# Initialize Supabase
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# -------------------------------------------------------------------
# LIVE WEATHER FUNCTION (Magedara / Galle coordinates)
# -------------------------------------------------------------------
@st.cache_data(ttl=900)  # Caches the weather for 15 minutes so it doesn't overload the API
def get_weather():
    try:
        # Approximate coordinates for the Magedara / Galle inland area
        lat = 6.13
        lon = 80.34
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&timezone=Asia%2FColombo"
        
        res = requests.get(url).json()
        current = res.get("current", {})
        
        temp = current.get("temperature_2m", "--")
        humidity = current.get("relative_humidity_2m", "--")
        rain = current.get("precipitation", "--")
        wind = current.get("wind_speed_10m", "--")
        
        # Build a styled HTML ribbon
        html_ribbon = f"""
        <div style="background-color: #e3f2fd; padding: 10px; border-radius: 5px; color: #0d47a1; display: flex; justify-content: space-around; font-weight: bold; margin-bottom: 20px;">
            <span>📍 Enasalkanda Estate</span>
            <span>🌡️ {temp}°C</span>
            <span>💧 Humidity: {humidity}%</span>
            <span>🌧️ Rain (last hr): {rain} mm</span>
            <span>💨 Wind: {wind} km/h</span>
        </div>
        """
        return html_ribbon
    except Exception:
        return "<div style='color: red; padding: 10px;'>⚠️ Live weather temporarily unavailable</div>"

# -------------------------------------------------------------------
# MAIN LAYOUT
# -------------------------------------------------------------------
st.title("🌱 Enasalkanda Estate Tracker")

# Display the Weather Ribbon right under the title
st.markdown(get_weather(), unsafe_allow_html=True)


# -------------------------------------------------------------------
# INTERACTIVE SIDEBAR NAVIGATION
# -------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1892/1892751.png", width=100) # Optional: Adds a little leaf logo at the top
    st.title("Menu")
    
    menu = option_menu(
        menu_title=None,
        options=[
            "Dashboard", "Blocks", "Employees", "Inventory", "Tea Plucking", 
            "Rubber Tapping", "Cinnamon Harvest", "Coconut Harvest", "Fertilizer Log", "Clearing Log", 
            "Spraying Log", "Soil Records", "Pilot Projects"
        ],
        icons=[
            "bar-chart-line-fill", "map-fill", "people-fill", "box-seam-fill", "basket3-fill", 
            "tree-fill", "scissors", "circle-fill", "moisture", "tools", "bug-fill", "layers", "compass-fill"  
            ],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#4CAF50", "font-size": "18px"}, 
            "nav-link": {
                "font-size": "16px", 
                "text-align": "left", 
                "margin": "0px", 
                "--hover-color": "#2e2e2e" if st.get_option("theme.base") == "dark" else "#f0f2f6"
            },
            "nav-link-selected": {"background-color": "#4CAF50", "color": "white", "font-weight": "bold"},
        }
    )

# Helper: Fetch Blocks
@st.cache_data(ttl=60)
def get_blocks():
    try:
        res = supabase.table("blocks").select("id, name").execute()
        return {item["name"]: item["id"] for item in res.data} if res.data else {}
    except Exception:
        return {}

# Helper: Fetch Employees by Role (or all active)
@st.cache_data(ttl=60)
def get_employees(role_filter=None):
    try:
        query = supabase.table("employees").select("emp_code, full_name, roles").eq("status", "Active")
        if role_filter:
            # Use .contains() to search inside the Postgres array
            query = query.contains("roles", [role_filter])
        res = query.execute()
        return {f"{item['emp_code']} - {item['full_name']}": item['full_name'] for item in res.data} if res.data else {}
    except Exception:
        return {}

blocks_map = get_blocks()

# -------------------------------------------------------------------
# ESTATE BLOCKS MANAGEMENT
# -------------------------------------------------------------------
if menu == "Blocks":
    st.header("🗺️ Estate Blocks Management")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        tab1, tab2 = st.tabs(["Add Block", "Update Block"])
        
        # --- TAB 1: ADD NEW BLOCK ---
        with tab1:
            with st.form("add_block_form", clear_on_submit=True):
                name = st.text_input("Block Name", placeholder="e.g., Block A")
                extent_acres = st.number_input("Extent (Acres)", min_value=0.0, step=0.25)
                primary_crop = st.selectbox(
                    "Primary Crop", 
                    ["Tea", "Rubber", "Mixed (Tea & Rubber)", "Pepper", "Cinnamon", "Coconut", "Other"]
                )
                planting_density = st.number_input("Planting Density (Total Bushes/Trees)", min_value=0, step=50)
                
                submitted_add = st.form_submit_button("Save Block")
                if submitted_add:
                    if name:
                        data = {
                            "name": name.strip(),
                            "extent_acres": extent_acres,
                            "primary_crop": primary_crop,
                            "planting_density": planting_density
                        }
                        supabase.table("blocks").insert(data).execute()
                        st.success(f"Added {name} successfully!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Please provide a Block Name.")

        # --- TAB 2: UPDATE EXISTING BLOCK ---
        with tab2:
            res_blocks = supabase.table("blocks").select("*").execute()
            all_blocks = res_blocks.data if res_blocks.data else []
            
            if all_blocks:
                block_dict = {b["name"]: b for b in all_blocks}
                selected_block_name = st.selectbox("Select Block to Update", list(block_dict.keys()))
                selected_b = block_dict[selected_block_name]
                
                with st.form("update_block_form"):
                    new_name = st.text_input("Block Name", value=selected_b["name"])
                    new_extent = st.number_input("Extent (Acres)", value=float(selected_b.get("extent_acres") or 0.0), step=0.25)
                    
                    crop_options = ["Tea", "Rubber", "Mixed (Tea & Rubber)", "Pepper", "Cinnamon", "Coconut", "Other"]
                    current_crop = selected_b.get("primary_crop", "Tea")
                    crop_index = crop_options.index(current_crop) if current_crop in crop_options else 0
                    
                    new_crop = st.selectbox("Primary Crop", crop_options, index=crop_index)
                    new_density = st.number_input("Planting Density", value=int(selected_b.get("planting_density") or 0), step=50)
                    
                    submitted_update = st.form_submit_button("Update Details")
                    if submitted_update:
                        if new_name:
                            update_data = {
                                "name": new_name.strip(),
                                "extent_acres": new_extent,
                                "primary_crop": new_crop,
                                "planting_density": new_density
                            }
                            supabase.table("blocks").update(update_data).eq("id", selected_b["id"]).execute()
                            
                            st.success(f"Updated details for {new_name}!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Block Name cannot be empty.")
            else:
                st.info("No blocks found to update.")

    # --- DATAFRAME VIEW ---
    with col2:
        st.subheader("Current Blocks")
        res = supabase.table("blocks").select("name, extent_acres, primary_crop, planting_density").execute()
        if res.data:
            df_blocks = pd.DataFrame(res.data)
            # Rename columns so they look clean in the dashboard
            df_blocks.columns = ["Block Name", "Acres", "Primary Crop", "Density (Trees/Bushes)"]
            st.dataframe(df_blocks, use_container_width=True)
        else:
            st.info("No blocks registered yet.")

# -------------------------------------------------------------------
# 1. EMPLOYEE MANAGEMENT
# -------------------------------------------------------------------
if menu == "Employees":
    st.header("👥 Employee Directory")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        tab1, tab2 = st.tabs(["Add Worker", "Update Worker"])
        
        # --- TAB 1: ADD NEW WORKER ---
        with tab1:
            with st.form("add_employee_form", clear_on_submit=True):
                emp_code = st.text_input("Worker ID / Code", placeholder="e.g., EMP01")
                full_name = st.text_input("Full Name")
                roles = st.multiselect(
                    "Assigned Roles", 
                    ["Plucker", "Tapper", "General Labor", "Sprayer", "Supervisor"],
                    default=["General Labor"]
                )
                joined_date = st.date_input("Joined Date", value=date.today()) # New date picker
                phone = st.text_input("Phone Number (Optional)")
                
                submitted_add = st.form_submit_button("Save Employee")
                if submitted_add:
                    if emp_code and full_name and roles:
                        data = {
                            "emp_code": emp_code.strip().upper(),
                            "full_name": full_name.strip(),
                            "roles": roles,
                            "joined_date": str(joined_date), # Convert to string for database
                            "phone": phone.strip() if phone else None,
                            "status": "Active"
                        }
                        supabase.table("employees").insert(data).execute()
                        st.success(f"Added {full_name} ({emp_code}) successfully!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Please provide a Worker ID, Full Name, and at least one Role.")

        # --- TAB 2: UPDATE EXISTING WORKER ---
        with tab2:
            all_employees_res = supabase.table("employees").select("*").execute()
            all_employees = all_employees_res.data if all_employees_res.data else []
            
            if all_employees:
                emp_dict = {f"{emp['emp_code']} - {emp['full_name']}": emp for emp in all_employees}
                selected_emp_label = st.selectbox("Select Worker to Update", list(emp_dict.keys()))
                selected_emp = emp_dict[selected_emp_label]
                
                # Handle existing dates carefully (in case some are missing)
                existing_date_str = selected_emp.get("joined_date")
                if existing_date_str:
                    parsed_date = datetime.strptime(existing_date_str, "%Y-%m-%d").date()
                else:
                    parsed_date = date.today()

                with st.form("update_employee_form"):
                    new_full_name = st.text_input("Full Name", value=selected_emp["full_name"])
                    new_roles = st.multiselect(
                        "Assigned Roles", 
                        ["Plucker", "Tapper", "General Labor", "Sprayer", "Supervisor"],
                        default=selected_emp.get("roles", ["General Labor"])
                    )
                    new_joined_date = st.date_input("Joined Date", value=parsed_date) # Pre-filled date picker
                    new_phone = st.text_input("Phone Number", value=selected_emp.get("phone", ""))
                    new_status = st.selectbox(
                        "Employment Status", 
                        ["Active", "Inactive"], 
                        index=0 if selected_emp.get("status") == "Active" else 1
                    )
                    
                    submitted_update = st.form_submit_button("Update Details")
                    if submitted_update:
                        if new_full_name and new_roles:
                            update_data = {
                                "full_name": new_full_name.strip(),
                                "roles": new_roles,
                                "joined_date": str(new_joined_date),
                                "phone": new_phone.strip() if new_phone else None,
                                "status": new_status
                            }
                            supabase.table("employees").update(update_data).eq("emp_code", selected_emp["emp_code"]).execute()
                            
                            st.success(f"Updated details for {new_full_name}!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Full Name and Roles cannot be empty.")
            else:
                st.info("No employees found to update.")

    # --- DATAFRAME VIEW ---
    with col2:
        st.subheader("Employee Database")
        # Added joined_date to the select query
        res = supabase.table("employees").select("emp_code, full_name, roles, joined_date, phone, status").execute()
        if res.data:
            df_emp = pd.DataFrame(res.data)
            if "roles" in df_emp.columns:
                df_emp["roles"] = df_emp["roles"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
            
            def highlight_status(val):
                color = '#4CAF50' if val == 'Active' else '#F44336'
                return f'color: {color}; font-weight: bold'
            
            st.dataframe(df_emp.style.map(highlight_status, subset=['status']), use_container_width=True)
        else:
            st.info("No employees registered yet.")

# -------------------------------------------------------------------
# 2. TEA PLUCKING FORM & HISTORY
# -------------------------------------------------------------------
elif menu == "Tea Plucking":
    st.header("🍃 Log Tea Plucking")
    
    # Fetch active workers
    pluckers_map = get_employees(role_filter="Plucker")
    if not pluckers_map:
        pluckers_map = get_employees()

    col1, col2 = st.columns([1, 2])

    # --- ADD NEW RECORD ---
    with col1:
        st.subheader("New Record")
        with st.form("tea_form", clear_on_submit=True):
            # Fetch and filter only Tea blocks
            res_blocks = supabase.table("blocks").select("id, name, primary_crop").execute()
            tea_blocks_map = {
                b["name"]: b["id"] 
                for b in (res_blocks.data or []) 
                if b.get("primary_crop") in ["Tea", "Mixed (Tea & Rubber)"]
            }
            
            block_name = st.selectbox(
                "Select Block", 
                list(tea_blocks_map.keys()) if tea_blocks_map else ["No Tea Blocks Found"]
            )
            plucking_date = st.date_input("Plucking Date", value=date.today())
            
            selected_worker_label = st.selectbox("Select Plucker", list(pluckers_map.keys()) if pluckers_map else ["Manual Entry"])
            worker_name = pluckers_map.get(selected_worker_label) if pluckers_map else st.text_input("Plucker Name")
            
            green_leaf_kg = st.number_input("Green Leaf Weight (kg)", min_value=0.0, step=0.5)
            
            submitted = st.form_submit_button("Save Record")
            if submitted:
                if green_leaf_kg > 0:
                    data = {
                        "block_id": tea_blocks_map.get(block_name),
                        "plucking_date": str(plucking_date),
                        "worker_name": worker_name,
                        "green_leaf_kg": green_leaf_kg
                    }
                    supabase.table("tea_plucking_logs").insert(data).execute()
                    st.success(f"Recorded {green_leaf_kg} kg for {worker_name} in {block_name}!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Please enter a valid weight greater than 0.")

    # --- VIEW HISTORY ---
    with col2:
        st.subheader("Plucking History")
        # Fetch records sorted by newest first
        res = supabase.table("tea_plucking_logs").select("*").order("plucking_date", desc=True).execute()
        
        if res.data:
            df_tea = pd.DataFrame(res.data)
            
            # Map Block IDs back to Block Names for readability
            inv_blocks_map = {v: k for k, v in blocks_map.items()}
            df_tea["Block"] = df_tea["block_id"].map(inv_blocks_map)
            
            # Reorganize and clean up columns for display
            df_tea = df_tea[["plucking_date", "Block", "worker_name", "green_leaf_kg"]]
            df_tea.columns = ["Date", "Block", "Plucker Name", "Green Leaf (kg)"]
            
            st.dataframe(df_tea, use_container_width=True)
        else:
            st.info("No tea plucking records logged yet.")

# -------------------------------------------------------------------
# 3. RUBBER TAPPING FORM & HISTORY
# -------------------------------------------------------------------
elif menu == "Rubber Tapping":
    st.header("🪵 Log Rubber Tapping")
    
    # Fetch active workers
    tappers_map = get_employees(role_filter="Tapper")
    if not tappers_map:
        tappers_map = get_employees()

    col1, col2 = st.columns([1, 2])

    # --- ADD NEW RECORD ---
    with col1:
        st.subheader("New Record")
        with st.form("rubber_form", clear_on_submit=True):
            # Fetch and filter only Rubber blocks
            res_blocks = supabase.table("blocks").select("id, name, primary_crop").execute()
            rubber_blocks_map = {
                b["name"]: b["id"] 
                for b in (res_blocks.data or []) 
                if b.get("primary_crop") in ["Rubber", "Mixed (Tea & Rubber)"]
            }
            
            block_name = st.selectbox(
                "Select Block", 
                list(rubber_blocks_map.keys()) if rubber_blocks_map else ["No Rubber Blocks Found"]
            )
            tapping_date = st.date_input("Tapping Date", value=date.today())
            
            selected_tapper_label = st.selectbox("Select Tapper", list(tappers_map.keys()) if tappers_map else ["Manual Entry"])
            tapper_name = tappers_map.get(selected_tapper_label) if tappers_map else st.text_input("Tapper Name")
            
            trees_tapped = st.number_input("Trees Tapped", min_value=0, step=1)
            latex_liters = st.number_input("Latex Collected (Liters)", min_value=0.0, step=0.5)
            drc_percent = st.number_input("Dry Rubber Content (DRC %)", min_value=0.0, max_value=100.0, value=30.0)
            
            submitted = st.form_submit_button("Save Record")
            if submitted:
                data = {
                    "block_id": rubber_blocks_map.get(block_name),
                    "tapping_date": str(tapping_date),
                    "tapper_name": tapper_name,
                    "trees_tapped": trees_tapped,
                    "latex_liters": latex_liters,
                    "drc_percent": drc_percent
                }
                supabase.table("rubber_tapping_logs").insert(data).execute()
                st.success(f"Recorded {latex_liters} L for {tapper_name} in {block_name}!")
                st.cache_data.clear()
                st.rerun()

    # --- VIEW HISTORY ---
    with col2:
        st.subheader("Tapping History")
        # Fetch records sorted by newest first
        res = supabase.table("rubber_tapping_logs").select("*").order("tapping_date", desc=True).execute()
        
        if res.data:
            df_rubber = pd.DataFrame(res.data)
            
            # Map Block IDs back to Block Names
            inv_blocks_map = {v: k for k, v in blocks_map.items()}
            df_rubber["Block"] = df_rubber["block_id"].map(inv_blocks_map)
            
            # Auto-calculate the actual Dry Rubber weight
            df_rubber["Dry Rubber (kg)"] = (df_rubber["latex_liters"] * (df_rubber["drc_percent"] / 100)).round(2)
            
            # Reorganize and clean up columns for display
            df_rubber = df_rubber[["tapping_date", "Block", "tapper_name", "trees_tapped", "latex_liters", "drc_percent", "Dry Rubber (kg)"]]
            df_rubber.columns = ["Date", "Block", "Tapper", "Trees Tapped", "Latex (L)", "DRC (%)", "Dry Rubber (kg)"]
            
            st.dataframe(df_rubber, use_container_width=True)
        else:
            st.info("No rubber tapping records logged yet.")
            
# -------------------------------------------------------------------
# 3.5 CINNAMON HARVEST FORM & HISTORY
# -------------------------------------------------------------------
elif menu == "Cinnamon Harvest":
    st.header("✂️ Log Cinnamon Harvesting & Peeling")
    
    # Fetch active workers (You can filter by a specific role like 'Peeler' if you add it to the Employee section later)
    workers_map = get_employees()

    col1, col2 = st.columns([1, 2])

    # --- ADD NEW RECORD ---
    with col1:
        st.subheader("New Record")
        with st.form("cinnamon_form", clear_on_submit=True):
            # Fetch and filter only Cinnamon blocks
            res_blocks = supabase.table("blocks").select("id, name, primary_crop").execute()
            cinnamon_blocks_map = {
                b["name"]: b["id"] 
                for b in (res_blocks.data or []) 
                if b.get("primary_crop") in ["Cinnamon"]
            }
            
            block_name = st.selectbox(
                "Select Block", 
                list(cinnamon_blocks_map.keys()) if cinnamon_blocks_map else ["No Cinnamon Blocks Found"]
            )
            
            harvest_date = st.date_input("Harvest Date", value=date.today())
            
            selected_worker_label = st.selectbox("Select Worker/Peeler", list(workers_map.keys()) if workers_map else ["Manual Entry"])
            worker_name = workers_map.get(selected_worker_label) if workers_map else st.text_input("Worker Name")
            
            yield_kg = st.number_input("Yield Weight (kg)", min_value=0.0, step=0.5)
            
            # Common Sri Lankan Cinnamon Grades
            grade = st.selectbox(
                "Cinnamon Grade", 
                ["Alba", "C5 Special", "C5", "C4", "M5", "M4", "H1", "H2", "Quillings/Off-grades"]
            )
            
            notes = st.text_area("Notes", placeholder="Weather conditions, quality observations...")
            
            submitted = st.form_submit_button("Save Record")
            if submitted:
                if yield_kg > 0:
                    data = {
                        "block_id": cinnamon_blocks_map.get(block_name),
                        "harvest_date": str(harvest_date),
                        "worker_name": worker_name,
                        "yield_kg": yield_kg,
                        "grade": grade,
                        "notes": notes.strip() if notes else None
                    }
                    supabase.table("cinnamon_logs").insert(data).execute()
                    st.success(f"Recorded {yield_kg}kg of {grade} grade for {worker_name}!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Please enter a valid weight greater than 0.")

    # --- VIEW HISTORY ---
    with col2:
        st.subheader("Harvesting History")
        res = supabase.table("cinnamon_logs").select("*").order("harvest_date", desc=True).execute()
        
        if res.data:
            df_cin = pd.DataFrame(res.data)
            
            # Map Block IDs back to Block Names
            inv_blocks_map = {v: k for k, v in blocks_map.items()}
            df_cin["Block"] = df_cin["block_id"].map(inv_blocks_map)
            
            # Highlight premium grades (Alba, C5 Special)
            def highlight_grades(row):
                if row['Grade'] in ['Alba', 'C5 Special']:
                    return ['color: #FF9800; font-weight: bold'] * len(row) # Highlight premium in orange/gold
                return [''] * len(row)
            
            # Reorganize columns
            df_cin = df_cin[["harvest_date", "Block", "worker_name", "yield_kg", "grade"]]
            df_cin.columns = ["Date", "Block", "Worker", "Yield (kg)", "Grade"]
            
            st.dataframe(df_cin.style.apply(highlight_grades, axis=1), use_container_width=True)
        else:
            st.info("No cinnamon harvesting records logged yet.")

# -------------------------------------------------------------------
# 3.6 COCONUT HARVEST FORM & HISTORY
# -------------------------------------------------------------------
elif menu == "Coconut Harvest":
    st.header("🥥 Log Coconut Harvesting")
    
    # Fetch active workers (Can use general labor or specific pluckers)
    workers_map = get_employees()

    col1, col2 = st.columns([1, 2])

    # --- ADD NEW RECORD ---
    with col1:
        st.subheader("New Record")
        with st.form("coconut_form", clear_on_submit=True):
            # Fetch and filter only Coconut blocks
            res_blocks = supabase.table("blocks").select("id, name, primary_crop").execute()
            coconut_blocks_map = {
                b["name"]: b["id"] 
                for b in (res_blocks.data or []) 
                if b.get("primary_crop") in ["Coconut"]
            }
            
            block_name = st.selectbox(
                "Select Block", 
                list(coconut_blocks_map.keys()) if coconut_blocks_map else ["No Coconut Blocks Found"]
            )
            
            harvest_date = st.date_input("Harvest Date", value=date.today())
            
            selected_worker_label = st.selectbox("Select Harvester", list(workers_map.keys()) if workers_map else ["Manual Entry"])
            worker_name = workers_map.get(selected_worker_label) if workers_map else st.text_input("Worker Name")
            
            nuts_harvested = st.number_input("Good Nuts Harvested", min_value=0, step=10)
            rejected_nuts = st.number_input("Rejected / Spoiled Nuts", min_value=0, step=1)
            
            notes = st.text_area("Notes", placeholder="Pest issues, weather conditions...")
            
            submitted = st.form_submit_button("Save Record")
            if submitted:
                if nuts_harvested > 0 or rejected_nuts > 0:
                    data = {
                        "block_id": coconut_blocks_map.get(block_name),
                        "harvest_date": str(harvest_date),
                        "worker_name": worker_name,
                        "nuts_harvested": nuts_harvested,
                        "rejected_nuts": rejected_nuts,
                        "notes": notes.strip() if notes else None
                    }
                    supabase.table("coconut_logs").insert(data).execute()
                    st.success(f"Recorded {nuts_harvested} nuts for {worker_name}!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Please enter a valid nut count greater than 0.")

    # --- VIEW HISTORY ---
    with col2:
        st.subheader("Harvesting History")
        res = supabase.table("coconut_logs").select("*").order("harvest_date", desc=True).execute()
        
        if res.data:
            df_coco = pd.DataFrame(res.data)
            
            # Map Block IDs back to Block Names
            inv_blocks_map = {v: k for k, v in blocks_map.items()}
            df_coco["Block"] = df_coco["block_id"].map(inv_blocks_map)
            
            # Highlight rows with high rejection rates
            def highlight_rejected(row):
                if row['Rejected'] > 5:
                    return ['color: #F44336; font-weight: bold'] * len(row) # Highlight in red if many spoiled nuts
                return [''] * len(row)
            
            # Reorganize columns
            df_coco = df_coco[["harvest_date", "Block", "worker_name", "nuts_harvested", "rejected_nuts"]]
            df_coco.columns = ["Date", "Block", "Worker", "Good Nuts", "Rejected"]
            
            st.dataframe(df_coco.style.apply(highlight_rejected, axis=1), use_container_width=True)
        else:
            st.info("No coconut harvesting records logged yet.")

# -------------------------------------------------------------------
# 4. DASHBOARD & ANALYTICS
# -------------------------------------------------------------------
elif menu == "Dashboard":
    st.header("📊 Estate Performance Dashboard")
    
    # 1. Fetch data from all operational tables
    tea_res = supabase.table("tea_plucking_logs").select("*").execute()
    rubber_res = supabase.table("rubber_tapping_logs").select("*").execute()
    clear_res = supabase.table("clearing_logs").select("*").execute()
    fert_res = supabase.table("fertilizer_logs").select("*").execute()
    
    df_tea = pd.DataFrame(tea_res.data) if tea_res.data else pd.DataFrame()
    df_rubber = pd.DataFrame(rubber_res.data) if rubber_res.data else pd.DataFrame()
    df_clear = pd.DataFrame(clear_res.data) if clear_res.data else pd.DataFrame()
    df_fert = pd.DataFrame(fert_res.data) if fert_res.data else pd.DataFrame()
    
    # 2. Extract all available months across all datasets for the drop-down
    all_dates = []
    if not df_tea.empty: all_dates.extend(pd.to_datetime(df_tea["plucking_date"]).tolist())
    if not df_rubber.empty: all_dates.extend(pd.to_datetime(df_rubber["tapping_date"]).tolist())
    if not df_clear.empty: all_dates.extend(pd.to_datetime(df_clear["clearing_date"]).tolist())
    if not df_fert.empty: all_dates.extend(pd.to_datetime(df_fert["fertilizer_date"]).tolist())
    
    if all_dates:
        # Get unique months formatted as YYYY-MM
        unique_months = sorted(list(set([d.strftime("%Y-%m") for d in all_dates])), reverse=True)
    else:
        unique_months = [datetime.now().strftime("%Y-%m")]
        
    # Month Selector
    selected_month = st.selectbox("📅 Select Month to View", unique_months)
    
    # 3. Filter DataFrames by the selected month
    def filter_by_month(df, date_col, month_str):
        if df.empty: return df
        df[date_col] = pd.to_datetime(df[date_col])
        return df[df[date_col].dt.strftime("%Y-%m") == month_str]

    m_tea = filter_by_month(df_tea.copy(), "plucking_date", selected_month)
    m_rubber = filter_by_month(df_rubber.copy(), "tapping_date", selected_month)
    m_clear = filter_by_month(df_clear.copy(), "clearing_date", selected_month)
    m_fert = filter_by_month(df_fert.copy(), "fertilizer_date", selected_month)
    
    st.markdown("---")
    
    # ---------------------------------------------------------
    # ROW 1: PRODUCTION YIELD (Current Month)
    # ---------------------------------------------------------
    st.subheader(f"🌱 Production Yield ({selected_month})")
    
    # Calculate Tea
    tea_kg = m_tea["green_leaf_kg"].sum() if not m_tea.empty else 0
    
    # Calculate Rubber
    rubber_liters = m_rubber["latex_liters"].sum() if not m_rubber.empty else 0
    if not m_rubber.empty:
        m_rubber["dry_kg"] = m_rubber["latex_liters"] * (m_rubber["drc_percent"] / 100)
        rubber_dry_kg = m_rubber["dry_kg"].sum()
    else:
        rubber_dry_kg = 0

    col1, col2, col3 = st.columns(3)
    col1.metric("🍃 Total Tea Leaves (kg)", f"{tea_kg:.2f}")
    col2.metric("💧 Rubber Latex (Liters)", f"{rubber_liters:.2f}")
    col3.metric("🪵 Dry Rubber Equivalent (kg)", f"{rubber_dry_kg:.2f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ---------------------------------------------------------
    # ROW 2: LABOR & MAN-DAYS (Current Month)
    # ---------------------------------------------------------
    st.subheader(f"👥 Labor & Man-Days Utilized ({selected_month})")
    
    # Calculate Labors (Man-days)
    # Tea and Rubber forms log 1 record per worker per day
    tea_labor = len(m_tea) if not m_tea.empty else 0
    rubber_labor = len(m_rubber) if not m_rubber.empty else 0
    
    # Clearing and Fertilizer forms have a specific 'worker_count' column
    clear_labor = int(m_clear["worker_count"].sum()) if not m_clear.empty else 0
    fert_labor = int(m_fert["worker_count"].sum()) if not m_fert.empty else 0
    total_labor = tea_labor + rubber_labor + clear_labor + fert_labor
    
    colA, colB, colC, colD, colE = st.columns(5)
    colA.metric("Total Estate Labors", total_labor)
    colB.metric("Tea Pluckers", tea_labor)
    colC.metric("Rubber Tappers", rubber_labor)
    colD.metric("Clearing Labors", clear_labor)
    colE.metric("Fertilizing Labors", fert_labor)

    st.markdown("---")
    
# ---------------------------------------------------------
    # DETAILED TABS (Added Yield Forecast)
    # ---------------------------------------------------------
    # 1. Update the tabs array to include the 4th tab
    tab1, tab2, tab3, tab4 = st.tabs([
        "Tea Performance (All Time)", 
        "Rubber Performance (All Time)", 
        "⚠️ Maintenance Alerts", 
        "📈 Yield Forecast"
    ])
    
    # ... (Keep your existing code for tab1, tab2, and tab3 exactly as they are) ...
    
    # --- TAB 4: YIELD FORECASTING ---
    with tab4:
        st.write("### 📈 3-Month Yield Projection")
        st.write("This tool analyzes your historical monthly data and applies a 3-month rolling average to project expected short-term future yields.")
        
        # Helper function to generate time-series forecast
        def generate_forecast(df, date_col, value_col):
            if df.empty or len(df) < 2:
                return None
                
            df_calc = df.copy()
            df_calc['temp_date'] = pd.to_datetime(df_calc[date_col])
            df_calc['Month_Str'] = df_calc['temp_date'].dt.strftime('%Y-%m')
            
            # Group by Month
            monthly = df_calc.groupby('Month_Str')[value_col].sum().reset_index()
            monthly = monthly.sort_values('Month_Str')
            
            # Prepare Historical Dataframe
            hist_df = monthly.copy()
            hist_df.columns = ['Month', 'Actual (kg)']
            hist_df['Forecast (kg)'] = None
            
            # Calculate Forecast (using 3-month moving average)
            recent_avg = monthly[value_col].tail(3).mean()
            last_month_dt = pd.to_datetime(monthly['Month_Str'].iloc[-1])
            
            future_records = []
            for i in range(1, 4):
                # Automatically handles year rollover (e.g., Dec -> Jan)
                next_month = (last_month_dt + pd.DateOffset(months=i)).strftime('%Y-%m')
                future_records.append({
                    'Month': next_month,
                    'Actual (kg)': None,
                    'Forecast (kg)': round(recent_avg, 2)
                })
                
            fut_df = pd.DataFrame(future_records)
            
            # Connect the lines visually on the chart
            last_actual = hist_df.iloc[-1].copy()
            last_actual['Forecast (kg)'] = last_actual['Actual (kg)']
            hist_df.iloc[-1] = last_actual
            
            # Combine and return
            final_df = pd.concat([hist_df, fut_df]).set_index('Month')
            return final_df
            
        colA, colB = st.columns(2)
        
        with colA:
            st.markdown("**🍃 Tea Yield Forecast (kg)**")
            tea_forecast = generate_forecast(df_tea, "plucking_date", "green_leaf_kg")
            if tea_forecast is not None:
                st.line_chart(tea_forecast, color=["#4CAF50", "#FF9800"])
            else:
                st.info("Need at least 2 months of tea data to generate a forecast.")
                
        with colB:
            st.markdown("**🪵 Rubber Yield Forecast (Dry kg)**")
            if not df_rubber.empty:
                df_rubber_calc = df_rubber.copy()
                if "dry_kg" not in df_rubber_calc.columns:
                    df_rubber_calc["dry_kg"] = df_rubber_calc["latex_liters"] * (df_rubber_calc["drc_percent"] / 100)
                
                rubber_forecast = generate_forecast(df_rubber_calc, "tapping_date", "dry_kg")
                if rubber_forecast is not None:
                    # Renders Actuals in Blue, Forecasts in Orange
                    st.line_chart(rubber_forecast, color=["#2196F3", "#FF9800"]) 
                else:
                    st.info("Need at least 2 months of rubber data to generate a forecast.")
            else:
                st.info("No rubber data available.")

# -------------------------------------------------------------------
# 5. FERTILIZER LOG
# -------------------------------------------------------------------
elif menu == "Fertilizer Log":
    st.header("🧪 Log Fertilizer Application")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("New Application")
        with st.form("fertilizer_form", clear_on_submit=True):
            # Select Block
            block_name = st.selectbox("Select Block", list(blocks_map.keys()) if blocks_map else ["Block A"])
            
            # Application Details
            fertilizer_date = st.date_input("Application Date", value=date.today())
            fertilizer_type = st.text_input("Fertilizer Type / Mixture", placeholder="e.g., T-750, Urea, Dolomite")
            quantity_kg = st.number_input("Total Quantity Applied (kg)", min_value=0.0, step=5.0)
            worker_count = st.number_input("Number of Workers", min_value=1, step=1)
            
            submitted = st.form_submit_button("Save Record")
            if submitted:
                if fertilizer_type and quantity_kg > 0:
                    data = {
                        "block_id": blocks_map.get(block_name),
                        "fertilizer_date": str(fertilizer_date),
                        "fertilizer_type": fertilizer_type.strip(),
                        "quantity_kg": quantity_kg,
                        "worker_count": worker_count
                    }
                    supabase.table("fertilizer_logs").insert(data).execute()
                    st.success(f"Recorded {quantity_kg}kg of {fertilizer_type} for {block_name}!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Please provide the Fertilizer Type and a Quantity greater than 0.")

    with col2:
        st.subheader("Application History")
        res = supabase.table("fertilizer_logs").select("*").order("fertilizer_date", desc=True).execute()
        
        if res.data:
            df_fert = pd.DataFrame(res.data)
            
            # Map Block IDs back to Block Names for readability
            inv_blocks_map = {v: k for k, v in blocks_map.items()}
            df_fert["Block"] = df_fert["block_id"].map(inv_blocks_map)
            
            # Reorganize and clean up columns for the dataframe display
            df_fert = df_fert[["fertilizer_date", "Block", "fertilizer_type", "quantity_kg", "worker_count"]]
            df_fert.columns = ["Date", "Block", "Fertilizer Type", "Quantity (kg)", "Workers Used"]
            
            st.dataframe(df_fert, use_container_width=True)
        else:
            st.info("No fertilizer applications logged yet.")
            
# -------------------------------------------------------------------
# 6. CLEARING LOG
# -------------------------------------------------------------------
elif menu == "Clearing Log":
    st.header("🪓 Log Field Clearing & Maintenance")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("New Clearing Task")
        with st.form("clearing_form", clear_on_submit=True):
            # Select Block
            block_name = st.selectbox("Select Block", list(blocks_map.keys()) if blocks_map else ["Block A"])
            
            # Application Details
            clearing_date = st.date_input("Clearing Date", value=date.today())
            work_type = st.selectbox(
                "Type of Work", 
                ["Manual Weeding", "Brush Cutting", "Stump Removal", "Shade Tree Lopping", "Drain/Trench Clearing", "General Clean-up"]
            )
            worker_count = st.number_input("Number of Workers", min_value=1, step=1)
            
            submitted = st.form_submit_button("Save Record")
            if submitted:
                data = {
                    "block_id": blocks_map.get(block_name),
                    "clearing_date": str(clearing_date),
                    "work_type": work_type,
                    "worker_count": worker_count
                }
                supabase.table("clearing_logs").insert(data).execute()
                st.success(f"Recorded '{work_type}' for {block_name}!")
                st.cache_data.clear()
                st.rerun()

    with col2:
        st.subheader("Clearing History")
        # Fetch records sorted by newest first
        res = supabase.table("clearing_logs").select("*").order("clearing_date", desc=True).execute()
        
        if res.data:
            df_clear = pd.DataFrame(res.data)
            
            # Map Block IDs back to Block Names for readability
            inv_blocks_map = {v: k for k, v in blocks_map.items()}
            df_clear["Block"] = df_clear["block_id"].map(inv_blocks_map)
            
            # Reorganize and clean up columns for the dataframe display
            df_clear = df_clear[["clearing_date", "Block", "work_type", "worker_count"]]
            df_clear.columns = ["Date", "Block", "Work Type", "Workers Used"]
            
            st.dataframe(df_clear, use_container_width=True)
        else:
            st.info("No clearing tasks logged yet.")
            
# -------------------------------------------------------------------
# 7. SPRAYING LOG
# -------------------------------------------------------------------
elif menu == "Spraying Log":
    st.header("💨 Log Agrochemical Spraying")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("New Spraying Task")
        with st.form("spraying_form", clear_on_submit=True):
            block_name = st.selectbox("Select Block", list(blocks_map.keys()) if blocks_map else ["Block A"])
            spraying_date = st.date_input("Spraying Date", value=date.today())
            
            chemical_type = st.selectbox("Chemical Type", ["Herbicide (Weed Killer)", "Fungicide", "Pesticide", "Foliar Fertilizer", "Other"])
            chemical_name = st.text_input("Chemical Name / Brand", placeholder="e.g., RoundUp, Copper Fungicide")
            quantity = st.text_input("Quantity Used", placeholder="e.g., 5 Liters or 2 kg")
            worker_count = st.number_input("Number of Workers", min_value=1, step=1)
            
            submitted = st.form_submit_button("Save Record")
            if submitted:
                if chemical_name and quantity:
                    data = {
                        "block_id": blocks_map.get(block_name),
                        "spraying_date": str(spraying_date),
                        "chemical_type": chemical_type,
                        "chemical_name": chemical_name.strip(),
                        "quantity": quantity.strip(),
                        "worker_count": worker_count
                    }
                    supabase.table("spraying_logs").insert(data).execute()
                    st.success(f"Recorded spraying {chemical_name} in {block_name}!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Please provide the Chemical Name and Quantity.")

    with col2:
        st.subheader("Spraying History")
        res = supabase.table("spraying_logs").select("*").order("spraying_date", desc=True).execute()
        
        if res.data:
            df_spray = pd.DataFrame(res.data)
            inv_blocks_map = {v: k for k, v in blocks_map.items()}
            df_spray["Block"] = df_spray["block_id"].map(inv_blocks_map)
            
            df_spray = df_spray[["spraying_date", "Block", "chemical_type", "chemical_name", "quantity", "worker_count"]]
            df_spray.columns = ["Date", "Block", "Type", "Chemical", "Quantity", "Workers Used"]
            
            st.dataframe(df_spray, use_container_width=True)
        else:
            st.info("No spraying tasks logged yet.")

# -------------------------------------------------------------------
# 8. SOIL RECORDS
# -------------------------------------------------------------------
elif menu == "Soil Records":
    st.header("🪨 Soil Health & Testing")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("New Soil Test")
        with st.form("soil_form", clear_on_submit=True):
            block_name = st.selectbox("Select Block", list(blocks_map.keys()) if blocks_map else ["Block A"])
            test_date = st.date_input("Test Date", value=date.today())
            
            ph_level = st.number_input("pH Level", min_value=0.0, max_value=14.0, value=6.5, step=0.1)
            
            st.markdown("**Macronutrient Levels (N-P-K)**")
            nitrogen_level = st.selectbox("Nitrogen (N)", ["Low", "Optimal", "High"])
            phosphorus_level = st.selectbox("Phosphorus (P)", ["Low", "Optimal", "High"])
            potassium_level = st.selectbox("Potassium (K)", ["Low", "Optimal", "High"])
            
            submitted = st.form_submit_button("Save Record")
            if submitted:
                data = {
                    "block_id": blocks_map.get(block_name),
                    "test_date": str(test_date),
                    "ph_level": ph_level,
                    "nitrogen_level": nitrogen_level,
                    "phosphorus_level": phosphorus_level,
                    "potassium_level": potassium_level
                }
                supabase.table("soil_logs").insert(data).execute()
                st.success(f"Recorded soil data for {block_name}!")
                st.cache_data.clear()
                st.rerun()

    with col2:
        st.subheader("Soil Test History")
        res = supabase.table("soil_logs").select("*").order("test_date", desc=True).execute()
        
        if res.data:
            df_soil = pd.DataFrame(res.data)
            inv_blocks_map = {v: k for k, v in blocks_map.items()}
            df_soil["Block"] = df_soil["block_id"].map(inv_blocks_map)
            
            # Highlight pH levels below 5.5 or above 7.5 (requires attention for tea/rubber)
            def highlight_ph(val):
                if val < 5.5:
                    return 'color: #F44336; font-weight: bold' # Too acidic
                elif val > 7.5:
                    return 'color: #FF9800; font-weight: bold' # Too alkaline
                return 'color: #4CAF50' # Optimal

            df_soil = df_soil[["test_date", "Block", "ph_level", "nitrogen_level", "phosphorus_level", "potassium_level"]]
            df_soil.columns = ["Date", "Block", "pH Level", "Nitrogen (N)", "Phosphorus (P)", "Potassium (K)"]
            
            st.dataframe(df_soil.style.map(highlight_ph, subset=['pH Level']), use_container_width=True)
        else:
            st.info("No soil test records logged yet.")
            
# -------------------------------------------------------------------
# 9. INVENTORY & STOCK MANAGEMENT
# -------------------------------------------------------------------
elif menu == "Inventory":
    st.header("📦 Inventory & Stock Management")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        tab1, tab2 = st.tabs(["Add New Item", "Receive Stock"])
        
        # --- TAB 1: REGISTER A NEW ITEM ---
        with tab1:
            with st.form("new_item_form", clear_on_submit=True):
                st.subheader("Register New Product")
                item_name = st.text_input("Item Name", placeholder="e.g., T-750, Pepper Vine Fertilizer, RoundUp")
                category = st.selectbox("Category", ["Fertilizer", "Agrochemical", "Tools/Equipment", "Other"])
                unit = st.selectbox("Unit of Measurement", ["kg", "Liters", "Pieces", "Bags"])
                initial_qty = st.number_input("Initial Quantity", min_value=0.0, step=1.0)
                
                submitted_new = st.form_submit_button("Register Item")
                if submitted_new:
                    if item_name:
                        # 1. Insert into main inventory
                        data = {
                            "item_name": item_name.strip(),
                            "category": category,
                            "unit": unit,
                            "quantity": initial_qty
                        }
                        try:
                            res = supabase.table("inventory").insert(data).execute()
                            
                            # 2. If initial quantity > 0, log it in the history!
                            if initial_qty > 0 and res.data:
                                new_item_id = res.data[0]['id']
                                log_data = {
                                    "item_id": new_item_id,
                                    "transaction_date": str(date.today()),
                                    "transaction_type": "IN",
                                    "quantity": initial_qty
                                }
                                supabase.table("inventory_logs").insert(log_data).execute()
                                
                            st.success(f"Registered {item_name} successfully!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Error saving item. It might already exist.")
                    else:
                        st.error("Please provide an Item Name.")

        # --- TAB 2: UPDATE/RECEIVE STOCK ---
        with tab2:
            res_inv = supabase.table("inventory").select("*").order("item_name").execute()
            all_items = res_inv.data if res_inv.data else []
            
            if all_items:
                st.subheader("Log New Delivery")
                item_dict = {f"{item['item_name']} ({item['category']})": item for item in all_items}
                selected_item_label = st.selectbox("Select Item", list(item_dict.keys()))
                selected_item = item_dict[selected_item_label]
                
                with st.form("update_stock_form"):
                    st.write(f"**Current Stock:** {selected_item['quantity']} {selected_item['unit']}")
                    
                    # Added a date selector so you can log past deliveries accurately
                    receive_date = st.date_input("Date Received", value=date.today())
                    qty_to_add = st.number_input("Quantity Received", min_value=0.0, step=1.0)
                    
                    submitted_update = st.form_submit_button("Update Stock")
                    if submitted_update:
                        if qty_to_add > 0:
                            # 1. Update the master inventory table
                            new_total = float(selected_item['quantity']) + qty_to_add
                            update_data = {
                                "quantity": new_total,
                                "last_updated": datetime.now().isoformat()
                            }
                            supabase.table("inventory").update(update_data).eq("id", selected_item["id"]).execute()
                            
                            # 2. Insert a record into the ledger
                            log_data = {
                                "item_id": selected_item["id"],
                                "transaction_date": str(receive_date),
                                "transaction_type": "IN",
                                "quantity": qty_to_add
                            }
                            supabase.table("inventory_logs").insert(log_data).execute()
                            
                            st.success(f"Added {qty_to_add} {selected_item['unit']} to {selected_item['item_name']}!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Please enter a quantity greater than 0.")
            else:
                st.info("No items registered yet. Use the 'Add New Item' tab first.")

    # --- RIGHT COLUMN: DATA VIEWS ---
    with col2:
        view_tab1, view_tab2 = st.tabs(["Current Stock", "Inward History Ledger"])
        
        with view_tab1:
            st.subheader("Current Stock Levels")
            res = supabase.table("inventory").select("item_name, category, quantity, unit, last_updated").order("category").execute()
            
            if res.data:
                df_inv = pd.DataFrame(res.data)
                df_inv["last_updated"] = pd.to_datetime(df_inv["last_updated"]).dt.strftime("%Y-%m-%d %H:%M")
                
                def highlight_low_stock(row):
                    if float(row['Quantity']) <= 10.0:
                        return ['color: #F44336; font-weight: bold'] * len(row)
                    return [''] * len(row)

                df_inv.columns = ["Item Name", "Category", "Quantity", "Unit", "Last Updated"]
                st.dataframe(df_inv.style.apply(highlight_low_stock, axis=1), use_container_width=True)
            else:
                st.info("Inventory is empty.")
                
        with view_tab2:
            st.subheader("Recent Deliveries (IN)")
            # Fetch only the 'IN' transactions
            res_logs = supabase.table("inventory_logs").select("*").eq("transaction_type", "IN").order("transaction_date", desc=True).execute()
            
            if res_logs.data and all_items:
                df_logs = pd.DataFrame(res_logs.data)
                
                # Map the item_id back to the human-readable item_name and unit
                id_to_name = {item['id']: item['item_name'] for item in all_items}
                id_to_unit = {item['id']: item['unit'] for item in all_items}
                
                df_logs["Item Name"] = df_logs["item_id"].map(id_to_name)
                df_logs["Unit"] = df_logs["item_id"].map(id_to_unit)
                
                # Clean up and arrange the columns
                df_logs = df_logs[["transaction_date", "Item Name", "quantity", "Unit"]]
                df_logs.columns = ["Date Received", "Item Name", "Quantity Received", "Unit"]
                
                st.dataframe(df_logs, use_container_width=True)
            else:
                st.info("No delivery records found.")
            
# -------------------------------------------------------------------
# 10. NURSERY & PILOT PROJECTS
# -------------------------------------------------------------------
elif menu == "Pilot Projects":
    st.header("🌱 Nursery & Pilot Project Tracker")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        tab1, tab2 = st.tabs(["Launch Project", "Update Survival"])
        
        # --- TAB 1: LAUNCH NEW PROJECT ---
        with tab1:
            with st.form("new_project_form", clear_on_submit=True):
                st.subheader("Start New Pilot")
                project_name = st.text_input("Project Name", placeholder="e.g., Block A Pepper Extension")
                crop_type = st.selectbox("Crop Type", ["Pepper", "Tea Clones", "Rubber Saplings", "Cinnamon", "Other"])
                planting_date = st.date_input("Planting/Nursery Date", value=date.today())
                initial_plants = st.number_input("Initial Number of Plants/Vines", min_value=1, step=10)
                notes = st.text_area("Notes", placeholder="Sourcing details, weather conditions, etc.")
                
                submitted_new = st.form_submit_button("Launch Project")
                if submitted_new:
                    if project_name:
                        data = {
                            "project_name": project_name.strip(),
                            "crop_type": crop_type,
                            "planting_date": str(planting_date),
                            "initial_plants": initial_plants,
                            "surviving_plants": initial_plants, # Starts at 100% survival
                            "last_checked": str(date.today()),
                            "notes": notes.strip() if notes else None
                        }
                        try:
                            supabase.table("pilot_projects").insert(data).execute()
                            st.success(f"Launched {project_name} successfully!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error("Error saving project. Name might already exist.")
                    else:
                        st.error("Please provide a Project Name.")

        # --- TAB 2: UPDATE SURVIVAL/STATUS ---
        with tab2:
            # Fetch active projects for the drop-down
            res_proj = supabase.table("pilot_projects").select("*").eq("status", "Active").order("project_name").execute()
            active_projects = res_proj.data if res_proj.data else []
            
            if active_projects:
                st.subheader("Log Project Check-in")
                proj_dict = {p['project_name']: p for p in active_projects}
                selected_proj_label = st.selectbox("Select Active Project", list(proj_dict.keys()))
                selected_proj = proj_dict[selected_proj_label]
                
                with st.form("update_project_form"):
                    st.write(f"**Planted:** {selected_proj['initial_plants']} | **Last Count:** {selected_proj['surviving_plants']}")
                    
                    new_surviving = st.number_input(
                        "Current Surviving Plants", 
                        min_value=0, 
                        max_value=int(selected_proj['initial_plants']), 
                        value=int(selected_proj['surviving_plants'])
                    )
                    
                    status = st.selectbox(
                        "Project Status", 
                        ["Active", "Matured (Move to Main Blocks)", "Failed/Discontinued"]
                    )
                    
                    update_notes = st.text_area("Update Notes", placeholder="Reason for mortality, disease spotted, etc.")
                    
                    submitted_update = st.form_submit_button("Update Project")
                    if submitted_update:
                        update_data = {
                            "surviving_plants": new_surviving,
                            "status": status,
                            "last_checked": str(date.today())
                        }
                        # Append new notes if provided
                        if update_notes:
                            existing_notes = selected_proj.get("notes") or ""
                            update_data["notes"] = f"{existing_notes}\n[{date.today()}] {update_notes.strip()}".strip()

                        supabase.table("pilot_projects").update(update_data).eq("id", selected_proj["id"]).execute()
                        st.success(f"Updated status for {selected_proj['project_name']}!")
                        st.cache_data.clear()
                        st.rerun()
            else:
                st.info("No active projects. Launch one in the other tab.")

    # --- DATAFRAME VIEW ---
    with col2:
        st.subheader("Project Overview")
        res = supabase.table("pilot_projects").select("project_name, crop_type, initial_plants, surviving_plants, status, last_checked").order("planting_date", desc=True).execute()
        
        if res.data:
            df_proj = pd.DataFrame(res.data)
            
            # Calculate the Survival Rate %
            df_proj["Survival Rate"] = ((df_proj["surviving_plants"] / df_proj["initial_plants"]) * 100).round(1).astype(str) + "%"
            
            # Highlight projects based on status and survival
            def highlight_projects(row):
                if row['status'] != 'Active':
                    return ['color: gray; font-style: italic'] * len(row)
                
                # Check survival rate (remove '%' and convert to float)
                rate = float(row['Survival Rate'].replace('%', ''))
                if rate < 70.0:
                    return ['color: #F44336; font-weight: bold'] * len(row) # Red if below 70%
                elif rate < 90.0:
                    return ['color: #FF9800'] * len(row) # Orange if below 90%
                return ['color: #4CAF50'] * len(row) # Green otherwise

            df_proj = df_proj[["project_name", "crop_type", "initial_plants", "surviving_plants", "Survival Rate", "status", "last_checked"]]
            df_proj.columns = ["Project Name", "Crop", "Planted", "Surviving", "Survival Rate", "Status", "Last Checked"]
            
            st.dataframe(df_proj.style.apply(highlight_projects, axis=1), use_container_width=True)
        else:
            st.info("No projects registered yet.")
