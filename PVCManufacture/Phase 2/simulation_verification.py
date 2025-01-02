import openpyxl
from openpyxl.styles import Font

# Create a new workbook
workbook = openpyxl.Workbook()
sheet = workbook.active
sheet.title = "Simulation Verification"

# Define column headers
headers = [
    "Day", "Shift", "Start Time", "End Time", "Effective Hours", "Downtime (min)", 
    "Production Rate (kg/hour)", "Operator Productivity", "Net Production (kg)", 
    "Cumulative Production (kg)"
]

# Write headers to the first row
for col, header in enumerate(headers, start=1):
    sheet.cell(row=1, column=col).value = header
    sheet.cell(row=1, column=col).font = Font(bold=True)

# Inputs for calculations
production_rate = 100  # kg/hour
operator_productivity = 0.85
actual_demand = 5000  # kg
shifts = [
    {"shift": 1, "start_time": "00:00", "end_time": "08:00", "hours": 8},
    {"shift": 2, "start_time": "08:00", "end_time": "16:00", "hours": 8},
    {"shift": 3, "start_time": "16:00", "end_time": "23:59", "hours": 8}
]

# Initialize cumulative production
cumulative_production = 0
row = 2  # Start from the second row

# Simulate shifts
day = 1
while cumulative_production < actual_demand:
    for shift in shifts:
        if cumulative_production >= actual_demand:
            break

        # Calculate effective hours and production
        effective_hours = shift["hours"] * operator_productivity
        downtime = 0  # Replace with actual downtime if needed
        net_production = (production_rate * effective_hours) - (downtime / 60 * production_rate)
        cumulative_production += net_production

        # Write data to the sheet
        sheet.cell(row=row, column=1).value = day
        sheet.cell(row=row, column=2).value = shift["shift"]
        sheet.cell(row=row, column=3).value = shift["start_time"]
        sheet.cell(row=row, column=4).value = shift["end_time"]
        sheet.cell(row=row, column=5).value = effective_hours
        sheet.cell(row=row, column=6).value = downtime
        sheet.cell(row=row, column=7).value = production_rate
        sheet.cell(row=row, column=8).value = operator_productivity
        sheet.cell(row=row, column=9).value = net_production
        sheet.cell(row=row, column=10).value = cumulative_production

        row += 1
    day += 1

# Save the workbook
workbook.save("Simulation_Verification.xlsx")
print("Excel file created: Simulation_Verification.xlsx")