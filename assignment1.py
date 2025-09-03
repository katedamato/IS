import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt 
import seaborn as sns
import plotly.express as px

#Download Data 
lf = pd.read_csv("https://vincentarelbundock.github.io/Rdatasets/csv/sampleSelection/Mroz87.csv", index_col=0)
print(lf.head())

# Fixing issues..
print(lf.columns)
lf_workeda = lf[lf['hours'] > 0]

import os
print(os.getcwd())


### Visualize with 3 different packages 
#Hello 

#Matplotlib 

plt.scatter(lf_worked['kids5'], lf_worked['hours'], alpha=0.6, color='teal')
plt.title("Women's Work Hours vs. Number of Children Under 5")
plt.xlabel("Number of Children under 5")
plt.xticks(range(0, 3, 1))
plt.ylabel("Hours Worked in 1975")
plt.grid(True)
plt.show()

plt.savefig("Matplotlib.png")
print("Plot saved as Matplotlib.png")

#Seaborn 
sns.boxplot(x='kids5', y='hours', data=lf, palette="pastel")
plt.title("Distribution of Work Hours by Number of Children Under 5")
plt.xlabel("Number of Children under 5")
plt.ylabel("Hours Worked in 1975")
plt.show()

plt.savefig("Seaborn.png")
print("Plot saved as Seaborn.png")

#Plotly 
fig = px.scatter(lf, x="kids5", y="hours", color="faminc", title="Women's Work Hours vs. Number of Children Under 5", labels={'kids5':'Number of Children Under 5', 'hours':'Hours Worked in 1975'}, hover_data=['age','educ','wage'])
fig.show()

fig.write_html("Plotly.html")


