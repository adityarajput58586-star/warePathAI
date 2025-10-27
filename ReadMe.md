# AI Warehouse Layout Optimizer

## Overview

This is a Flask-based web application that provides AI-powered warehouse layout optimization. The system helps users maximize storage capacity by intelligently placing items within warehouse spaces using various optimization algorithms including bin packing, space filling, and hybrid approaches.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology**: HTML5 with Bootstrap 5 (dark theme)
- **Interactive Canvas**: HTML5 Canvas for 2D/3D warehouse visualization
- **JavaScript**: Vanilla JavaScript for client-side interactions and canvas rendering
- **Styling**: Custom CSS with Bootstrap components for responsive design
- **Icons**: Font Awesome for UI icons

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database ORM**: SQLAlchemy with declarative base
- **Session Management**: Flask sessions with configurable secret key
- **Middleware**: ProxyFix for handling proxy headers
- **Logging**: Built-in Python logging configured for debugging

### Core Components
1. **Web Application** (`app.py`): Main Flask application with route definitions
2. **Data Models** (`models.py`): SQLAlchemy models for data persistence
3. **Optimization Engine** (`optimization.py`): AI algorithms for layout optimization
4. **Frontend Interface** (`templates/`, `static/`): User interface and interactions

## Key Components

### Database Models
- **OptimizationSession**: Stores optimization results with warehouse dimensions, algorithm used, utilization metrics, and layout data as JSON
- **StorageItem**: Template storage for reusable item configurations with dimensions, weight, and categorization

### Optimization Algorithms
- **Bin Packing**: Traditional space-efficient packing algorithm
- **Space Filling**: Algorithm focused on maximizing space utilization
- **Hybrid**: Combined approach leveraging multiple strategies
- **3D Grid System**: Uses occupancy grid with configurable resolution (0.5m default) for precise space tracking

### API Structure
- **POST /api/optimize**: Main optimization endpoint accepting warehouse dimensions and item specifications
- **GET /**: Main interface serving the optimization dashboard

## Data Flow

1. **User Input**: Warehouse dimensions and item specifications entered via web interface
2. **Validation**: Server-side validation of input parameters
3. **Optimization**: Selected algorithm processes items using 3D grid-based space tracking
4. **Visualization**: Results rendered on HTML5 canvas with 2D/3D view options
5. **Persistence**: Optimization sessions stored in database for future reference
6. **Export**: Results can be exported for external use

## External Dependencies

### Python Packages
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and modeling
- **NumPy**: Numerical computations for optimization algorithms
- **Werkzeug**: WSGI utilities and middleware

### Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome 6**: Icon library
- **HTML5 Canvas**: For warehouse layout visualization

### Development Tools
- **Replit Bootstrap Theme**: Consistent dark theme styling
- **CDN Dependencies**: External CSS/JS libraries loaded via CDN

## Deployment Strategy

### Database Configuration
- **Development**: SQLite database (`warehouse.db`)
- **Production**: Configurable via `DATABASE_URL` environment variable
- **Connection Management**: Pool recycling and pre-ping enabled for reliability

### Environment Variables
- **SESSION_SECRET**: Flask session encryption key
- **DATABASE_URL**: Database connection string
- **Logging Level**: Configurable via Python logging

### Application Structure
- **Entry Point**: `main.py` imports and runs the Flask app
- **Auto-initialization**: Database tables created automatically on startup
- **Static Assets**: Served via Flask's static file handling
- **Template Rendering**: Jinja2 templating with base template inheritance

### Scalability Considerations
- **Grid Resolution**: Configurable for balancing accuracy vs. performance
- **Session Storage**: Database-backed for multi-instance deployment
- **Algorithm Selection**: Multiple optimization strategies for different use cases
- **3D Visualization**: Client-side rendering to reduce server load

## Recent Changes: Latest modifications with dates

### 1-Meter Distance Constraint Implementation (September 23, 2025)
- **Object Type Classification**: Added intelligent categorization system that identifies object types from item names
- **Distance Constraint Engine**: Implemented 1-meter minimum distance enforcement between different object types
- **Same-Type Stacking**: Only items of the same type can be stacked together without distance constraints
- **3D Bounding Box Distance Calculation**: Precise distance measurement using 3D box-to-box calculations
- **Enhanced Placement Logic**: Updated all optimization algorithms to respect type-based distance constraints
- **Comprehensive Testing**: Validated with multiple object types showing 100% compliance (0 violations/25 checks)
- **Type Categories**: Supports box, pallet, drum, rack, machinery, hazmat, and custom type classification
- **Stacking Rules**: Same-type items (box↔box, pallet↔pallet) can stack; different types maintain 1m+ separation
- **Performance**: Distance constraint checking integrated efficiently without impacting placement performance

### Machine Learning Integration (July 25, 2025)
- **ML Predictor Module**: Added `ml_predictor.py` with predictive optimization capabilities
- **Seasonal Demand Prediction**: Algorithms predict seasonal patterns for inventory planning
- **Turnover Rate Analysis**: ML calculates item turnover rates and optimal placement zones
- **Algorithm Recommendation**: System automatically recommends best optimization algorithm
- **Storage Type Optimization**: Enhanced compatibility matching between items and storage types

### Picking Path Optimization (July 25, 2025)
- **Picking Path Calculator**: Added `picking_optimizer.py` for workflow optimization
- **Zone-Based Optimization**: Warehouse divided into high/medium/low access zones
- **Path Efficiency**: Calculates optimal picking routes using modified TSP algorithms
- **Workflow Analysis**: Comprehensive efficiency metrics and bottleneck identification
- **Traffic Pattern Analysis**: Predicts and optimizes warehouse traffic flow

### Enhanced API Endpoints (July 25, 2025)
- **ML Insights API**: `/api/ml-insights` for seasonal and turnover predictions
- **Picking Optimization**: `/api/optimize-picking` for path optimization
- **Workflow Analysis**: `/api/workflow-analysis` for efficiency metrics
- **Storage Types**: `/api/storage-types` for different storage configurations
- **Enhanced Algorithms**: Added ML-enhanced and auto-select algorithm options

### Extended Database Models (July 25, 2025)
- **StorageType**: Model for different storage configurations (pallets, shelving, bulk)
- **HistoricalData**: Model for storing optimization history for ML training
- **PickingPath**: Model for storing optimized picking paths and efficiency metrics