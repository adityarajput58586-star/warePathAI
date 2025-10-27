from app import db
from datetime import datetime
import json

class OptimizationSession(db.Model):
    """Model to store optimization sessions"""
    id = db.Column(db.Integer, primary_key=True)
    warehouse_length = db.Column(db.Float, nullable=False)
    warehouse_width = db.Column(db.Float, nullable=False)
    warehouse_height = db.Column(db.Float, nullable=False)
    algorithm_used = db.Column(db.String(50), nullable=False)
    utilization_percentage = db.Column(db.Float)
    total_items_placed = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    layout_data = db.Column(db.Text)  # JSON string of layout result
    
    def __repr__(self):
        return f'<OptimizationSession {self.id}: {self.utilization_percentage}% utilization>'

class StorageItem(db.Model):
    """Model to store storage item templates"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    length = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float)
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'weight': self.weight,
            'category': self.category
        }
    
    def __repr__(self):
        return f'<StorageItem {self.name}: {self.length}x{self.width}x{self.height}>'

class StorageType(db.Model):
    """Model for different storage configurations"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type_category = db.Column(db.String(50), nullable=False)  # 'pallet', 'shelving', 'bulk'
    load_capacity = db.Column(db.Float)  # kg
    accessibility = db.Column(db.String(50))  # 'forklift', 'manual', 'automated'
    dimensions = db.Column(db.Text)  # JSON string for complex dimensions
    constraints = db.Column(db.Text)  # JSON string for placement constraints
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type_category': self.type_category,
            'load_capacity': self.load_capacity,
            'accessibility': self.accessibility,
            'dimensions': json.loads(self.dimensions) if self.dimensions else {},
            'constraints': json.loads(self.constraints) if self.constraints else {}
        }

class HistoricalData(db.Model):
    """Model to store historical optimization data for ML training"""
    id = db.Column(db.Integer, primary_key=True)
    warehouse_config = db.Column(db.Text, nullable=False)  # JSON string
    item_mix = db.Column(db.Text, nullable=False)  # JSON string
    algorithm_used = db.Column(db.String(50), nullable=False)
    performance_metrics = db.Column(db.Text)  # JSON string
    seasonal_factor = db.Column(db.Float)
    turnover_rate = db.Column(db.Float)
    operational_efficiency = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'warehouse_config': json.loads(self.warehouse_config),
            'item_mix': json.loads(self.item_mix),
            'algorithm_used': self.algorithm_used,
            'performance_metrics': json.loads(self.performance_metrics) if self.performance_metrics else {},
            'seasonal_factor': self.seasonal_factor,
            'turnover_rate': self.turnover_rate,
            'operational_efficiency': self.operational_efficiency,
            'created_at': self.created_at.isoformat()
        }

class PickingPath(db.Model):
    """Model to store optimized picking paths"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('optimization_session.id'), nullable=False)
    path_data = db.Column(db.Text)  # JSON string of path coordinates
    total_distance = db.Column(db.Float)
    estimated_time = db.Column(db.Float)  # minutes
    path_efficiency = db.Column(db.Float)  # percentage
    picking_zones = db.Column(db.Text)  # JSON string of zones
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'path_data': json.loads(self.path_data) if self.path_data else [],
            'total_distance': self.total_distance,
            'estimated_time': self.estimated_time,
            'path_efficiency': self.path_efficiency,
            'picking_zones': json.loads(self.picking_zones) if self.picking_zones else []
        }
