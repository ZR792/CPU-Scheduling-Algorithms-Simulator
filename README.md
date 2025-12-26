# CPU Scheduling Algorithms Simulator

A desktop-based **Operating System simulator** that visually demonstrates how different **CPU scheduling algorithms** work using **animated Gantt charts**. This project is designed for **academic learning** and **practical understanding** of core OS concepts.

---

## 📌 Project Overview

This simulator helps students understand how CPU scheduling decisions are made by the operating system. Users can select different scheduling algorithms, generate random processes, and observe **real-time animated execution**, including:

- Which process is currently running  
- How **preemption** occurs  
- How scheduling **metrics** are calculated  

The project was developed as part of the **Operating Systems course** for the **Department of Software Engineering, SMIU**.

---

## 🎯 Objectives

- Visualize CPU scheduling algorithms in an interactive way  
- Understand process execution, preemption, and context switching  
- Calculate and analyze scheduling metrics  
- Bridge the gap between **theoretical OS concepts** and **practical behavior**

---

## ⚙️ Implemented Scheduling Algorithms

### 🔹 First Come First Serve (FCFS)

### 🔹 Shortest Job First (SJF)
- Non-Preemptive  
- Preemptive (Shortest Remaining Time First)

### 🔹 Priority Scheduling
- Non-Preemptive  
- Preemptive  

### 🔹 Round Robin (RR)

---

## ✨ Key Features

- 🎞️ **Animated Gantt Chart** using PyQt5 (`QPainter` & `QTimer`)
- 🎯 Highlights the currently running process
- 🔄 Visualizes **preemption** and **priority-based switching**
- 📊 Automatically generates a **process statistics table**:
  - Arrival Time  
  - Burst Time  
  - Completion Time  
  - Turnaround Time (TAT)  
  - Waiting Time  
  - Response Time
- 🎨 Color-coded processes for better visualization
- 🧠 Randomized process generation for realistic simulation
- 🖱️ Interactive UI with algorithm selection

---

## 🧰 Technologies Used

### Programming Language
- Python 3.12

### GUI Framework
- PyQt5  
  - QWidget  
  - QPainter  
  - QTimer  
  - Signals & Slots

### Core Concepts
- CPU Scheduling Algorithms  
- Gantt Chart Visualization  
- Event-driven GUI Programming  

---

## 📁 Project Structure
````
CPU-Scheduling-Algorithms-Simulator/
│
├── src/
│ ├── hmain.py # Main application & UI logic
│ ├── animation_widget.py # Gantt chart animation engine
│ ├── scheduler.py # Scheduling algorithms logic
│ └── utils.py # Process data model
│ └── gantt.py
│
├── README.md
└── requirements.txt
└── .gitignore
````


---

## ▶️ How to Run the Project

### 1️⃣ Install Python
Ensure Python **3.8 or higher** is installed:
```bash
python --version
```

### 2️⃣ Install dependencies

``
pip install - requirements.txt
``

### 3️⃣ Run the Simulator

``
pyhton src/hmain.py
``

## 🧪 How to Use the Simulator

- Launch the application
- Select a CPU scheduling algorithm
- Generate random processes
- Start the simulation

### Observe:

- Animated execution
- Process switching
- Gantt chart timeline
- View the generated process statistics table after completion

### 📚 Learning Outcomes

- Clear understanding of CPU scheduling behavior
- Visual grasp of preemption vs non-preemption
- Ability to analyze algorithm performance
-  Practical exposure to operating system internals

### 👨‍🎓 Academic Information

- **Course:** *Operating Systems*
- **Department:** *Software Engineering*
- **University:** *SMIU*

## 👥 Group Members

- **(Zainab Ramzan)[https://github.com/ZR792]**  
- **(Hafsa Rahman)[https://github.com/HafsaRahman05]**  
- **(Alishba Shabbir)[https://github.com/alishba25-alish]**  

### 📄 License

- This project is developed for academic purposes only.
