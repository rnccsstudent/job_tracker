import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date

st.set_page_config(page_title="Job Tracker", layout="centered")

# Connect to DB
def connect_db():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        port=int(st.secrets["mysql"]["port"]),
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"]
    )

# Load Data
def get_all_jobs():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM jobs")
    result = cursor.fetchall()
    conn.close()
    return result

# Add or Update Job
def add_job(job, edit_id=None):
    conn = connect_db()
    cursor = conn.cursor()
    if edit_id:
        cursor.execute("""
            UPDATE jobs SET job_title=%s, company=%s, url=%s, status=%s, date_applied=%s, notes=%s WHERE id=%s
        """, (*job, edit_id))
    else:
        cursor.execute("""
            INSERT INTO jobs (job_title, company, url, status, date_applied, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, job)
    conn.commit()
    conn.close()

# Delete Job
def delete_job(job_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE id=%s", (job_id,))
    conn.commit()
    conn.close()

# Main UI
st.title("📋 Job Application Tracker")

with st.expander("➕ Add or Edit Job"):
    with st.form("job_form", clear_on_submit=True):
        job_title = st.text_input("Job Title")
        company = st.text_input("Company Name")
        job_url = st.text_input("Job URL")
        status = st.selectbox("Status", ["Interested", "Applied", "Interviewing", "Offer", "Rejected"])
        date_applied = st.date_input("Date Applied", date.today())
        notes = st.text_area("Notes")
        edit_id = st.text_input("Edit Job ID (Leave blank to add new)", "")
        submitted = st.form_submit_button("💾 Save")
        if submitted:
            data = (job_title, company, job_url, status, date_applied, notes)
            add_job(data, edit_id if edit_id else None)
            st.success("✅ Job saved successfully")
            st.rerun()  # use st.experimental_rerun() if you're using old version

# Display Jobs
jobs = get_all_jobs()
df = pd.DataFrame(jobs)

if not df.empty:
    status_filter = st.selectbox("🔍 Filter by Status", ["All"] + df["status"].unique().tolist())
    if status_filter != "All":
        df = df[df["status"] == status_filter]

    for _, row in df.iterrows():
        with st.expander(f"{row['job_title']} at {row['company']}"):
            st.write(f"🔗 [Job Link]({row['url']})")
            st.write(f"🗓️ Applied: {row['date_applied']}")
            st.write(f"📌 Status: {row['status']}")
            st.write(f"📝 Notes: {row['notes']}")
            col1, col2 = st.columns(2)
            if col1.button("📝 Edit", key=f"edit_{row['id']}"):
                st.warning(f"Scroll up and enter Job ID: {row['id']} to edit")
            if col2.button("❌ Delete", key=f"del_{row['id']}"):
                delete_job(row['id'])
                st.success("🗑️ Deleted!")
                st.rerun()

    st.download_button("📥 Download CSV", data=df.to_csv(index=False), file_name="job_tracker.csv", mime="text/csv")
else:
    st.info("No jobs found. Add one from above.")
