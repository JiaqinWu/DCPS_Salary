import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

st.title("DCPS Salary Correction Dashboard")

st.caption(
    "Analyze original vs corrected salary amounts per employee and visualize changes across years."
)

df = pd.read_excel("Data Specialist Perf Task.xlsx",sheet_name = 'Staff Data')
salary = pd.read_excel("Data Specialist Perf Task.xlsx",sheet_name = '20-21 Salary Scale')

salary1 = pd.melt(salary, 
                  id_vars=['Education Level'], 
                  var_name='Step level', 
                  value_name='Salary')
salary1['Step level'] = salary1['Step level'].replace('Step 21','Step 21+')

def categorize_step(i):
    if 1 <= i <= 11:
        return f"Step {i}"
    elif 12 <= i <= 15:
        return "Step 12-15"
    elif i == 16:
        return "Step 16"
    elif 17 <= i <= 18:
        return "Step 17-18"
    elif 19 <= i <= 20:
        return "Step 19-20"
    elif i >= 21:
        return "Step 21+"
    else:
        return "Unknown"

# Create corrected step column
df['20-21 Step_corrected'] = df['20-21 Step'] + 1

# Apply categorization
df['Step level'] = df['20-21 Step'].apply(categorize_step)
df['Step level corrected'] = df['20-21 Step_corrected'].apply(categorize_step)

df_salary = pd.merge(df, salary1, on=['Education Level','Step level'], how='left').rename(columns={'Salary':'Salary 20-21'})
df_salary = pd.merge(df_salary, salary1.rename(columns={'Step level':'Step level corrected'}),\
     on=['Education Level','Step level corrected'], how='left').rename(columns={'Salary':'Salary 20-21 corrected'})

df_salary['Salary 21-22'] = round(df_salary['Salary 20-21']*1.02,2)
df_salary['Salary 22-23'] = round(df_salary['Salary 21-22']*1.03,2)
df_salary['Salary 23-24'] = round(df_salary['Salary 22-23'],2)
df_salary['Salary 24-25'] = round(df_salary['Salary 23-24']*1.02,2)
df_salary['Salary 21-22 corrected'] = round(df_salary['Salary 20-21 corrected']*1.02,2)
df_salary['Salary 22-23 corrected'] = round(df_salary['Salary 21-22 corrected']*1.03,2)
df_salary['Salary 23-24 corrected'] = round(df_salary['Salary 22-23 corrected'],2)
df_salary['Salary 24-25 corrected'] = round(df_salary['Salary 23-24 corrected']*1.02,2)

df_salary['Salary paid'] = df_salary['Salary 21-22']+df_salary['Salary 22-23']+df_salary['Salary 23-24']+df_salary['Salary 24-25']
df_salary['Salary paid corrected'] = df_salary['Salary 21-22 corrected']+df_salary['Salary 22-23 corrected']+df_salary['Salary 23-24 corrected']+df_salary['Salary 24-25 corrected']

st.header("Salary Step-Level Review")

employee_ids = df_salary['Employee ID'].unique()
id_labels = {eid: f"Employee ID: {eid}" for eid in employee_ids}
selected_label = st.selectbox(
    "Select an employee",
    options=[id_labels[eid] for eid in employee_ids],
)
selected_id = int(selected_label.split(": ")[-1])

selected = df_salary[df_salary['Employee ID'] == selected_id].iloc[0]

paid_original = float(selected['Salary 21-22'] + selected['Salary 22-23'] + selected['Salary 23-24'] + selected['Salary 24-25'])
paid_corrected = float(selected['Salary 21-22 corrected'] + selected['Salary 22-23 corrected'] + selected['Salary 23-24 corrected'] + selected['Salary 24-25 corrected'])
owed = round(paid_original - paid_corrected, 2)
owe_flag = owed >= 0
is_zero_delta = np.isclose(owed, 0.0)

st.subheader("Summary")
col1, col2, col3 = st.columns(3)
col1.metric(label="Employee", value=f"Employee ID: {selected_id}")
col2.metric(label="Total Paid (Original)", value=f"${paid_original:,.2f}")
# Delta rendering: yellow when 0, custom red badge when negative (owe), default metric when positive
if is_zero_delta:
    col3.markdown(
        f"""
        <div style="border:1px solid #e5e7eb; border-radius:8px; padding:12px">
          <div style="font-size:0.8rem; color:#6b7280">Total Paid (Corrected)</div>
          <div style="font-size:1.2rem; font-weight:600">${paid_corrected:,.2f}</div>
          <div style="margin-top:6px; display:inline-block; background:#facc15; color:#111827; border-radius:999px; padding:2px 8px; font-size:0.8rem">Δ 0</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
elif owed < 0:
    owe_amount = abs(owed)
    col3.markdown(
        f"""
        <div style="border:1px solid #e5e7eb; border-radius:8px; padding:12px">
          <div style="font-size:0.8rem; color:#6b7280">Total Paid (Corrected)</div>
          <div style="font-size:1.2rem; font-weight:600">${paid_corrected:,.2f}</div>
          <div style="margin-top:6px; display:inline-block; background:#ef4444; color:#ffffff; border-radius:999px; padding:2px 8px; font-size:0.8rem">owe ${owe_amount:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    delta_value = owed
    col3.metric(label="Total Paid (Corrected)", value=f"${paid_corrected:,.2f}", delta=delta_value, delta_color="normal")

st.divider()

# Prepare tidy data for line plot
years = ["21-22", "22-23", "23-24", "24-25"]
original_values = [
    float(selected['Salary 21-22']),
    float(selected['Salary 22-23']),
    float(selected['Salary 23-24']),
    float(selected['Salary 24-25']),
]
corrected_values = [
    float(selected['Salary 21-22 corrected']),
    float(selected['Salary 22-23 corrected']),
    float(selected['Salary 23-24 corrected']),
    float(selected['Salary 24-25 corrected']),
]

plot_df = pd.DataFrame(
    {
        "Year": years * 2,
        "Amount": original_values + corrected_values,
        "Type": ["Original"] * 4 + ["Corrected"] * 4,
    }
)

st.subheader("Salary by Year")
# If all yearly values match, show a single green line; otherwise show both
all_equal = all(np.isclose(original_values[i], corrected_values[i]) for i in range(len(years)))
if all_equal:
    single_df = pd.DataFrame({"Year": years, "Amount": original_values})
    single_chart = (
        alt.Chart(single_df)
        .mark_line(point=True, strokeWidth=3, color="#2ca02c")
        .encode(
            x=alt.X("Year:N", sort=years, title="School Year"),
            y=alt.Y("Amount:Q", title="Salary ($)"),
            tooltip=["Year", alt.Tooltip("Amount", format=",")],
        )
        .properties(title=f"Salary by Year — Employee ID: {selected_id}")
    )
    st.altair_chart(single_chart, use_container_width=True)
else:
    # Dynamic color scale: red if we owe, green if not
    orig_color = "#d62728" if owe_flag else "#2ca02c"
    corr_color = "#2ca02c" if owe_flag else "#1f77b4"
    color_scale = alt.Scale(domain=["Original", "Corrected"], range=[orig_color, corr_color])
    line_chart = (
        alt.Chart(plot_df)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X("Year:N", sort=years, title="School Year"),
            y=alt.Y("Amount:Q", title="Salary ($)"),
            color=alt.Color("Type:N", title="Series", scale=color_scale, sort=["Original", "Corrected"]),
            tooltip=["Year", "Type", alt.Tooltip("Amount", format=",")],
        )
        .properties(title=f"Salary by Year — Employee ID: {selected_id}")
    )
    st.altair_chart(line_chart, use_container_width=True)


