import numpy as np
import math
import json
from datetime import datetime
from typing import List, Dict, Tuple, Any
from ml_predictor import MachineLearningPredictor
from picking_optimizer import PickingPathOptimizer

class WarehouseOptimizer:
    """AI-powered warehouse layout optimization system"""
    
    def __init__(self, warehouse_length: float, warehouse_width: float, warehouse_height: float):
        self.warehouse_length = warehouse_length
        self.warehouse_width = warehouse_width
        self.warehouse_height = warehouse_height
        self.warehouse_volume = warehouse_length * warehouse_width * warehouse_height
        
        # Grid resolution for space tracking (in meters)
        self.grid_resolution = 0.5
        self.grid_length = int(warehouse_length / self.grid_resolution)
        self.grid_width = int(warehouse_width / self.grid_resolution)
        self.grid_height = int(warehouse_height / self.grid_resolution)
        
        # Initialize 3D occupancy grid
        self.occupancy_grid = np.zeros((self.grid_length, self.grid_width, self.grid_height), dtype=bool)
        
        # Track placed items with their types and positions for distance constraints
        self.placed_items_tracker = []  # List of {'type': str, 'position': tuple, 'bounds': tuple}
        
        # Minimum distance between different object types (in meters)
        self.type_distance_constraint = 1.0
        
        # Initialize ML predictor and picking optimizer
        self.ml_predictor = MachineLearningPredictor()
        self.picking_optimizer = PickingPathOptimizer(warehouse_length, warehouse_width, warehouse_height)
        
    def optimize(self, items: List[Dict], algorithm: str = 'bin_packing', 
                 use_ml_prediction: bool = True, storage_types: List[Dict] | None = None) -> Dict[str, Any]:
        """Main optimization method with ML enhancement"""
        # Reset grid for new optimization
        self.occupancy_grid.fill(False)
        # Reset placed items tracker for distance constraints
        self.placed_items_tracker.clear()
        
        # Prepare warehouse configuration for ML
        warehouse_config = {
            'length': self.warehouse_length,
            'width': self.warehouse_width,
            'height': self.warehouse_height
        }
        
        # Use ML to predict optimal algorithm if enabled
        if use_ml_prediction and algorithm == 'auto':
            algorithm = self.ml_predictor.predict_optimal_algorithm(warehouse_config, items)
        
        # Get ML predictions for enhanced optimization
        seasonal_predictions = self.ml_predictor.predict_seasonal_demand(items)
        turnover_predictions = self.ml_predictor.calculate_turnover_predictions(items)
        
        # Adjust item quantities based on seasonal predictions
        adjusted_items = self._apply_seasonal_adjustments(items, seasonal_predictions)
        
        # Apply storage type optimization if provided
        if storage_types:
            storage_optimization = self.ml_predictor.optimize_for_storage_types(adjusted_items, storage_types)
        else:
            storage_optimization = None
        
        # Prepare items for optimization with ML enhancements
        processed_items = self._prepare_items_with_ml(adjusted_items, turnover_predictions, storage_optimization or {})
        
        # Run selected algorithm
        if algorithm == 'bin_packing':
            result = self._bin_packing_optimization(processed_items)
        elif algorithm == 'space_filling':
            result = self._space_filling_optimization(processed_items)
        elif algorithm == 'hybrid':
            result = self._hybrid_optimization(processed_items)
        elif algorithm == 'ml_enhanced':
            result = self._ml_enhanced_optimization(processed_items, turnover_predictions)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        # Calculate picking path optimization
        picking_optimization = self.picking_optimizer.optimize_picking_path(result)
        workflow_efficiency = self.picking_optimizer.calculate_workflow_efficiency(result)
        zone_optimization = self.picking_optimizer.optimize_zone_layout(result)
        
        # Calculate metrics and prepare response
        optimization_result = self._prepare_enhanced_result(
            result, processed_items, algorithm, picking_optimization, 
            workflow_efficiency, zone_optimization, seasonal_predictions, turnover_predictions
        )
        
        # Store result for ML training
        self.ml_predictor.store_optimization_result(warehouse_config, items, algorithm, optimization_result['metrics'])
        
        return optimization_result
    
    def _get_object_type(self, item_name: str) -> str:
        """Determine object type from item name for distance constraint"""
        # Convert item name to lowercase for consistent comparison
        name_lower = item_name.lower()
        
        # Define object type categories
        if any(keyword in name_lower for keyword in ['box', 'carton', 'package', 'crate']):
            return 'box'
        elif any(keyword in name_lower for keyword in ['pallet', 'skid']):
            return 'pallet'
        elif any(keyword in name_lower for keyword in ['drum', 'barrel', 'container']):
            return 'drum'
        elif any(keyword in name_lower for keyword in ['rack', 'shelf', 'frame']):
            return 'rack'
        elif any(keyword in name_lower for keyword in ['machinery', 'equipment', 'machine']):
            return 'machinery'
        elif any(keyword in name_lower for keyword in ['hazmat', 'chemical', 'dangerous']):
            return 'hazmat'
        else:
            # Default: use first word of the item name as type
            return name_lower.split('_')[0].split(' ')[0]
    
    def _prepare_items(self, items: List[Dict]) -> List[Dict]:
        """Prepare and validate items for optimization"""
        processed_items = []
        
        for item in items:
            # Create individual items based on quantity
            for i in range(int(item['quantity'])):
                processed_item = {
                    'id': f"{item['name']}_{i+1}",
                    'name': item['name'],
                    'length': float(item['length']),
                    'width': float(item['width']),
                    'height': float(item['height']),
                    'volume': float(item['length']) * float(item['width']) * float(item['height']),
                    'weight': float(item.get('weight', 0)),
                    'placed': False,
                    'position': None,
                    'rotation': 0  # 0, 90, 180, 270 degrees
                }
                processed_items.append(processed_item)
        
        return processed_items
    
    def _apply_seasonal_adjustments(self, items: List[Dict], seasonal_predictions: Dict[str, float]) -> List[Dict]:
        """Apply seasonal demand adjustments to item quantities"""
        adjusted_items = []
        
        for item in items:
            item_copy = item.copy()
            item_name = item['name']
            seasonal_factor = seasonal_predictions.get(item_name, 1.0)
            
            # Adjust quantity based on seasonal factor
            original_quantity = item['quantity']
            adjusted_quantity = max(1, int(original_quantity * seasonal_factor))
            item_copy['quantity'] = adjusted_quantity
            item_copy['seasonal_factor'] = seasonal_factor
            
            adjusted_items.append(item_copy)
        
        return adjusted_items
    
    def _prepare_items_with_ml(self, items: List[Dict], turnover_predictions: Dict[str, Dict], 
                              storage_optimization: Dict[str, Any]) -> List[Dict]:
        """Prepare items with ML enhancements"""
        processed_items = []
        
        for item in items:
            # Create individual items based on quantity
            for i in range(int(item['quantity'])):
                processed_item = {
                    'id': f"{item['name']}_{i+1}",
                    'name': item['name'],
                    'length': float(item['length']),
                    'width': float(item['width']),
                    'height': float(item['height']),
                    'volume': float(item['length']) * float(item['width']) * float(item['height']),
                    'weight': float(item.get('weight', 0)),
                    'placed': False,
                    'position': None,
                    'rotation': 0,
                    'seasonal_factor': item.get('seasonal_factor', 1.0),
                    'turnover_prediction': turnover_predictions.get(item['name'], {}),
                    'storage_optimization': storage_optimization.get('item_assignments', {}).get(item['name'])
                }
                processed_items.append(processed_item)
        
        return processed_items
    
    def _ml_enhanced_optimization(self, items: List[Dict], turnover_predictions: Dict[str, Dict]) -> List[Dict]:
        """ML-enhanced optimization algorithm that considers turnover and access patterns"""
        # Sort items by access priority (high turnover items first)
        def get_access_priority(item):
            turnover_data = item.get('turnover_prediction', {})
            return turnover_data.get('access_priority', 0.5)
        
        sorted_items = sorted(items, key=get_access_priority, reverse=True)
        placed_items = []
        
        # Define access zones based on turnover predictions
        high_access_zone = {'x_max': self.warehouse_length * 0.3, 'y_max': self.warehouse_width * 0.4}
        medium_access_zone = {'x_max': self.warehouse_length * 0.6, 'y_max': self.warehouse_width * 0.8}
        
        for item in sorted_items:
            turnover_data = item.get('turnover_prediction', {})
            optimal_zone = turnover_data.get('optimal_zone', 'low_access')
            
            # Find position based on optimal zone
            position = self._find_position_in_zone(item, optimal_zone, high_access_zone, medium_access_zone)
            
            if position:
                item['position'] = position
                item['placed'] = True
                self._mark_space_occupied(item, position)
                placed_items.append(item)
        
        return placed_items
    
    def _find_position_in_zone(self, item: Dict, optimal_zone: str, 
                              high_access_zone: Dict, medium_access_zone: Dict):
        """Find position for item in its optimal zone"""
        item_length = item['length']
        item_width = item['width']
        item_height = item['height']
        item_type = self._get_object_type(item['name'])
        
        # Define search bounds based on zone
        if optimal_zone == 'high_access':
            x_bounds = (0, high_access_zone['x_max'])
            y_bounds = (0, high_access_zone['y_max'])
        elif optimal_zone == 'medium_access':
            x_bounds = (0, medium_access_zone['x_max'])
            y_bounds = (high_access_zone['y_max'], medium_access_zone['y_max'])
        else:  # low_access
            x_bounds = (medium_access_zone['x_max'], self.warehouse_length)
            y_bounds = (0, self.warehouse_width)
        
        # Try different rotations
        rotations = [
            (item_length, item_width, item_height),
            (item_width, item_length, item_height)
        ]
        
        for rotation_dims in rotations:
            rot_length, rot_width, rot_height = rotation_dims
            
            # Check if item fits in warehouse
            if (rot_length > self.warehouse_length or 
                rot_width > self.warehouse_width or 
                rot_height > self.warehouse_height):
                continue
            
            # Scan for available position in zone
            x_start = x_bounds[0]
            x_end = min(x_bounds[1], self.warehouse_length - rot_length + 0.1)
            y_start = y_bounds[0]
            y_end = min(y_bounds[1], self.warehouse_width - rot_width + 0.1)
            
            for x in np.arange(x_start, x_end, self.grid_resolution):
                for y in np.arange(y_start, y_end, self.grid_resolution):
                    for z in np.arange(0, self.warehouse_height - rot_height + 0.1, self.grid_resolution):
                        if self._can_place_item_at_position(rot_length, rot_width, rot_height, float(x), float(y), float(z), item_type):
                            # Update item dimensions for this rotation
                            if rotation_dims != (item_length, item_width, item_height):
                                item['rotation'] = 90
                                item['length'] = rot_length
                                item['width'] = rot_width
                            return (float(x), float(y), float(z))
        
        # If no position found in optimal zone, try general placement
        return self._find_best_position(item)
    
    def _bin_packing_optimization(self, items: List[Dict]) -> List[Dict]:
        """First Fit Decreasing bin packing algorithm"""
        # Sort items by volume (largest first)
        sorted_items = sorted(items, key=lambda x: x['volume'], reverse=True)
        placed_items = []
        
        for item in sorted_items:
            position = self._find_best_position(item)
            if position:
                item['position'] = position
                item['placed'] = True
                self._mark_space_occupied(item, position)
                placed_items.append(item)
        
        return placed_items
    
    def _space_filling_optimization(self, items: List[Dict]) -> List[Dict]:
        """Space-filling curve optimization using Z-order curve"""
        # Sort items by volume
        sorted_items = sorted(items, key=lambda x: x['volume'], reverse=True)
        placed_items = []
        
        # Generate Z-order curve positions
        positions = self._generate_z_order_positions()
        
        for item in sorted_items:
            for pos in positions:
                if self._can_place_item(item, pos):
                    item['position'] = pos
                    item['placed'] = True
                    self._mark_space_occupied(item, pos)
                    placed_items.append(item)
                    break
        
        return placed_items
    
    def _hybrid_optimization(self, items: List[Dict]) -> List[Dict]:
        """Hybrid approach combining bin packing and space filling"""
        # First pass: Use bin packing for large items
        large_items = [item for item in items if item['volume'] > self.warehouse_volume * 0.01]
        small_items = [item for item in items if item['volume'] <= self.warehouse_volume * 0.01]
        
        # Place large items first with bin packing
        placed_large = self._bin_packing_optimization(large_items)
        
        # Place small items with space filling
        placed_small = self._space_filling_optimization(small_items)
        
        return placed_large + placed_small
    
    def _find_best_position(self, item: Dict) -> Tuple[float, float, float] | None:
        """Find the best position for an item using First Fit strategy"""
        item_length = item['length']
        item_width = item['width']
        item_height = item['height']
        item_type = self._get_object_type(item['name'])
        
        # Try different rotations
        rotations = [
            (item_length, item_width, item_height),
            (item_width, item_length, item_height)
        ]
        
        for rotation_dims in rotations:
            rot_length, rot_width, rot_height = rotation_dims
            
            # Check if item fits in warehouse
            if (rot_length > self.warehouse_length or 
                rot_width > self.warehouse_width or 
                rot_height > self.warehouse_height):
                continue
            
            # Scan for available position
            for x in np.arange(0, self.warehouse_length - rot_length + 0.1, self.grid_resolution):
                for y in np.arange(0, self.warehouse_width - rot_width + 0.1, self.grid_resolution):
                    for z in np.arange(0, self.warehouse_height - rot_height + 0.1, self.grid_resolution):
                        if self._can_place_item_at_position(rot_length, rot_width, rot_height, float(x), float(y), float(z), item_type):
                            # Update item dimensions for this rotation
                            if rotation_dims != (item_length, item_width, item_height):
                                item['rotation'] = 90
                                item['length'] = rot_length
                                item['width'] = rot_width
                            return (float(x), float(y), float(z))
        
        return None
    
    def _can_place_item(self, item: Dict, position: Tuple[float, float, float]) -> bool:
        """Check if an item can be placed at a specific position"""
        x, y, z = position
        item_name = item.get('name', '')
        return self._can_place_item_at_position(item['length'], item['width'], item['height'], x, y, z, self._get_object_type(item_name))
    
    def _can_place_item_at_position(self, length: float, width: float, height: float, 
                                  x: float, y: float, z: float, item_type: str | None = None) -> bool:
        """Check if item dimensions fit at position without overlap and respecting type distance constraints"""
        # Convert to grid coordinates
        x_start = int(x / self.grid_resolution)
        y_start = int(y / self.grid_resolution)
        z_start = int(z / self.grid_resolution)
        
        x_end = min(int((x + length) / self.grid_resolution), self.grid_length)
        y_end = min(int((y + width) / self.grid_resolution), self.grid_width)
        z_end = min(int((z + height) / self.grid_resolution), self.grid_height)
        
        # Check bounds
        if x_end > self.grid_length or y_end > self.grid_width or z_end > self.grid_height:
            return False
        
        # Check for collisions
        if np.any(self.occupancy_grid[x_start:x_end, y_start:y_end, z_start:z_end]):
            return False
        
        # Check distance constraint between different object types
        if item_type and self.placed_items_tracker:
            item_bounds = (x, y, z, x + length, y + width, z + height)
            if not self._check_type_distance_constraint(item_type, item_bounds):
                return False
        
        return True
    
    def _check_type_distance_constraint(self, item_type: str, item_bounds: Tuple[float, float, float, float, float, float]) -> bool:
        """Check if placing item would violate distance constraint with all other items (except same type)"""
        x_min, y_min, z_min, x_max, y_max, z_max = item_bounds
        
        for placed_item in self.placed_items_tracker:
            placed_type = placed_item['type']
            placed_bounds = placed_item['bounds']
            
            # Allow close placement only for same type items (can stack together)
            if item_type == placed_type:
                continue
            
            # For all different items (different types), enforce 1m distance constraint
            px_min, py_min, pz_min, px_max, py_max, pz_max = placed_bounds
            
            # Calculate shortest distance between two 3D boxes
            dx = max(0, max(x_min - px_max, px_min - x_max))
            dy = max(0, max(y_min - py_max, py_min - y_max))
            dz = max(0, max(z_min - pz_max, pz_min - z_max))
            
            distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            # If distance is less than constraint, placement not allowed
            if distance < self.type_distance_constraint:
                return False
        
        return True
    
    def _mark_space_occupied(self, item: Dict, position: Tuple[float, float, float]):
        """Mark the space as occupied in the grid and add item to tracker for distance constraints"""
        x, y, z = position
        
        x_start = int(x / self.grid_resolution)
        y_start = int(y / self.grid_resolution)
        z_start = int(z / self.grid_resolution)
        
        x_end = min(int((x + item['length']) / self.grid_resolution), self.grid_length)
        y_end = min(int((y + item['width']) / self.grid_resolution), self.grid_width)
        z_end = min(int((z + item['height']) / self.grid_resolution), self.grid_height)
        
        self.occupancy_grid[x_start:x_end, y_start:y_end, z_start:z_end] = True
        
        # Add item to tracker for distance constraint checking
        item_type = self._get_object_type(item['name'])
        item_bounds = (x, y, z, x + item['length'], y + item['width'], z + item['height'])
        self.placed_items_tracker.append({
            'type': item_type,
            'position': position,
            'bounds': item_bounds
        })
    
    def _generate_z_order_positions(self) -> List[Tuple[float, float, float]]:
        """Generate positions following Z-order curve for better space filling"""
        positions = []
        
        # Simple Z-order curve implementation
        for i in range(0, min(1000, self.grid_length * self.grid_width)):  # Limit iterations
            x = (i & 0x55555555) << 1 | (i & 0xAAAAAAAA) >> 1
            y = (i & 0x33333333) << 2 | (i & 0xCCCCCCCC) >> 2
            z = 0  # Start from ground level
            
            # Convert to actual coordinates
            x_coord = (x % self.grid_length) * self.grid_resolution
            y_coord = (y % self.grid_width) * self.grid_resolution
            z_coord = z * self.grid_resolution
            
            if (x_coord < self.warehouse_length and 
                y_coord < self.warehouse_width and 
                z_coord < self.warehouse_height):
                positions.append((x_coord, y_coord, z_coord))
        
        return positions
    
    def _calculate_metrics(self, placed_items: List[Dict], total_items: List[Dict]) -> Dict[str, float]:
        """Calculate optimization metrics"""
        if not total_items:
            return {'utilization': 0.0, 'efficiency': 0.0, 'items_placed': 0, 'items_total': 0}
        
        total_volume = sum(item['volume'] for item in total_items)
        placed_volume = sum(item['volume'] for item in placed_items)
        
        utilization = (placed_volume / self.warehouse_volume) * 100
        efficiency = (len(placed_items) / len(total_items)) * 100
        
        return {
            'utilization': round(utilization, 2),
            'efficiency': round(efficiency, 2),
            'items_placed': len(placed_items),
            'items_total': len(total_items),
            'volume_used': round(placed_volume, 2),
            'volume_total': round(self.warehouse_volume, 2)
        }
    
    def _prepare_result(self, placed_items: List[Dict], all_items: List[Dict], algorithm: str) -> Dict[str, Any]:
        """Prepare the final optimization result"""
        metrics = self._calculate_metrics(placed_items, all_items)
        
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'algorithm': algorithm,
            'warehouse_dimensions': {
                'length': self.warehouse_length,
                'width': self.warehouse_width,
                'height': self.warehouse_height,
                'volume': self.warehouse_volume
            },
            'metrics': metrics,
            'placed_items': [
                {
                    'id': item['id'],
                    'name': item['name'],
                    'position': {
                        'x': item['position'][0],
                        'y': item['position'][1],
                        'z': item['position'][2]
                    },
                    'dimensions': {
                        'length': item['length'],
                        'width': item['width'],
                        'height': item['height']
                    },
                    'rotation': item['rotation'],
                    'volume': item['volume']
                } for item in placed_items
            ],
            'unplaced_items': [
                {
                    'id': item['id'],
                    'name': item['name'],
                    'dimensions': {
                        'length': item['length'],
                        'width': item['width'],
                        'height': item['height']
                    },
                    'volume': item['volume']
                } for item in all_items if not item['placed']
            ],
            'summary': {
                'total_items': len(all_items),
                'placed_items': len(placed_items),
                'utilization_percentage': metrics['utilization'],
                'space_efficiency': metrics['efficiency']
            }
        }
    
    def _prepare_enhanced_result(self, placed_items: List[Dict], all_items: List[Dict], algorithm: str,
                               picking_optimization: Dict, workflow_efficiency: Dict, zone_optimization: Dict,
                               seasonal_predictions: Dict, turnover_predictions: Dict) -> Dict[str, Any]:
        """Prepare enhanced optimization result with ML and picking insights"""
        # Get basic metrics
        metrics = self._calculate_metrics(placed_items, all_items)
        
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'algorithm': algorithm,
            'warehouse_dimensions': {
                'length': self.warehouse_length,
                'width': self.warehouse_width,
                'height': self.warehouse_height,
                'volume': self.warehouse_volume
            },
            'metrics': metrics,
            'placed_items': [
                {
                    'id': item['id'],
                    'name': item['name'],
                    'position': {
                        'x': item['position'][0],
                        'y': item['position'][1],
                        'z': item['position'][2]
                    },
                    'dimensions': {
                        'length': item['length'],
                        'width': item['width'],
                        'height': item['height']
                    },
                    'rotation': item['rotation'],
                    'volume': item['volume'],
                    'seasonal_factor': item.get('seasonal_factor', 1.0),
                    'turnover_prediction': item.get('turnover_prediction', {}),
                    'storage_optimization': item.get('storage_optimization')
                } for item in placed_items
            ],
            'unplaced_items': [
                {
                    'id': item['id'],
                    'name': item['name'],
                    'dimensions': {
                        'length': item['length'],
                        'width': item['width'],
                        'height': item['height']
                    },
                    'volume': item['volume']
                } for item in all_items if not item['placed']
            ],
            'summary': {
                'total_items': len(all_items),
                'placed_items': len(placed_items),
                'utilization_percentage': metrics['utilization'],
                'space_efficiency': metrics['efficiency']
            },
            'picking_optimization': picking_optimization,
            'workflow_efficiency': workflow_efficiency,
            'zone_optimization': zone_optimization,
            'ml_insights': {
                'seasonal_predictions': seasonal_predictions,
                'turnover_predictions': turnover_predictions,
                'algorithm_recommendation': algorithm
            }
        }
