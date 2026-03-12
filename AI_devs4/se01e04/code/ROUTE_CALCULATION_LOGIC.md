# Route Calculation Algorithm for Żarnowiec Strategic Shipments

## Input Constraints
- **Start**: Gdańsk (WR-Północ regional node)
- **End**: Żarnowiec (excluded zone, special handling required)
- **Category**: A (Strategic)
- **Budget**: 0 PP
- **Weight**: 2800 kg (2.8 tony)
- **Content**: kasety z paliwem do reaktora (fuel cassettes for reactor)
- **Special Notes**: brak (none)

## Algorithm Steps

### Step 1: Parse Route Diagram (`zalacznik-F.md`)
```
Key patterns in the diagram:
- ŻARNOWIEC ===X=== GDAŃSK  (closed route connection)
- ===X=== indicates excluded/closed route
- Gdańsk connections: R-01 (Bydgoszcz), R-16 (Elbląg), M-10 (Poznań)
```

### Step 2: Analyze Closed Route Map (`trasy-wylaczone.png`)
- Verify Żarnowiec is marked as excluded zone
- Confirm direct connection between Gdańsk and Żarnowiec
- Note any special closure designations

### Step 3: Apply Section 8.3 Rules (Closed Routes)
```python
def can_use_closed_route(category, destination):
    """
    Section 8.3: Closed routes can only be used for categories A and B packages
    """
    if category in ['A', 'B'] and destination == 'Żarnowiec':
        return True
    return False
```

### Step 4: Route Calculation
```python
# For Category A strategic package to Żarnowiec
if category == 'A' and destination == 'Żarnowiec':
    route = "GDAŃSK → ŻARNOWIEC (via closed route)"
    route_code = "X-ZAR"  # Special designation for Żarnowiec closed route
    is_closed_route = True
    permission_required = True  # Special System authorization needed
```

### Step 5: Distance Calculation (Estimation)
Since Żarnowiec is not on standard maps:
- Assumed distance: Based on geographical proximity to Gdańsk
- Estimated range: 30-50 km (for fee calculation purposes)
- Note: Category A exempt from distance fees anyway

### Step 6: Wagon Requirements Calculation
```python
standard_wagon_capacity = 500  # kg
total_weight = 2800  # kg

wagons_required = math.ceil(total_weight / standard_wagon_capacity)  # = 6
standard_wagons_in_composition = 2  # Basic train composition
additional_wagons = wagons_required - standard_wagons_in_composition  # = 4

# Category A exemption: additional wagons free (55 PP each normally)
additional_wagon_cost = 0 if category == 'A' else additional_wagons * 55
```

### Step 7: Fee Calculation with Category A Exemptions
| Fee Component | Standard Calculation | Category A (Strategic) |
|--------------|---------------------|------------------------|
| Base Fee (OB) | Category-based | 0 PP (exempt) |
| Weight Fee (OW) | Progressive: 0.5-7 PP/kg | 0 PP (exempt) |
| Route Fee (OT) | 1-3 PP/100km based on boundaries | 0 PP (exempt) |
| Additional Wagons | 55 PP each | 0 PP (exempt) |
| **TOTAL** | **Variable** | **0 PP** |

### Step 8: Declaration Generation
```python
declaration_template = """
SYSTEM PRZESYŁEK KONDUKTORSKICH - DEKLARACJA ZAWARTOŚCI
======================================================
DATA: {date}
PUNKT NADAWCZY: Gdańsk
------------------------------------------------------
NADAWCA: 450202122
PUNKT DOCELOWY: Żarnowiec
TRASA: X-ZAR (via closed route - Category A strategic)
------------------------------------------------------
KATEGORIA PRZESYŁKI: A
------------------------------------------------------
OPIS ZAWARTOŚCI (max 200 znaków): kasety z paliwem do reaktora
------------------------------------------------------
DEKLAROWANA MASA (kg): 2800
------------------------------------------------------
WDP: 4
------------------------------------------------------
UWAGI SPECJALNE: brak
------------------------------------------------------
KWOTA DO ZAPŁATY: 0 PP
------------------------------------------------------
OŚWIADCZAM, ŻE PODANE INFORMACJE SĄ PRAWDZIWE.
BIORĘ NA SIEBIE KONSEKWENCJĘ ZA FAŁSZYWE OŚWIADCZENIE.
======================================================
"""
```

## Special Considerations

### 1. System Authorization (ZS)
- Category A packages to Żarnowiec require special System authorization
- Agent should include note about required Zezwolenie Systemu (ZS)
- Authorization process is outside agent scope (handled by SPK system)

### 2. Closed Route Security
- Physical barriers exist on closed routes (Section 8.1)
- Special access permissions required for strategic shipments
- Monitoring and patrols may be increased

### 3. Documentation Compliance
- Declaration must match `zalacznik-E.md` format exactly
- All Polish text must be correctly spelled and formatted
- Date format: YYYY-MM-DD
- Numeric format: using Polish decimal separator (comma for thousands)

## Validation Checks

1. **Route Validity**: Gdańsk → Żarnowiec via closed route (permitted for Category A)
2. **Cost Compliance**: Total = 0 PP (Category A exemptions applied)
3. **Format Compliance**: Matches `zalacznik-E.md` template exactly
4. **Weight Verification**: 2800 kg = 6 wagons (2 standard + 4 additional)
5. **Category Verification**: Fuel cassettes for reactor = Strategic (A)
6. **Special Handling**: Closed route access properly documented

## Error Conditions

1. **If category ≠ A or B**: Route calculation fails - closed routes not permitted
2. **If destination ≠ Żarnowiec**: Standard routing algorithm applies
3. **If weight > 4000 kg**: Exceeds maximum limit (reject)
4. **If budget > 0**: Cannot meet budget constraint for non-Strategic categories