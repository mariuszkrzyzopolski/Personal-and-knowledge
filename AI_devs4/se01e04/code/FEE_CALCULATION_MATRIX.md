# SPK Fee Calculation Matrix

## Base Fee Structure (Section 9.2)

### 1. Base Fees by Category (OB)
| Category | Name | Base Fee (PP) | Notes |
|----------|------|---------------|-------|
| A | Strategic | 0 | Covered by System |
| B | Medical | 0 | Covered by System |
| C | Food | 2 | 50% discount for collective farms |
| D | Economic | 5 | Standard economic shipments |
| E | Personal | 10 | Highest base fee |

### 2. Weight Fees (OW) - Progressive Scale
| Weight Range (kg) | Fee per kg (PP) | Example Calculation |
|-------------------|-----------------|---------------------|
| 0.1 - 5.0 | 0.5 PP/kg | 3 kg = 3 × 0.5 = 1.5 PP |
| 5.1 - 25.0 | 1.0 PP/kg | 20 kg = 5×0.5 + 15×1 = 17.5 PP |
| 25.1 - 100.0 | 2.0 PP/kg | 80 kg = 5×0.5 + 20×1 + 55×2 = 132.5 PP |
| 100.1 - 500.0 | 3.0 PP/kg | 300 kg = 5×0.5 + 20×1 + 75×2 + 200×3 = 772.5 PP |
| 500.1 - 1000.0 | 5.0 PP/kg | 800 kg = 5×0.5 + 20×1 + 75×2 + 400×3 + 300×5 = 2587.5 PP |
| 1000.0+ | 7.0 PP/kg | See additional wagons below |

### 3. Route Fees (OT) - Distance Based
| Route Type | Fee per 100 km (PP) | Example Calculation |
|------------|---------------------|---------------------|
| Within one region | 1 PP/100km | 150 km = 1.5 PP |
| Cross 1 regional boundary | 2 PP/100km | 150 km = 3 PP |
| Cross 2+ regional boundaries | 3 PP/100km | 150 km = 4.5 PP |

### 4. Additional Wagons
- **Standard composition**: 2 wagons (500 kg each) = 1000 kg capacity
- **Additional wagons**: 55 PP each (500 kg capacity)
- **Strategic/Medical**: Additional wagons free (0 PP)

## Category A (Strategic) Exemptions

### Complete Fee Waiver
| Fee Component | Standard Rate | Category A Rate | Reason |
|---------------|---------------|-----------------|--------|
| Base Fee (OB) | Category-based | 0 PP | System covers strategic shipments |
| Weight Fee (OW) | 0.5-7 PP/kg | 0 PP | Critical infrastructure support |
| Route Fee (OT) | 1-3 PP/100km | 0 PP | Priority routing for system needs |
| Additional Wagons | 55 PP each | 0 PP | Necessary for system operations |

### Wagon Calculation for 2800 kg Strategic Package
```
Total weight: 2800 kg
Wagon capacity: 500 kg each

Wagons required: ceil(2800 / 500) = 6 wagons
Standard composition: 2 wagons
Additional wagons needed: 6 - 2 = 4 wagons

Additional wagon cost (standard): 4 × 55 PP = 220 PP
Additional wagon cost (Category A): 4 × 0 PP = 0 PP
```

## Complete Fee Calculation Example: Gdańsk-Żarnowiec

### Parameters
- **Category**: A (Strategic)
- **Weight**: 2800 kg
- **Distance**: Unknown (closed route) - estimated 40 km
- **Regional boundaries**: 0 (within Pomeranian region)
- **Additional wagons**: 4 required

### Calculation Matrix
| Component | Formula | Standard Calculation | Category A Calculation |
|-----------|---------|---------------------|------------------------|
| Base Fee (OB) | Category rate | 0 PP | 0 PP |
| Weight Fee (OW) | 7 PP/kg (1000kg+) | 2800 × 7 = 19,600 PP | 0 PP |
| Route Fee (OT) | 1 PP/100km | 0.4 × 1 = 0.4 PP | 0 PP |
| Additional Wagons | 55 PP each | 4 × 55 = 220 PP | 0 PP |
| **TOTAL** | **OB + OW + OT + Wagons** | **19,820.4 PP** | **0 PP** |

## Fee Calculation Algorithm

```python
def calculate_fee(category, weight_kg, distance_km, regional_boundaries):
    """
    Calculate total fee based on SPK fee structure
    """
    
    # 1. Base fee
    base_fee = {
        'A': 0, 'B': 0, 'C': 2, 'D': 5, 'E': 10
    }[category]
    
    # 2. Weight fee (progressive)
    weight_fee = 0
    remaining_weight = weight_kg
    
    # Apply progressive brackets
    brackets = [
        (5, 0.5),    # 0.1-5 kg
        (20, 1.0),   # 5.1-25 kg  
        (75, 2.0),   # 25.1-100 kg
        (400, 3.0),  # 100.1-500 kg
        (500, 5.0),  # 500.1-1000 kg
        (float('inf'), 7.0)  # 1000+ kg
    ]
    
    for max_weight, rate in brackets:
        if remaining_weight <= 0:
            break
        
        bracket_weight = min(remaining_weight, max_weight)
        weight_fee += bracket_weight * rate
        remaining_weight -= bracket_weight
    
    # 3. Route fee
    if regional_boundaries == 0:
        route_rate = 1.0
    elif regional_boundaries == 1:
        route_rate = 2.0
    else:
        route_rate = 3.0
    
    route_fee = (distance_km / 100) * route_rate
    
    # 4. Additional wagons (if weight > 1000 kg)
    additional_wagons = 0
    if weight_kg > 1000:
        wagons_needed = math.ceil(weight_kg / 500)
        standard_wagons = 2
        additional_wagons = max(0, wagons_needed - standard_wagons)
    
    additional_wagon_fee = additional_wagons * 55
    
    # 5. Apply Category A/B exemptions
    if category in ['A', 'B']:
        weight_fee = 0
        route_fee = 0
        additional_wagon_fee = 0
    
    # 6. Total
    total = base_fee + weight_fee + route_fee + additional_wagon_fee
    
    return {
        'base_fee': base_fee,
        'weight_fee': weight_fee,
        'route_fee': route_fee,
        'additional_wagons': additional_wagons,
        'additional_wagon_fee': additional_wagon_fee,
        'total': total
    }
```

## Discounts and Special Cases

### Available Discounts
1. **Category C from collective farms**: 50% discount on base fee
2. **Operators/Technicians**: 25% discount on Category E personal shipments
3. **Multiple discounts do NOT stack**

### Penalty Fees
- **Weight discrepancy**: 200% of correct fee if weight under-declared
- **Late pickup**: Storage fees after 14 days
- **Prohibited items**: Immediate confiscation + criminal charges

## Declaration Field: WDP (Wagony Dodatkowe Płatne)

### Definition
WDP = Number of additional wagons requiring payment
- For Categories A/B: WDP = 0 (even if wagons needed, they're free)
- For Categories C/D/E: WDP = additional wagons needed

### Calculation
```python
def calculate_wdp(category, weight_kg):
    if weight_kg <= 1000:
        return 0
    
    wagons_needed = math.ceil(weight_kg / 500)
    additional_wagons = wagons_needed - 2
    
    if category in ['A', 'B']:
        return 0  # Free for strategic/medical
    else:
        return additional_wagons
```

### Example for 2800 kg:
- Weight: 2800 kg → 6 wagons needed
- Standard: 2 wagons
- Additional: 4 wagons
- Category A: WDP = 0 (free)
- Category D: WDP = 4 (220 PP cost)