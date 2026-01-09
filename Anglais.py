import matplotlib.pyplot as plt

# Data for the total fleet
categories_en = [
    "Retirees",
    "Business Owners / Executives",
    "Intermediate Professions",
    "Employees / Workers",
    "Others / Inactive"
]

stock_values = [275000, 71500, 55000, 121000, 33000]

# Create the pie chart
plt.figure(figsize=(6, 6))
plt.pie(stock_values, labels=categories_en, autopct='%1.1f%%', startangle=140)
plt.title("Distribution of Total Vehicle Fleet by Socio-Professional Category (550,000 Vehicles)")
plt.show()
