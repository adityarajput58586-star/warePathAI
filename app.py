import os
import logging
import json
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from optimization import WarehouseOptimizer
from picking_optimizer import PickingPathOptimizer

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "warehouse-optimizer-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///warehouse.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()

@app.route('/')
def index():
    """Main warehouse optimization interface"""
    return render_template('index.html')

@app.route('/api/optimize', methods=['POST'])
def optimize_layout():
    """API endpoint to optimize warehouse layout"""
    try:
        data = request.get_json()
        
        # Validate input data
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract warehouse dimensions
        warehouse = data.get('warehouse', {})
        if not all(k in warehouse for k in ['length', 'width', 'height']):
            return jsonify({'error': 'Warehouse dimensions (length, width, height) are required'}), 400
        
        # Extract storage items
        items = data.get('items', [])
        if not items:
            return jsonify({'error': 'At least one storage item is required'}), 400
        
        # Validate items
        for i, item in enumerate(items):
            required_fields = ['name', 'length', 'width', 'height', 'quantity']
            if not all(k in item for k in required_fields):
                return jsonify({'error': f'Item {i+1} missing required fields: {required_fields}'}), 400
        
        # Get optimization algorithm
        algorithm = data.get('algorithm', 'bin_packing')
        
        # Get enhanced options
        use_ml_prediction = data.get('use_ml_prediction', True)
        storage_types = data.get('storage_types', [])
        
        # Create optimizer instance
        optimizer = WarehouseOptimizer(
            warehouse_length=float(warehouse['length']),
            warehouse_width=float(warehouse['width']),
            warehouse_height=float(warehouse['height'])
        )
        
        # Run optimization with enhanced features
        result = optimizer.optimize(items, algorithm, use_ml_prediction, storage_types)
        
        # Store result in session for potential export
        session['last_optimization'] = result
        
        return jsonify(result)
        
    except ValueError as e:
        app.logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Optimization error: {str(e)}")
        return jsonify({'error': 'Internal server error during optimization'}), 500

@app.route('/api/export', methods=['GET'])
def export_layout():
    """Export the last optimization result"""
    try:
        result = session.get('last_optimization')
        if not result:
            return jsonify({'error': 'No optimization result to export'}), 400
        
        # Generate export data
        export_data = {
            'timestamp': result.get('timestamp'),
            'warehouse_dimensions': result.get('warehouse_dimensions'),
            'optimization_summary': result.get('summary'),
            'placed_items': result.get('placed_items'),
            'utilization_metrics': result.get('metrics')
        }
        
        return jsonify(export_data)
        
    except Exception as e:
        app.logger.error(f"Export error: {str(e)}")
        return jsonify({'error': 'Failed to export layout'}), 500

@app.route('/api/algorithms', methods=['GET'])
def get_algorithms():
    """Get available optimization algorithms"""
    algorithms = [
        {
            'id': 'bin_packing',
            'name': 'Bin Packing (First Fit Decreasing)',
            'description': 'Places largest items first in available spaces'
        },
        {
            'id': 'space_filling',
            'name': 'Space-Filling Curves',
            'description': 'Uses mathematical curves to maximize space utilization'
        },
        {
            'id': 'hybrid',
            'name': 'Hybrid Optimization',
            'description': 'Combines multiple algorithms for optimal results'
        },
        {
            'id': 'ml_enhanced',
            'name': 'ML-Enhanced Optimization',
            'description': 'Uses machine learning to optimize based on turnover and access patterns'
        },
        {
            'id': 'auto',
            'name': 'Auto-Select (ML Prediction)',
            'description': 'Automatically selects the best algorithm using machine learning'
        }
    ]
    return jsonify(algorithms)

@app.route('/api/storage-types', methods=['GET'])
def get_storage_types():
    """Get available storage types"""
    try:
        # Query storage types from database
        storage_types = models.StorageType.query.all()
        
        if not storage_types:
            # Return default storage types if none in database
            default_types = [
                {
                    'id': 1,
                    'name': 'Standard Pallet Racking',
                    'type_category': 'pallet',
                    'load_capacity': 1000.0,
                    'accessibility': 'forklift',
                    'dimensions': {'length': 2.4, 'width': 1.2, 'height': 2.0},
                    'constraints': {'ground_level': True, 'forklift_access': True}
                },
                {
                    'id': 2,
                    'name': 'Heavy Duty Shelving',
                    'type_category': 'shelving',
                    'load_capacity': 500.0,
                    'accessibility': 'manual',
                    'dimensions': {'length': 2.0, 'width': 0.6, 'height': 2.5},
                    'constraints': {'manual_access': True, 'small_items_only': True}
                },
                {
                    'id': 3,
                    'name': 'Bulk Storage Area',
                    'type_category': 'bulk',
                    'load_capacity': 5000.0,
                    'accessibility': 'automated',
                    'dimensions': {'length': 10.0, 'width': 5.0, 'height': 3.0},
                    'constraints': {'large_items_only': True, 'automated_handling': True}
                }
            ]
            return jsonify(default_types)
        
        return jsonify([storage_type.to_dict() for storage_type in storage_types])
        
    except Exception as e:
        app.logger.error(f"Error getting storage types: {str(e)}")
        return jsonify({'error': 'Failed to retrieve storage types'}), 500

@app.route('/api/optimize-picking', methods=['POST'])
def optimize_picking():
    """Optimize picking path for selected items"""
    try:
        data = request.get_json()
        
        if not data or 'placed_items' not in data:
            return jsonify({'error': 'No placed items provided'}), 400
        
        placed_items = data['placed_items']
        pick_list = data.get('pick_list', [])
        warehouse_dims = data.get('warehouse_dimensions', {})
        
        # Create picking optimizer
        picking_optimizer = PickingPathOptimizer(
            warehouse_dims.get('length', 50),
            warehouse_dims.get('width', 30),
            warehouse_dims.get('height', 8)
        )
        
        # Optimize picking path
        picking_result = picking_optimizer.optimize_picking_path(placed_items, pick_list)
        
        return jsonify(picking_result)
        
    except Exception as e:
        app.logger.error(f"Picking optimization error: {str(e)}")
        return jsonify({'error': 'Failed to optimize picking path'}), 500

@app.route('/api/workflow-analysis', methods=['POST'])
def analyze_workflow():
    """Analyze workflow efficiency for current layout"""
    try:
        data = request.get_json()
        
        if not data or 'placed_items' not in data:
            return jsonify({'error': 'No placed items provided'}), 400
        
        placed_items = data['placed_items']
        warehouse_dims = data.get('warehouse_dimensions', {})
        
        # Create picking optimizer for workflow analysis
        picking_optimizer = PickingPathOptimizer(
            warehouse_dims.get('length', 50),
            warehouse_dims.get('width', 30),
            warehouse_dims.get('height', 8)
        )
        
        # Analyze workflow
        workflow_efficiency = picking_optimizer.calculate_workflow_efficiency(placed_items)
        zone_optimization = picking_optimizer.optimize_zone_layout(placed_items)
        
        return jsonify({
            'workflow_efficiency': workflow_efficiency,
            'zone_optimization': zone_optimization
        })
        
    except Exception as e:
        app.logger.error(f"Workflow analysis error: {str(e)}")
        return jsonify({'error': 'Failed to analyze workflow'}), 500

@app.route('/api/ml-insights', methods=['POST'])
def get_ml_insights():
    """Get ML insights for warehouse optimization"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        warehouse_config = data.get('warehouse', {})
        items = data.get('items', [])
        
        # Create ML predictor
        from ml_predictor import MachineLearningPredictor
        ml_predictor = MachineLearningPredictor()
        
        # Get ML insights
        seasonal_predictions = ml_predictor.predict_seasonal_demand(items)
        turnover_predictions = ml_predictor.calculate_turnover_predictions(items)
        algorithm_recommendation = ml_predictor.predict_optimal_algorithm(warehouse_config, items)
        
        return jsonify({
            'seasonal_predictions': seasonal_predictions,
            'turnover_predictions': turnover_predictions,
            'algorithm_recommendation': algorithm_recommendation
        })
        
    except Exception as e:
        app.logger.error(f"ML insights error: {str(e)}")
        return jsonify({'error': 'Failed to generate ML insights'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
