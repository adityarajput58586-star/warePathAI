import numpy as np
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Any

class MachineLearningPredictor:
    """Machine learning predictor for warehouse optimization"""
    
    def __init__(self):
        self.seasonal_patterns = {}
        self.efficiency_weights = {
            'volume_utilization': 0.3,
            'accessibility': 0.25,
            'picking_efficiency': 0.25,
            'storage_type_match': 0.2
        }
    
    def predict_optimal_algorithm(self, warehouse_config: Dict, items: List[Dict]) -> str:
        """Predict the best optimization algorithm based on historical data"""
        try:
            # Analyze warehouse characteristics
            warehouse_volume = warehouse_config['length'] * warehouse_config['width'] * warehouse_config['height']
            total_item_volume = sum(item['length'] * item['width'] * item['height'] * item['quantity'] for item in items)
            volume_ratio = total_item_volume / warehouse_volume
            
            # Analyze item characteristics
            item_count = sum(item['quantity'] for item in items)
            item_variety = len(set(item['name'] for item in items))
            avg_item_size = total_item_volume / item_count if item_count > 0 else 0
            
            # Get historical performance data
            historical_data = self._get_similar_scenarios(warehouse_config, items)
            
            if historical_data:
                algorithm_scores = self._calculate_algorithm_scores(historical_data)
                return max(algorithm_scores.keys(), key=lambda k: algorithm_scores[k])
            
            # Fallback rules based on characteristics
            if volume_ratio > 0.8:  # High density
                return 'hybrid'
            elif item_variety > 10 and avg_item_size < warehouse_volume / 100:  # Many small items
                return 'space_filling'
            else:
                return 'bin_packing'
                
        except Exception:
            return 'bin_packing'  # Safe default
    
    def predict_seasonal_demand(self, items: List[Dict]) -> Dict[str, float]:
        """Predict seasonal demand patterns for items"""
        current_month = datetime.now().month
        seasonal_factors = {}
        
        for item in items:
            item_name = item['name']
            
            # Simple seasonal patterns (can be enhanced with real data)
            if 'seasonal' in item_name.lower() or 'winter' in item_name.lower():
                seasonal_factors[item_name] = self._get_winter_factor(current_month)
            elif 'summer' in item_name.lower():
                seasonal_factors[item_name] = self._get_summer_factor(current_month)
            else:
                seasonal_factors[item_name] = 1.0  # No seasonal variation
        
        return seasonal_factors
    
    def calculate_turnover_predictions(self, items: List[Dict]) -> Dict[str, Dict]:
        """Calculate predicted turnover rates and optimal placement"""
        turnover_data = {}
        
        for item in items:
            item_name = item['name']
            
            # Analyze item characteristics for turnover prediction
            item_volume = item['length'] * item['width'] * item['height']
            weight = item.get('weight', 0)
            
            # Predict turnover based on size and weight (smaller, lighter items tend to have higher turnover)
            base_turnover = max(0.1, 1.0 - (item_volume / 10.0) - (weight / 1000.0))
            
            # Historical analysis
            historical_turnover = self._get_historical_turnover(item_name)
            if historical_turnover:
                predicted_turnover = (base_turnover + historical_turnover) / 2
            else:
                predicted_turnover = base_turnover
            
            # Determine optimal placement zone
            if predicted_turnover > 0.7:
                placement_zone = 'high_access'  # Near entrance/exits
            elif predicted_turnover > 0.4:
                placement_zone = 'medium_access'  # Middle areas
            else:
                placement_zone = 'low_access'  # Back areas
            
            turnover_data[item_name] = {
                'predicted_turnover': predicted_turnover,
                'optimal_zone': placement_zone,
                'access_priority': predicted_turnover
            }
        
        return turnover_data
    
    def optimize_for_storage_types(self, items: List[Dict], storage_types: List[Dict]) -> Dict[str, Any]:
        """Optimize item placement based on storage type compatibility"""
        optimization_recommendations = {
            'item_assignments': {},
            'storage_efficiency': {},
            'compatibility_scores': {}
        }
        
        for item in items:
            item_name = item['name']
            best_storage_type = None
            best_score = 0
            
            for storage_type in storage_types:
                score = self._calculate_storage_compatibility(item, storage_type)
                
                if score > best_score:
                    best_score = score
                    best_storage_type = storage_type
            
            if best_storage_type:
                optimization_recommendations['item_assignments'][item_name] = {
                    'storage_type': best_storage_type['name'],
                    'compatibility_score': best_score,
                    'efficiency_factors': self._get_efficiency_factors(item, best_storage_type)
                }
        
        return optimization_recommendations
    
    def _get_similar_scenarios(self, warehouse_config: Dict, items: List[Dict]) -> List[Dict]:
        """Find similar historical scenarios"""
        # For now, return empty list until we implement proper database integration
        # This will use fallback rules instead
        return []
    
    def _calculate_algorithm_scores(self, historical_data: List[Dict]) -> Dict[str, float]:
        """Calculate performance scores for each algorithm"""
        algorithm_scores = {'bin_packing': 0.0, 'space_filling': 0.0, 'hybrid': 0.0}
        algorithm_counts = {'bin_packing': 0, 'space_filling': 0, 'hybrid': 0}
        
        for scenario in historical_data:
            algorithm = scenario['algorithm_used']
            efficiency = scenario.get('operational_efficiency', 0.5)
            
            if algorithm in algorithm_scores:
                algorithm_scores[algorithm] += efficiency
                algorithm_counts[algorithm] += 1
        
        # Calculate average scores
        for algorithm in algorithm_scores:
            if algorithm_counts[algorithm] > 0:
                algorithm_scores[algorithm] /= algorithm_counts[algorithm]
            else:
                algorithm_scores[algorithm] = 0.5  # Default score
        
        return algorithm_scores
    
    def _get_winter_factor(self, current_month: int) -> float:
        """Get seasonal factor for winter items"""
        winter_months = [12, 1, 2]
        if current_month in winter_months:
            return 1.5  # Higher demand in winter
        elif current_month in [3, 4, 10, 11]:
            return 1.2  # Moderate demand in transition months
        else:
            return 0.7  # Lower demand in summer
    
    def _get_summer_factor(self, current_month: int) -> float:
        """Get seasonal factor for summer items"""
        summer_months = [6, 7, 8]
        if current_month in summer_months:
            return 1.5  # Higher demand in summer
        elif current_month in [5, 9]:
            return 1.2  # Moderate demand in transition months
        else:
            return 0.7  # Lower demand in winter
    
    def _get_historical_turnover(self, item_name: str) -> float | None:
        """Get historical turnover rate for an item"""
        # Simplified implementation without database queries
        # This would be enhanced with real historical data
        return None
    
    def _calculate_storage_compatibility(self, item: Dict, storage_type: Dict) -> float:
        """Calculate compatibility score between item and storage type"""
        score = 0.0
        
        # Size compatibility
        item_volume = item['length'] * item['width'] * item['height']
        storage_dimensions = storage_type.get('dimensions', {})
        
        if storage_dimensions:
            storage_volume = (storage_dimensions.get('length', 0) * 
                            storage_dimensions.get('width', 0) * 
                            storage_dimensions.get('height', 0))
            
            if storage_volume > 0 and item_volume <= storage_volume:
                size_ratio = item_volume / storage_volume
                score += 0.4 * (1.0 - abs(0.8 - size_ratio))  # Optimal at 80% utilization
        
        # Weight compatibility
        item_weight = item.get('weight', 0)
        load_capacity = storage_type.get('load_capacity', float('inf'))
        
        if item_weight <= load_capacity:
            if load_capacity > 0:
                weight_ratio = item_weight / load_capacity
                score += 0.3 * (1.0 - abs(0.7 - weight_ratio))  # Optimal at 70% capacity
            else:
                score += 0.3
        
        # Category compatibility
        item_category = item.get('category', 'general')
        storage_category = storage_type.get('type_category', 'general')
        
        category_matches = {
            ('pallet', 'pallet'): 1.0,
            ('bulk', 'bulk'): 1.0,
            ('small', 'shelving'): 1.0,
            ('general', 'pallet'): 0.7,
            ('general', 'shelving'): 0.8
        }
        
        category_score = category_matches.get((item_category, storage_category), 0.5)
        score += 0.3 * category_score
        
        return min(1.0, max(0.0, score))
    
    def _get_efficiency_factors(self, item: Dict, storage_type: Dict) -> Dict[str, float]:
        """Get efficiency factors for item-storage type combination"""
        return {
            'access_efficiency': self._calculate_access_efficiency(storage_type),
            'space_utilization': self._calculate_space_utilization(item, storage_type),
            'handling_efficiency': self._calculate_handling_efficiency(item, storage_type)
        }
    
    def _calculate_access_efficiency(self, storage_type: Dict) -> float:
        """Calculate access efficiency for storage type"""
        accessibility = storage_type.get('accessibility', 'manual')
        
        efficiency_map = {
            'automated': 0.95,
            'forklift': 0.85,
            'manual': 0.70
        }
        
        return efficiency_map.get(accessibility, 0.70)
    
    def _calculate_space_utilization(self, item: Dict, storage_type: Dict) -> float:
        """Calculate space utilization efficiency"""
        item_volume = item['length'] * item['width'] * item['height']
        storage_dimensions = storage_type.get('dimensions', {})
        
        if not storage_dimensions:
            return 0.5
        
        storage_volume = (storage_dimensions.get('length', 1) * 
                         storage_dimensions.get('width', 1) * 
                         storage_dimensions.get('height', 1))
        
        if storage_volume > 0:
            utilization = item_volume / storage_volume
            # Optimal utilization is around 75-85%
            if 0.75 <= utilization <= 0.85:
                return 1.0
            elif utilization < 0.75:
                return utilization / 0.75
            else:
                return max(0.1, 1.0 - (utilization - 0.85) * 2)
        
        return 0.5
    
    def _calculate_handling_efficiency(self, item: Dict, storage_type: Dict) -> float:
        """Calculate handling efficiency"""
        item_weight = item.get('weight', 0)
        
        if item_weight < 5:  # Light items
            return 0.9 if storage_type.get('type_category') == 'shelving' else 0.7
        elif item_weight < 50:  # Medium items
            return 0.8 if storage_type.get('accessibility') == 'forklift' else 0.6
        else:  # Heavy items
            return 0.9 if storage_type.get('accessibility') == 'automated' else 0.7
    
    def store_optimization_result(self, warehouse_config: Dict, items: List[Dict], 
                                 algorithm: str, performance_metrics: Dict):
        """Store optimization result for future ML training"""
        # This would store results in database for ML training
        # For now, we'll implement a simplified version
        pass