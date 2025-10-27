import numpy as np
import json
from typing import List, Dict, Tuple, Any
from datetime import datetime
import math

class PickingPathOptimizer:
    """Optimize picking paths for warehouse operations"""
    
    def __init__(self, warehouse_length: float, warehouse_width: float, warehouse_height: float):
        self.warehouse_length = warehouse_length
        self.warehouse_width = warehouse_width
        self.warehouse_height = warehouse_height
        
        # Define warehouse zones
        self.zones = self._define_warehouse_zones()
        
        # Picking parameters
        self.walking_speed = 1.5  # m/s
        self.picking_time = 15  # seconds per item
        self.zone_transition_time = 10  # seconds between zones
    
    def optimize_picking_path(self, placed_items: List[Dict], pick_list: List[str] = None) -> Dict[str, Any]:
        """Optimize picking path for given items"""
        if not pick_list:
            # If no specific pick list, include all items
            pick_list = [item['name'] for item in placed_items]
        
        # Filter items to be picked
        items_to_pick = [item for item in placed_items if item['name'] in pick_list]
        
        if not items_to_pick:
            return self._empty_path_result()
        
        # Calculate optimal path
        optimal_path = self._calculate_optimal_path(items_to_pick)
        
        # Calculate metrics
        total_distance = self._calculate_total_distance(optimal_path['waypoints'])
        estimated_time = self._calculate_picking_time(optimal_path, len(items_to_pick))
        efficiency = self._calculate_path_efficiency(optimal_path, items_to_pick)
        
        # Organize by zones
        picking_zones = self._organize_by_zones(items_to_pick)
        
        return {
            'path_data': optimal_path,
            'total_distance': round(total_distance, 2),
            'estimated_time': round(estimated_time, 2),
            'path_efficiency': round(efficiency, 2),
            'picking_zones': picking_zones,
            'zone_sequence': optimal_path['zone_sequence'],
            'items_to_pick': len(items_to_pick),
            'waypoints': optimal_path['waypoints']
        }
    
    def optimize_zone_layout(self, placed_items: List[Dict]) -> Dict[str, Any]:
        """Optimize zone layout for efficient picking"""
        zone_analysis = {}
        
        for zone_name, zone_data in self.zones.items():
            items_in_zone = self._get_items_in_zone(placed_items, zone_data['bounds'])
            
            zone_analysis[zone_name] = {
                'item_count': len(items_in_zone),
                'density': len(items_in_zone) / self._calculate_zone_area(zone_data['bounds']),
                'access_points': self._calculate_access_points(zone_data['bounds']),
                'avg_picking_time': self._estimate_zone_picking_time(items_in_zone),
                'items': [item['name'] for item in items_in_zone]
            }
        
        # Recommend zone optimizations
        recommendations = self._generate_zone_recommendations(zone_analysis)
        
        return {
            'zone_analysis': zone_analysis,
            'recommendations': recommendations,
            'total_zones': len(self.zones),
            'optimal_flow': self._calculate_optimal_flow(zone_analysis)
        }
    
    def calculate_workflow_efficiency(self, placed_items: List[Dict], 
                                    historical_picks: List[Dict] = None) -> Dict[str, Any]:
        """Calculate overall workflow efficiency metrics"""
        
        # Analyze current layout efficiency
        layout_efficiency = self._analyze_layout_efficiency(placed_items)
        
        # Calculate picking density
        picking_density = self._calculate_picking_density(placed_items)
        
        # Analyze traffic patterns
        traffic_analysis = self._estimate_traffic_patterns(placed_items)
        
        # Calculate bottlenecks
        bottlenecks = self._identify_bottlenecks(placed_items)
        
        return {
            'layout_efficiency': layout_efficiency,
            'picking_density': picking_density,
            'traffic_analysis': traffic_analysis,
            'bottlenecks': bottlenecks,
            'overall_score': self._calculate_overall_efficiency_score(
                layout_efficiency, picking_density, traffic_analysis
            ),
            'improvement_suggestions': self._generate_improvement_suggestions(
                layout_efficiency, traffic_analysis, bottlenecks
            )
        }
    
    def _define_warehouse_zones(self) -> Dict[str, Dict]:
        """Define warehouse zones for picking optimization"""
        return {
            'high_velocity': {
                'bounds': {
                    'x_min': 0, 'x_max': self.warehouse_length * 0.3,
                    'y_min': 0, 'y_max': self.warehouse_width * 0.4
                },
                'priority': 1,
                'access_type': 'high'
            },
            'medium_velocity': {
                'bounds': {
                    'x_min': 0, 'x_max': self.warehouse_length * 0.6,
                    'y_min': self.warehouse_width * 0.4, 'y_max': self.warehouse_width * 0.8
                },
                'priority': 2,
                'access_type': 'medium'
            },
            'low_velocity': {
                'bounds': {
                    'x_min': self.warehouse_length * 0.6, 'x_max': self.warehouse_length,
                    'y_min': 0, 'y_max': self.warehouse_width
                },
                'priority': 3,
                'access_type': 'low'
            },
            'bulk_storage': {
                'bounds': {
                    'x_min': self.warehouse_length * 0.3, 'x_max': self.warehouse_length * 0.6,
                    'y_min': 0, 'y_max': self.warehouse_width * 0.4
                },
                'priority': 4,
                'access_type': 'bulk'
            }
        }
    
    def _calculate_optimal_path(self, items_to_pick: List[Dict]) -> Dict[str, Any]:
        """Calculate optimal picking path using modified TSP approach"""
        if len(items_to_pick) <= 1:
            if items_to_pick:
                return {
                    'waypoints': [items_to_pick[0]['position']],
                    'zone_sequence': [self._get_item_zone(items_to_pick[0])],
                    'path_segments': []
                }
            return {'waypoints': [], 'zone_sequence': [], 'path_segments': []}
        
        # Group items by zones first
        zone_groups = {}
        for item in items_to_pick:
            zone = self._get_item_zone(item)
            if zone not in zone_groups:
                zone_groups[zone] = []
            zone_groups[zone].append(item)
        
        # Optimize sequence of zones
        zone_sequence = self._optimize_zone_sequence(list(zone_groups.keys()))
        
        # Optimize path within each zone
        waypoints = []
        path_segments = []
        
        for zone in zone_sequence:
            zone_items = zone_groups[zone]
            if len(zone_items) == 1:
                waypoints.append(zone_items[0]['position'])
            else:
                # Use nearest neighbor for items within zone
                zone_path = self._nearest_neighbor_path(zone_items)
                waypoints.extend([item['position'] for item in zone_path])
                
                # Add path segments
                for i in range(len(zone_path) - 1):
                    path_segments.append({
                        'from': zone_path[i]['position'],
                        'to': zone_path[i + 1]['position'],
                        'distance': self._calculate_distance(
                            zone_path[i]['position'], zone_path[i + 1]['position']
                        )
                    })
        
        return {
            'waypoints': waypoints,
            'zone_sequence': zone_sequence,
            'path_segments': path_segments
        }
    
    def _get_item_zone(self, item: Dict) -> str:
        """Determine which zone an item belongs to"""
        pos = item['position']
        # Handle both tuple and dict position formats
        if isinstance(pos, tuple):
            x, y = pos[0], pos[1]
        else:
            x, y = pos['x'], pos['y']
        
        for zone_name, zone_data in self.zones.items():
            bounds = zone_data['bounds']
            if (bounds['x_min'] <= x <= bounds['x_max'] and 
                bounds['y_min'] <= y <= bounds['y_max']):
                return zone_name
        
        return 'unassigned'
    
    def _optimize_zone_sequence(self, zones: List[str]) -> List[str]:
        """Optimize the sequence of zones to visit"""
        if len(zones) <= 1:
            return zones
        
        # Sort zones by priority (high velocity first)
        zone_priorities = {zone: self.zones[zone]['priority'] for zone in zones if zone in self.zones}
        
        # For unassigned zones, give them lowest priority
        for zone in zones:
            if zone not in zone_priorities:
                zone_priorities[zone] = 99
        
        return sorted(zones, key=lambda z: zone_priorities.get(z, 99))
    
    def _nearest_neighbor_path(self, items: List[Dict]) -> List[Dict]:
        """Calculate optimal path within a zone using nearest neighbor"""
        if len(items) <= 1:
            return items
        
        unvisited = items.copy()
        path = [unvisited.pop(0)]  # Start with first item
        
        while unvisited:
            current = path[-1]
            nearest = min(unvisited, key=lambda item: self._calculate_distance(
                current['position'], item['position']
            ))
            path.append(nearest)
            unvisited.remove(nearest)
        
        return path
    
    def _calculate_distance(self, pos1, pos2) -> float:
        """Calculate Euclidean distance between two positions"""
        # Handle both tuple and dict position formats
        if isinstance(pos1, tuple):
            x1, y1 = pos1[0], pos1[1]
        else:
            x1, y1 = pos1['x'], pos1['y']
            
        if isinstance(pos2, tuple):
            x2, y2 = pos2[0], pos2[1]
        else:
            x2, y2 = pos2['x'], pos2['y']
            
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    
    def _calculate_total_distance(self, waypoints: List[Dict]) -> float:
        """Calculate total distance of the path"""
        if len(waypoints) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(len(waypoints) - 1):
            total_distance += self._calculate_distance(waypoints[i], waypoints[i + 1])
        
        return total_distance
    
    def _calculate_picking_time(self, path_data: Dict, item_count: int) -> float:
        """Calculate estimated picking time in minutes"""
        # Walking time
        total_distance = self._calculate_total_distance(path_data['waypoints'])
        walking_time = total_distance / self.walking_speed  # seconds
        
        # Picking time
        picking_time = item_count * self.picking_time  # seconds
        
        # Zone transition time
        zone_transitions = len(path_data['zone_sequence']) - 1
        transition_time = zone_transitions * self.zone_transition_time  # seconds
        
        total_time_seconds = walking_time + picking_time + transition_time
        return total_time_seconds / 60  # Convert to minutes
    
    def _calculate_path_efficiency(self, path_data: Dict, items: List[Dict]) -> float:
        """Calculate path efficiency as percentage"""
        if not items:
            return 0.0
        
        # Calculate theoretical minimum distance (as the crow flies)
        positions = [item['position'] for item in items]
        if len(positions) < 2:
            return 100.0
        
        # Minimum spanning tree approximation
        min_distance = self._minimum_spanning_tree_distance(positions)
        actual_distance = self._calculate_total_distance(path_data['waypoints'])
        
        if min_distance == 0:
            return 100.0
        
        efficiency = (min_distance / actual_distance) * 100
        return min(100.0, max(0.0, efficiency))
    
    def _minimum_spanning_tree_distance(self, positions) -> float:
        """Approximate minimum distance using MST"""
        if len(positions) < 2:
            return 0.0
        
        # Handle both tuple and dict position formats
        x_coords = []
        y_coords = []
        
        for pos in positions:
            if isinstance(pos, tuple):
                x_coords.append(pos[0])
                y_coords.append(pos[1])
            else:
                x_coords.append(pos['x'])
                y_coords.append(pos['y'])
        
        # Simple approximation: sum of distances from center point
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)
        center = (center_x, center_y)
        
        return sum(self._calculate_distance(center, pos) for pos in positions)
    
    def _organize_by_zones(self, items: List[Dict]) -> List[Dict]:
        """Organize items by zones"""
        zone_data = {}
        
        for item in items:
            zone = self._get_item_zone(item)
            if zone not in zone_data:
                zone_data[zone] = {
                    'zone_name': zone,
                    'items': [],
                    'item_count': 0,
                    'priority': self.zones.get(zone, {}).get('priority', 99)
                }
            
            zone_data[zone]['items'].append({
                'name': item['name'],
                'position': item['position']
            })
            zone_data[zone]['item_count'] += 1
        
        return list(zone_data.values())
    
    def _get_items_in_zone(self, items: List[Dict], zone_bounds: Dict) -> List[Dict]:
        """Get all items within a specific zone"""
        items_in_zone = []
        
        for item in items:
            pos = item['position']
            # Handle both tuple and dict position formats
            if isinstance(pos, tuple):
                x, y = pos[0], pos[1]
            else:
                x, y = pos['x'], pos['y']
            
            if (zone_bounds['x_min'] <= x <= zone_bounds['x_max'] and 
                zone_bounds['y_min'] <= y <= zone_bounds['y_max']):
                items_in_zone.append(item)
        
        return items_in_zone
    
    def _calculate_zone_area(self, zone_bounds: Dict) -> float:
        """Calculate area of a zone"""
        return ((zone_bounds['x_max'] - zone_bounds['x_min']) * 
                (zone_bounds['y_max'] - zone_bounds['y_min']))
    
    def _calculate_access_points(self, zone_bounds: Dict) -> int:
        """Calculate number of access points for a zone"""
        # Simple heuristic based on zone perimeter
        perimeter = (2 * (zone_bounds['x_max'] - zone_bounds['x_min']) + 
                    2 * (zone_bounds['y_max'] - zone_bounds['y_min']))
        
        # One access point per 10 meters of perimeter
        return max(1, int(perimeter / 10))
    
    def _estimate_zone_picking_time(self, items: List[Dict]) -> float:
        """Estimate average picking time for items in a zone"""
        if not items:
            return 0.0
        
        # Base picking time plus movement within zone
        base_time = len(items) * self.picking_time
        
        # Add movement time within zone (simplified)
        if len(items) > 1:
            avg_distance = 5.0  # Assume 5m average distance between items
            movement_time = (len(items) - 1) * (avg_distance / self.walking_speed)
        else:
            movement_time = 0.0
        
        return (base_time + movement_time) / 60  # Convert to minutes
    
    def _generate_zone_recommendations(self, zone_analysis: Dict) -> List[Dict]:
        """Generate recommendations for zone optimization"""
        recommendations = []
        
        for zone_name, data in zone_analysis.items():
            if data['density'] > 0.5:  # High density
                recommendations.append({
                    'zone': zone_name,
                    'type': 'density_optimization',
                    'message': f'High item density in {zone_name}. Consider expanding or reorganizing.',
                    'priority': 'high'
                })
            
            if data['avg_picking_time'] > 10:  # Long picking time
                recommendations.append({
                    'zone': zone_name,
                    'type': 'efficiency_improvement',
                    'message': f'Long picking time in {zone_name}. Consider better organization.',
                    'priority': 'medium'
                })
        
        return recommendations
    
    def _calculate_optimal_flow(self, zone_analysis: Dict) -> List[str]:
        """Calculate optimal flow pattern through zones"""
        # Sort zones by picking frequency and priority
        zone_scores = {}
        
        for zone_name, data in zone_analysis.items():
            # Score based on item count and zone priority
            priority = self.zones.get(zone_name, {}).get('priority', 99)
            score = data['item_count'] / priority
            zone_scores[zone_name] = score
        
        return sorted(zone_scores.keys(), key=lambda z: zone_scores[z], reverse=True)
    
    def _analyze_layout_efficiency(self, placed_items: List[Dict]) -> Dict[str, float]:
        """Analyze overall layout efficiency"""
        if not placed_items:
            return {'overall': 0.0, 'zone_balance': 0.0, 'accessibility': 0.0}
        
        # Calculate zone balance
        zone_distribution = {}
        for item in placed_items:
            zone = self._get_item_zone(item)
            zone_distribution[zone] = zone_distribution.get(zone, 0) + 1
        
        # Calculate balance score (lower variance is better)
        if len(zone_distribution) > 1:
            values = list(zone_distribution.values())
            mean_val = np.mean(values)
            variance = np.var(values)
            balance_score = max(0, 100 - (variance / mean_val * 10))
        else:
            balance_score = 50  # Neutral score for single zone
        
        # Calculate accessibility (items in high-access zones)
        high_access_items = 0
        for item in placed_items:
            zone = self._get_item_zone(item)
            if self.zones.get(zone, {}).get('access_type') == 'high':
                high_access_items += 1
        
        accessibility_score = (high_access_items / len(placed_items)) * 100
        
        overall_score = (balance_score + accessibility_score) / 2
        
        return {
            'overall': round(overall_score, 2),
            'zone_balance': round(balance_score, 2),
            'accessibility': round(accessibility_score, 2)
        }
    
    def _calculate_picking_density(self, placed_items: List[Dict]) -> Dict[str, float]:
        """Calculate picking density metrics"""
        total_area = self.warehouse_length * self.warehouse_width
        item_density = len(placed_items) / total_area
        
        # Calculate zone densities
        zone_densities = {}
        for zone_name, zone_data in self.zones.items():
            items_in_zone = self._get_items_in_zone(placed_items, zone_data['bounds'])
            zone_area = self._calculate_zone_area(zone_data['bounds'])
            zone_densities[zone_name] = len(items_in_zone) / zone_area
        
        return {
            'overall_density': round(item_density, 4),
            'zone_densities': {k: round(v, 4) for k, v in zone_densities.items()},
            'density_variance': round(np.var(list(zone_densities.values())), 4)
        }
    
    def _estimate_traffic_patterns(self, placed_items: List[Dict]) -> Dict[str, Any]:
        """Estimate traffic patterns in the warehouse"""
        # Simulate traffic based on item distribution
        zone_traffic = {}
        
        for zone_name, zone_data in self.zones.items():
            items_in_zone = self._get_items_in_zone(placed_items, zone_data['bounds'])
            
            # Traffic is proportional to item count and zone priority
            base_traffic = len(items_in_zone)
            priority_multiplier = 1.0 / zone_data.get('priority', 1)
            traffic_score = base_traffic * priority_multiplier
            
            zone_traffic[zone_name] = {
                'traffic_score': round(traffic_score, 2),
                'congestion_risk': 'high' if traffic_score > 10 else 'medium' if traffic_score > 5 else 'low'
            }
        
        return {
            'zone_traffic': zone_traffic,
            'peak_zones': sorted(zone_traffic.keys(), 
                               key=lambda z: zone_traffic[z]['traffic_score'], 
                               reverse=True)[:3]
        }
    
    def _identify_bottlenecks(self, placed_items: List[Dict]) -> List[Dict]:
        """Identify potential bottlenecks in the warehouse layout"""
        bottlenecks = []
        
        # Check for overcrowded zones
        for zone_name, zone_data in self.zones.items():
            items_in_zone = self._get_items_in_zone(placed_items, zone_data['bounds'])
            zone_area = self._calculate_zone_area(zone_data['bounds'])
            
            if len(items_in_zone) > 0:
                density = len(items_in_zone) / zone_area
                
                if density > 0.3:  # High density threshold
                    bottlenecks.append({
                        'type': 'high_density',
                        'location': zone_name,
                        'severity': 'high' if density > 0.5 else 'medium',
                        'description': f'High item density ({density:.2f} items/m²) in {zone_name}',
                        'items_affected': len(items_in_zone)
                    })
        
        # Check for narrow aisles (simplified)
        if self.warehouse_width < 6:  # Less than 6m width
            bottlenecks.append({
                'type': 'narrow_aisle',
                'location': 'warehouse_layout',
                'severity': 'medium',
                'description': 'Narrow warehouse may cause traffic congestion',
                'items_affected': len(placed_items)
            })
        
        return bottlenecks
    
    def _calculate_overall_efficiency_score(self, layout_efficiency: Dict, 
                                          picking_density: Dict, 
                                          traffic_analysis: Dict) -> float:
        """Calculate overall efficiency score"""
        layout_score = layout_efficiency['overall']
        
        # Density score (optimal density is around 0.1-0.2 items/m²)
        optimal_density = 0.15
        actual_density = picking_density['overall_density']
        density_score = max(0, 100 - abs(actual_density - optimal_density) * 500)
        
        # Traffic score (fewer peak zones is better)
        peak_zones = len(traffic_analysis['peak_zones'])
        traffic_score = max(0, 100 - peak_zones * 20)
        
        # Weighted average
        overall_score = (layout_score * 0.4 + density_score * 0.3 + traffic_score * 0.3)
        return round(overall_score, 2)
    
    def _generate_improvement_suggestions(self, layout_efficiency: Dict, 
                                        traffic_analysis: Dict, 
                                        bottlenecks: List[Dict]) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if layout_efficiency['zone_balance'] < 70:
            suggestions.append("Rebalance item distribution across zones for better efficiency")
        
        if layout_efficiency['accessibility'] < 60:
            suggestions.append("Move frequently accessed items to high-access zones")
        
        if len(traffic_analysis['peak_zones']) > 2:
            suggestions.append("Consider redistributing items to reduce traffic congestion")
        
        for bottleneck in bottlenecks:
            if bottleneck['severity'] == 'high':
                suggestions.append(f"Address {bottleneck['type']}: {bottleneck['description']}")
        
        if not suggestions:
            suggestions.append("Current layout is well optimized")
        
        return suggestions
    
    def _empty_path_result(self) -> Dict[str, Any]:
        """Return empty path result structure"""
        return {
            'path_data': {'waypoints': [], 'zone_sequence': [], 'path_segments': []},
            'total_distance': 0.0,
            'estimated_time': 0.0,
            'path_efficiency': 0.0,
            'picking_zones': [],
            'zone_sequence': [],
            'items_to_pick': 0,
            'waypoints': []
        }