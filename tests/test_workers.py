import asyncio
import pytest


# ── auto_workers Tests ──────────────────────────────────────────────────────

class TestRechnungErfassen:
    def test_gibt_zeitstempel_zurueck(self):
        from src.workers.auto_workers import rechnung_erfassen
        result = asyncio.run(rechnung_erfassen(
            rechnungs_nummer="R-001",
            eingangskanal="email"
        ))
        assert result["rechnung_status"] == "erfasst"
        assert "erfassung_zeitstempel" in result

    def test_funktioniert_ohne_variablen(self):
        from src.workers.auto_workers import rechnung_erfassen
        result = asyncio.run(rechnung_erfassen())
        assert result["rechnung_status"] == "erfasst"


class TestAutomatischeValidierung:
    def test_gueltige_rechnung(self):
        from src.workers.auto_workers import automatische_validierung
        result = asyncio.run(automatische_validierung(
            rechnungs_nummer="R-001",
            lieferant="Test GmbH",
            betrag=5000,
            waehrung="EUR",
            datum="2026-06-01"
        ))
        assert result["validierung_erfolgreich"] is True
        assert result["validierung_fehler"] == ""

    def test_fehlende_rechnungsnummer(self):
        from src.workers.auto_workers import automatische_validierung
        result = asyncio.run(automatische_validierung(
            rechnungs_nummer="",
            lieferant="Test GmbH",
            betrag=5000,
            waehrung="EUR",
            datum="2026-06-01"
        ))
        assert result["validierung_erfolgreich"] is False
        assert "Rechnungsnummer fehlt" in result["validierung_fehler"]

    def test_ungueltige_waehrung(self):
        from src.workers.auto_workers import automatische_validierung
        result = asyncio.run(automatische_validierung(
            rechnungs_nummer="R-001",
            lieferant="Test GmbH",
            betrag=5000,
            waehrung="XYZ",
            datum="2026-06-01"
        ))
        assert result["validierung_erfolgreich"] is False
        assert "Währung ungültig" in result["validierung_fehler"]

    def test_negativer_betrag(self):
        from src.workers.auto_workers import automatische_validierung
        result = asyncio.run(automatische_validierung(
            rechnungs_nummer="R-001",
            lieferant="Test GmbH",
            betrag=-100,
            waehrung="EUR",
            datum="2026-06-01"
        ))
        assert result["validierung_erfolgreich"] is False


class TestComplianceCheck:
    def test_eur_unter_schwellenwert(self):
        from src.workers.auto_workers import compliance_check
        result = asyncio.run(compliance_check(
            rechnungs_nummer="R-001",
            betrag=5000,
            waehrung="EUR"
        ))
        assert result["compliance_notwendig"] is False
        assert result["compliance_schwellenwert"] == 10000

    def test_eur_ueber_schwellenwert(self):
        from src.workers.auto_workers import compliance_check
        result = asyncio.run(compliance_check(
            rechnungs_nummer="R-001",
            betrag=15000,
            waehrung="EUR"
        ))
        assert result["compliance_notwendig"] is True

    def test_usd_schwellenwert(self):
        from src.workers.auto_workers import compliance_check
        result = asyncio.run(compliance_check(
            rechnungs_nummer="R-001",
            betrag=11001,
            waehrung="USD"
        ))
        assert result["compliance_notwendig"] is True
        assert result["compliance_schwellenwert"] == 11000

    def test_chf_schwellenwert(self):
        from src.workers.auto_workers import compliance_check
        result = asyncio.run(compliance_check(
            rechnungs_nummer="R-001",
            betrag=10000,
            waehrung="CHF"
        ))
        assert result["compliance_notwendig"] is False
        assert result["compliance_schwellenwert"] == 10800

    def test_gbp_schwellenwert(self):
        from src.workers.auto_workers import compliance_check
        result = asyncio.run(compliance_check(
            rechnungs_nummer="R-001",
            betrag=9000,
            waehrung="GBP"
        ))
        assert result["compliance_notwendig"] is True
        assert result["compliance_schwellenwert"] == 8700
