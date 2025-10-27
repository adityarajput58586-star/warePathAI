class WarehouseOptimizer {
    constructor() {
        this.canvas = document.getElementById('warehouseCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.optimizationResult = null;
        this.itemCount = 0;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.addDefaultItem();
        this.drawEmptyWarehouse();
    }
    
    setupEventListeners() {
        // Form submission
        document.getElementById('optimizationForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.optimizeLayout();
        });
        
        // Add item button
        document.getElementById('addItemBtn').addEventListener('click', () => {
            this.addItem();
        });
        
        // Export button
        document.getElementById('exportBtn').addEventListener('click', () => {
            this.exportResults();
        });
        
        // View buttons
        document.getElementById('view2D').addEventListener('click', () => {
            this.switchView('2d');
        });
        
        document.getElementById('view3D').addEventListener('click', () => {
            this.switchView('3d');
        });
        
        // Warehouse dimension changes
        ['warehouseLength', 'warehouseWidth', 'warehouseHeight'].forEach(id => {
            document.getElementById(id).addEventListener('input', () => {
                this.drawEmptyWarehouse();
            });
        });
    }
    
    addDefaultItem() {
        this.addItem('Pallet Box', 1.2, 0.8, 1.5, 10, 500);
    }
    
    addItem(name = '', length = '', width = '', height = '', quantity = 1, weight = '') {
        const template = document.getElementById('itemTemplate');
        const itemElement = template.cloneNode(true);
        itemElement.id = `item-${++this.itemCount}`;
        itemElement.classList.remove('d-none');
        
        // Set values if provided
        if (name) itemElement.querySelector('.item-name').value = name;
        if (length) itemElement.querySelector('.item-length').value = length;
        if (width) itemElement.querySelector('.item-width').value = width;
        if (height) itemElement.querySelector('.item-height').value = height;
        if (quantity) itemElement.querySelector('.item-quantity').value = quantity;
        if (weight) itemElement.querySelector('.item-weight').value = weight;
        
        // Add remove functionality
        itemElement.querySelector('.remove-item').addEventListener('click', () => {
            itemElement.remove();
            this.validateForm();
        });
        
        // Add validation listeners
        itemElement.querySelectorAll('input').forEach(input => {
            input.addEventListener('input', () => this.validateForm());
        });
        
        document.getElementById('itemsList').appendChild(itemElement);
        this.validateForm();
    }
    
    validateForm() {
        const items = this.getItems();
        const hasValidItems = items.length > 0 && items.every(item => 
            item.name && item.length > 0 && item.width > 0 && item.height > 0 && item.quantity > 0
        );
        
        const warehouseDims = this.getWarehouseDimensions();
        const hasValidWarehouse = warehouseDims.length > 0 && warehouseDims.width > 0 && warehouseDims.height > 0;
        
        document.getElementById('optimizeBtn').disabled = !(hasValidItems && hasValidWarehouse);
        
        if (hasValidWarehouse) {
            this.drawEmptyWarehouse();
        }
    }
    
    getWarehouseDimensions() {
        return {
            length: parseFloat(document.getElementById('warehouseLength').value) || 0,
            width: parseFloat(document.getElementById('warehouseWidth').value) || 0,
            height: parseFloat(document.getElementById('warehouseHeight').value) || 0
        };
    }
    
    getItems() {
        const items = [];
        document.querySelectorAll('#itemsList .item-form').forEach(itemForm => {
            const name = itemForm.querySelector('.item-name').value.trim();
            const length = parseFloat(itemForm.querySelector('.item-length').value);
            const width = parseFloat(itemForm.querySelector('.item-width').value);
            const height = parseFloat(itemForm.querySelector('.item-height').value);
            const quantity = parseInt(itemForm.querySelector('.item-quantity').value);
            const weight = parseFloat(itemForm.querySelector('.item-weight').value) || 0;
            
            if (name && length > 0 && width > 0 && height > 0 && quantity > 0) {
                items.push({ name, length, width, height, quantity, weight });
            }
        });
        return items;
    }
    
    async optimizeLayout() {
        const warehouse = this.getWarehouseDimensions();
        const items = this.getItems();
        const algorithm = document.getElementById('algorithm').value;
        
        if (items.length === 0) {
            this.showError('Please add at least one storage item.');
            return;
        }
        
        this.showLoading(true);
        this.hideError();
        this.hideMetrics();
        
        try {
            const response = await fetch('/api/optimize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    warehouse: warehouse,
                    items: items,
                    algorithm: algorithm
                })
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Optimization failed');
            }
            
            this.optimizationResult = result;
            this.displayResults(result);
            document.getElementById('exportBtn').disabled = false;
            
        } catch (error) {
            console.error('Optimization error:', error);
            this.showError(error.message || 'Failed to optimize warehouse layout. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }
    
    displayResults(result) {
        this.showMetrics();
        this.updateMetrics(result);
        this.drawOptimizedLayout(result);
    }
    
    updateMetrics(result) {
        const metrics = result.metrics;
        const summary = result.summary;
        
        document.getElementById('utilizationRate').textContent = `${metrics.utilization}%`;
        document.getElementById('itemsPlaced').textContent = `${metrics.items_placed}/${metrics.items_total}`;
        document.getElementById('efficiency').textContent = `${metrics.efficiency}%`;
        document.getElementById('volumeUsed').textContent = `${metrics.volume_used} m³`;
        document.getElementById('algorithmUsed').textContent = this.getAlgorithmDisplayName(result.algorithm);
    }
    
    getAlgorithmDisplayName(algorithm) {
        const names = {
            'bin_packing': 'Bin Pack',
            'space_filling': 'Space Fill',
            'hybrid': 'Hybrid'
        };
        return names[algorithm] || algorithm;
    }
    
    drawEmptyWarehouse() {
        const warehouse = this.getWarehouseDimensions();
        if (warehouse.length <= 0 || warehouse.width <= 0) return;
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Calculate scale to fit warehouse in canvas
        const padding = 40;
        const availableWidth = this.canvas.width - 2 * padding;
        const availableHeight = this.canvas.height - 2 * padding;
        
        const scaleX = availableWidth / warehouse.length;
        const scaleY = availableHeight / warehouse.width;
        this.scale = Math.min(scaleX, scaleY);
        
        this.offsetX = padding + (availableWidth - warehouse.length * this.scale) / 2;
        this.offsetY = padding + (availableHeight - warehouse.width * this.scale) / 2;
        
        // Draw warehouse outline
        this.ctx.strokeStyle = '#6c757d';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(
            this.offsetX,
            this.offsetY,
            warehouse.length * this.scale,
            warehouse.width * this.scale
        );
        
        // Draw grid
        this.drawGrid(warehouse);
        
        // Draw dimensions
        this.drawDimensions(warehouse);
    }
    
    drawGrid(warehouse) {
        this.ctx.strokeStyle = '#495057';
        this.ctx.lineWidth = 0.5;
        this.ctx.setLineDash([2, 2]);
        
        // Vertical lines (every 5 meters)
        for (let x = 5; x < warehouse.length; x += 5) {
            const canvasX = this.offsetX + x * this.scale;
            this.ctx.beginPath();
            this.ctx.moveTo(canvasX, this.offsetY);
            this.ctx.lineTo(canvasX, this.offsetY + warehouse.width * this.scale);
            this.ctx.stroke();
        }
        
        // Horizontal lines (every 5 meters)
        for (let y = 5; y < warehouse.width; y += 5) {
            const canvasY = this.offsetY + y * this.scale;
            this.ctx.beginPath();
            this.ctx.moveTo(this.offsetX, canvasY);
            this.ctx.lineTo(this.offsetX + warehouse.length * this.scale, canvasY);
            this.ctx.stroke();
        }
        
        this.ctx.setLineDash([]);
    }
    
    drawDimensions(warehouse) {
        this.ctx.fillStyle = '#adb5bd';
        this.ctx.font = '12px Arial';
        this.ctx.textAlign = 'center';
        
        // Length dimension
        this.ctx.fillText(
            `${warehouse.length}m`,
            this.offsetX + (warehouse.length * this.scale) / 2,
            this.offsetY - 10
        );
        
        // Width dimension
        this.ctx.save();
        this.ctx.translate(this.offsetX - 15, this.offsetY + (warehouse.width * this.scale) / 2);
        this.ctx.rotate(-Math.PI / 2);
        this.ctx.fillText(`${warehouse.width}m`, 0, 0);
        this.ctx.restore();
    }
    
    drawOptimizedLayout(result) {
        this.drawEmptyWarehouse();
        
        const placedItems = result.placed_items;
        const colors = this.generateColors(placedItems.length);
        
        placedItems.forEach((item, index) => {
            this.drawItem(item, colors[index % colors.length]);
        });
        
        // Draw legend
        this.drawLegend(placedItems, colors);
    }
    
    drawItem(item, color) {
        const x = this.offsetX + item.position.x * this.scale;
        const y = this.offsetY + item.position.y * this.scale;
        const width = item.dimensions.length * this.scale;
        const height = item.dimensions.width * this.scale;
        
        // Draw item rectangle
        this.ctx.fillStyle = color;
        this.ctx.fillRect(x, y, width, height);
        
        // Draw item border
        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(x, y, width, height);
        
        // Draw item label if space allows
        if (width > 40 && height > 20) {
            this.ctx.fillStyle = '#000';
            this.ctx.font = '10px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(
                item.name.length > 8 ? item.name.substring(0, 8) + '...' : item.name,
                x + width / 2,
                y + height / 2 + 3
            );
        }
    }
    
    drawLegend(placedItems, colors) {
        const legendX = 10;
        let legendY = 10;
        const itemTypes = [...new Set(placedItems.map(item => item.name))];
        
        this.ctx.font = '11px Arial';
        this.ctx.textAlign = 'left';
        
        itemTypes.forEach((itemType, index) => {
            const color = colors[index % colors.length];
            const count = placedItems.filter(item => item.name === itemType).length;
            
            // Draw color box
            this.ctx.fillStyle = color;
            this.ctx.fillRect(legendX, legendY, 12, 12);
            this.ctx.strokeStyle = '#000';
            this.ctx.lineWidth = 1;
            this.ctx.strokeRect(legendX, legendY, 12, 12);
            
            // Draw text
            this.ctx.fillStyle = '#fff';
            this.ctx.fillText(`${itemType} (${count})`, legendX + 18, legendY + 9);
            
            legendY += 18;
        });
    }
    
    generateColors(count) {
        const colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#FFB6C1', '#87CEEB', '#F0E68C',
            '#FFA07A', '#20B2AA', '#B0C4DE', '#FF69B4', '#32CD32'
        ];
        
        // If we need more colors than predefined, generate them
        while (colors.length < count) {
            const hue = (colors.length * 137.508) % 360; // Golden angle
            colors.push(`hsl(${hue}, 70%, 60%)`);
        }
        
        return colors;
    }
    
    showLoading(show) {
        const loading = document.getElementById('loadingIndicator');
        const optimizeBtn = document.getElementById('optimizeBtn');
        const optimizeText = document.getElementById('optimizeText');
        
        if (show) {
            loading.classList.remove('d-none');
            optimizeBtn.disabled = true;
            optimizeText.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Optimizing...';
        } else {
            loading.classList.add('d-none');
            optimizeBtn.disabled = false;
            optimizeText.innerHTML = '<i class="fas fa-brain me-2"></i>Optimize Layout';
        }
    }
    
    showMetrics() {
        document.getElementById('metricsDisplay').classList.remove('d-none');
    }
    
    hideMetrics() {
        document.getElementById('metricsDisplay').classList.add('d-none');
    }
    
    showError(message) {
        const errorDisplay = document.getElementById('errorDisplay');
        const errorMessage = document.getElementById('errorMessage');
        
        errorMessage.textContent = message;
        errorDisplay.classList.remove('d-none');
    }
    
    hideError() {
        document.getElementById('errorDisplay').classList.add('d-none');
    }
    
    switchView(viewType) {
        const view2D = document.getElementById('view2D');
        const view3D = document.getElementById('view3D');
        
        if (viewType === '2d') {
            view2D.classList.add('active');
            view3D.classList.remove('active');
        } else {
            view3D.classList.add('active');
            view2D.classList.remove('active');
        }
        
        // Redraw with current results if available
        if (this.optimizationResult) {
            this.drawOptimizedLayout(this.optimizationResult);
        } else {
            this.drawEmptyWarehouse();
        }
    }
    
    async exportResults() {
        if (!this.optimizationResult) {
            this.showError('No optimization results to export.');
            return;
        }
        
        try {
            const response = await fetch('/api/export');
            const exportData = await response.json();
            
            if (!response.ok) {
                throw new Error(exportData.error || 'Export failed');
            }
            
            // Create and download JSON file
            const dataStr = JSON.stringify(exportData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `warehouse-layout-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
        } catch (error) {
            console.error('Export error:', error);
            this.showError(error.message || 'Failed to export results.');
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new WarehouseOptimizer();
});
