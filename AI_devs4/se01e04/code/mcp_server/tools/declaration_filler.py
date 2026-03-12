from datetime import datetime


DECLARATION_TEMPLATE = """SYSTEM PRZESYŁEK KONDUKTORSKICH - DEKLARACJA ZAWARTOŚCI
======================================================
DATA: {date}
PUNKT NADAWCZY: {origin}
------------------------------------------------------
NADAWCA: {sender_id}
PUNKT DOCELOWY: {destination}
TRASA: {route_code}
------------------------------------------------------
KATEGORIA PRZESYŁKI: {category}
------------------------------------------------------
OPIS ZAWARTOŚCI (max 200 znaków): {content}
------------------------------------------------------
DEKLAROWANA MASA (kg): {weight}
------------------------------------------------------
WDP: {wdp}
------------------------------------------------------
UWAGI SPECJALNE: {special_notes}
------------------------------------------------------
KWOTA DO ZAPŁATY: {fee} PP
------------------------------------------------------
OŚWIADCZAM, ŻE PODANE INFORMACJE SĄ PRAWDZIWE.
BIORĘ NA SIEBIE KONSEKWENCJĘ ZA FAŁSZYWE OŚWIADCZENIE.
======================================================"""


class DeclarationFiller:
    TEMPLATE = DECLARATION_TEMPLATE

    def fill(
        self,
        sender_id: str,
        origin: str,
        destination: str,
        route_code: str,
        category: str,
        content: str,
        weight_kg: float,
        wdp: int,
        special_notes: str,
        fee: float,
        date: str = None,
    ) -> str:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        content = content[:200]

        if special_notes is None or special_notes == "":
            special_notes = "brak"

        declaration = self.TEMPLATE.format(
            date=date,
            origin=origin,
            sender_id=sender_id,
            destination=destination,
            route_code=route_code,
            category=category,
            content=content,
            weight=int(weight_kg),
            wdp=wdp,
            special_notes=special_notes,
            fee=int(fee) if fee == int(fee) else fee,
        )

        return declaration

    def validate_format(self, declaration: str) -> bool:
        required_fields = [
            "SYSTEM PRZESYŁEK KONDUKTORSKICH - DEKLARACJA ZAWARTOŚCI",
            "DATA:",
            "PUNKT NADAWCZY:",
            "NADAWCA:",
            "PUNKT DOCELOWY:",
            "TRASA:",
            "KATEGORIA PRZESYŁKI:",
            "OPIS ZAWARTOŚCI",
            "DEKLAROWANA MASA",
            "WDP:",
            "UWAGI SPECJALNE:",
            "KWOTA DO ZAPŁATY:",
            "OŚWIADCZAM, ŻE PODANE INFORMACJE SĄ PRAWDZIWE.",
            "BIORĘ NA SIEBIE KONSEKWENCJĘ ZA FAŁSZYWE OŚWIADCZENIE.",
        ]

        for field in required_fields:
            if field not in declaration:
                return False

        return True
