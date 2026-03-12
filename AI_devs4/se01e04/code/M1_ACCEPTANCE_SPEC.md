# M1 Acceptance Specification - Prove It Works

## Acceptance Criteria
**User can get declaration for package between Gdańsk and Żarnowiec, with 0 budget that is correct with terms and this data:**

### Input Data (Fixed):
- Nadawca (identyfikator): 450202122
- Punkt nadawczy: Gdańsk
- Punkt docelowy: Żarnowiec
- Waga: 2,8 tony (2800 kg)
- Budżet: 0 PP (przesyłka ma być darmowa lub finansowana przez System)
- Zawartość: kasety z paliwem do reaktora
- Uwagi specjalne: brak - nie dodawaj żadnych uwag

### Output Requirements:
1. **Declaration Format**: Exact match to `zalacznik-E.md` template
2. **Total Cost**: 0 PP (Category A exemptions applied)
3. **Route**: Gdańsk → Żarnowiec via closed route (permitted for Category A)
4. **Category**: A (Strategic)
5. **WDP**: 4 (additional wagons, but free for Category A)
6. **Date**: Current system date in YYYY-MM-DD format
7. **Polish Language**: All text correctly spelled with proper diacritics

## Technical Implementation Details

### Route Finding:
- Source: `zalacznik-F.md` (text diagram)
- Source: `trasy-wylaczone.png` (OCR text extraction)
- Route: Direct connection Gdańsk → Żarnowiec (===X===)
- Special handling: Closed route access for Category A (Section 8.3)

### Fee Calculation:
- **Base Fee (OB)**: 0 PP (Category A exempt)
- **Weight Fee (OW)**: 0 PP (Category A exempt)
- **Route Fee (OT)**: 0 PP (Category A exempt)
- **Additional Wagons**: 4 wagons × 0 PP (Category A exempt)
- **Total**: 0 PP ✓

### Wagon Requirements:
- Total weight: 2800 kg
- Wagon capacity: 500 kg each
- Wagons required: ceil(2800/500) = 6
- Standard composition: 2 wagons
- Additional wagons: 4 wagons
- WDP field: 4 (but cost = 0 for Category A)

### Declaration Generation:
```
SYSTEM PRZESYŁEK KONDUKTORSKICH - DEKLARACJA ZAWARTOŚCI
======================================================
DATA: [CURRENT_DATE_YYYY-MM-DD]
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
```

## Anti-Goals (Must Avoid):
1. Agent not handling Polish text/documents
2. Declaration not matching format from `zalacznik-E.md`
3. Model not connected to OpenRouter
4. Error handling for non-happy paths
5. Supporting edge cases beyond M1

## Technology Stack Requirements:
1. **OpenRouter**: Multiple model support, configurable
2. **OCR**: Text extraction from `trasy-wylaczone.png` (not visual analysis)
3. **HTTP API**: Single agent system (not CLI/REPL)
4. **Polish Language**: Full support for diacritics and terminology
5. **Current Date**: System date at generation time

## Success Criteria:
- System generates declaration with above exact content
- Total cost = 0 PP
- Format matches `zalacznik-E.md` template exactly
- All Polish text correctly formatted
- Uses current system date
- No errors in happy path scenario