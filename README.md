# Drone Surveillance System Setup Guide

## System Design
![picture1](systemdesign.png)

## Project Structure
```
drone-surveillance-system/
├── frontend/                   # react frontend application
│   ├── public/
│   │   └── assets/
│   │       └── drone-icon.svg
│   ├── src/
│   │   ├── main.jsx          # application entry point
│   │   ├── App.jsx           # root component
│   │   ├── components/
│   │   │   ├── ui/          # shadcn/ui components
│   │   │   │   ├── alert.jsx
│   │   │   │   ├── badge.jsx
│   │   │   │   └── card.jsx
│   │   │   ├── theme-provider.jsx
│   │   │   ├── MapDashboard.jsx
│   │   │   ├── EventsList.jsx
│   │   │   └── EventDetails.jsx
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   └── eventService.js
│   │   ├── hooks/
│   │   │   └── useEvents.js
│   │   ├── utils/
│   │   │   ├── constants.js
│   │   │   └── geoUtils.js
│   │   └── styles/
│   │       └── index.css
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── server/                    # fastAPI backend server
│   ├── main.py               # server entry point
│   ├── database.py
│   ├── models.py
│   └── api/
│       └── routes/
│           ├── events.py
│           └── analytics.py
│
├── drone/                     # drone control system
│   ├── main.py               # drone controller
│   ├── video_processor.py    # YOLO processing
│   ├── geospatial.py        # location processing
│   ├── llm_processor.py     # Gemma + Langchain
│   └── data_transmitter.py  # data transmission
│
├── models/                    # AI Models
│   ├── yolo/
│   │   └── best.pt          # YOLO weights
│   └── gemma/               # Gemma model files
│
├── data/                     # data storage
│   ├── terrain.tif          # terrain data
│   └── land_use.gpkg        # land use data
│
├── requirements.txt          
└── README.md
```

## Setup Instructions
clone this repo

### 1. Environment Setup

```bash
# create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# install Python dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
# navigate to frontend directory
cd frontend

# install dependencies
npm install

# install additional required packages
npm install @radix-ui/react-alert @radix-ui/react-badge lucide-react class-variance-authority clsx tailwind-merge tailwindcss-animate
```

### 3. Configuration

Create a `.env` file in the root directory:
```env
# Backend settings
BACKEND_HOST=localhost
BACKEND_PORT=8000

# Drone settings
YOLO_MODEL_PATH=./models/yolo/best.pt
GEMMA_MODEL_PATH=./models/gemma
VIDEO_SOURCE=0  # 0 for webcam, or video file path

# Database settings
DATABASE_URL=postgresql://username:password@host:port/database_name
```

### 4. Starting the System

1. Start the Backend Server:
```bash
cd server
uvicorn main:app --reload --port 8000
```

2. Start the Frontend Development Server:
```bash
cd frontend
npm run dev
```

3. Start the Drone Simulation:
```bash
cd drone
python main.py
```

## Development Workflow

### Frontend Development
1. The frontend runs on `http://localhost:5173`
2. Components are in `frontend/src/components`
3. Use shadcn/ui components from `components/ui`
4. Styles are managed with Tailwind CSS

### Backend Development
1. The API runs on `http://localhost:8000`
2. API documentation at `http://localhost:8000/docs`
3. Add new routes in `server/api/routes`
4. Use FastAPI dependency injection for services

### Drone System Development
1. YOLO model processing in `drone/video_processor.py`
2. Geospatial processing in `drone/geospatial.py`
3. LLM analysis in `drone/llm_processor.py`
4. Event transmission in `drone/data_transmitter.py`

## Available Scripts

### Frontend
```bash
npm run dev          
npm run build       
npm run preview      
npm run lint        
```

### Backend
```bash
uvicorn main:app --reload             
uvicorn main:app --host 0.0.0.0        
python -m pytest tests/                 
```

### Drone System
```bash
python main.py                   
python main.py --simulate        
python main.py --debug         
```

## Adding New Features

1. Frontend Components:
   - Create component in `frontend/src/components`
   - Add styles using Tailwind classes
   - Update API services if needed

2. Backend Endpoints:
   - Add route in `server/api/routes`
   - Update models in `server/models.py`
   - Add tests in `tests/`

3. Drone Features:
   - Add processing modules in `drone/`
   - Update main controller as needed
   - Add new data transmission handlers

## Common Issues and Solutions

1. CORS Issues:
   - Check frontend API endpoint configuration
   - Verify CORS settings in FastAPI

2. Model Loading:
   - Ensure model paths are correct
   - Check CUDA availability for GPU usage

3. Video Processing:
   - Verify camera/video source availability
   - Check OpenCV installation

4. Database:
   - Ensure proper permissions for SQLite file
   - Check database migrations