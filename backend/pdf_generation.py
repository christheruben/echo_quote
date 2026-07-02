import reportlab
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
import math

CURRENCIES = {
    "ZAR": {"sym": "R",  "installPerW": 18.0, "elecRate": 3.5},
    "AUD": {"sym": "A$", "installPerW": 1.1,  "elecRate": 0.32},
    "GBP": {"sym": "£",  "installPerW": 1.3,  "elecRate": 0.28},
    "USD": {"sym": "$",  "installPerW": 1.0,  "elecRate": 0.15},
    "EUR": {"sym": "€",  "installPerW": 1.15, "elecRate": 0.25},
}

REGIONS = {
    "za": {"label": "South Africa",        "peakSun": 5.5},
    "au": {"label": "Australia",           "peakSun": 4.8},
    "uk": {"label": "United Kingdom",      "peakSun": 2.8},
    "us": {"label": "United States",       "peakSun": 4.5},
    "eu": {"label": "Europe (Central)",    "peakSun": 3.5},
    "me": {"label": "Middle East / MENA",  "peakSun": 6.0},
}


class QuotePDFGenerator:
    def __init__(self, region_key: str, currency_key: str, area_m2: float, usable: float = 0.75, efficiency: float = 0.2):
        self.q = self.calculate_quote(region_key, currency_key, area_m2, usable, efficiency)

    def calculate_quote(self, region_key: str, currency_key: str, area_m2: float, usable: float = 0.75, efficiency: float = 0.2):
        """Port of the TypeScript calculations."""
        region = REGIONS[region_key]
        cur = CURRENCIES[currency_key]

        usable_area   = area_m2 * usable
        system_kw     = usable_area * efficiency
        num_panels    = max(0, round(usable_area / 1.8))
        annual_kwh    = system_kw * region["peakSun"] * 365
        annual_saving = annual_kwh * cur["elecRate"]
        total_cost    = system_kw * 1000 * cur["installPerW"]

        hardware  = total_cost * 0.50
        inverter  = total_cost * 0.15
        labour    = total_cost * 0.25
        misc      = total_cost * 0.10

        payback = total_cost / annual_saving if annual_saving > 0 else math.inf
        net_25  = annual_saving * 25 - total_cost

        return {
            "region":        region["label"],
            "currency":      currency_key,
            "sym":           cur["sym"],
            "area_m2":       area_m2,
            "usable_area":   usable_area,
            "system_kw":     system_kw,
            "num_panels":    num_panels,
            "annual_kwh":    annual_kwh,
            "annual_saving": annual_saving,
            "total_cost":    total_cost,
            "hardware":      hardware,
            "inverter":      inverter,
            "labour":        labour,
            "misc":          misc,
            "payback_years": payback,
            "net_25yr":      net_25,
        }

    def generate_pdf(self) -> bytes:
        from io import BytesIO
        buf = BytesIO()
        q   = self.q
        sym = q["sym"]
        c   = canvas.Canvas(buf, pagesize=A4)
        w, h = A4

        def fmt(val):
            return f"{val:,.2f}"

        # ── Header ────────────────────────────────────────────────────────────
        c.setFillColor(colors.HexColor("#1a1a2e"))
        c.rect(0, h - 60*mm, w, 60*mm, fill=True, stroke=False)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(20*mm, h - 28*mm, "Solar Installation Quote")
        c.setFont("Helvetica", 11)
        c.drawString(20*mm, h - 40*mm, q["region"])

        # ── System Summary ────────────────────────────────────────────────────
        y = h - 80*mm
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(20*mm, y, "System Summary")
        y -= 8*mm

        summary_rows = [
            ("Roof Area",         f"{fmt(q['area_m2'])} m²"),
            ("Usable Area",       f"{fmt(q['usable_area'])} m²"),
            ("System Size",       f"{fmt(q['system_kw'])} kW"),
            ("Number of Panels",  str(q["num_panels"])),
            ("Annual Production", f"{fmt(q['annual_kwh'])} kWh"),
        ]
        self._draw_table(c, y, summary_rows, w)
        y -= len(summary_rows) * 8*mm + 10*mm

        # ── Cost Breakdown ────────────────────────────────────────────────────
        c.setFont("Helvetica-Bold", 13)
        c.drawString(20*mm, y, "Cost Breakdown")
        y -= 8*mm

        cost_rows = [
            ("Hardware",      f"{sym} {fmt(q['hardware'])}"),
            ("Inverter",      f"{sym} {fmt(q['inverter'])}"),
            ("Labour",        f"{sym} {fmt(q['labour'])}"),
            ("Miscellaneous", f"{sym} {fmt(q['misc'])}"),
            ("Total Cost",    f"{sym} {fmt(q['total_cost'])}"),
        ]
        self._draw_table(c, y, cost_rows, w, highlight_last=True)
        y -= len(cost_rows) * 8*mm + 10*mm

        # ── Financial Returns ─────────────────────────────────────────────────
        c.setFont("Helvetica-Bold", 13)
        c.drawString(20*mm, y, "Financial Returns")
        y -= 8*mm

        payback_str = (
            f"{q['payback_years']:.1f} years"
            if q["payback_years"] != math.inf else "N/A"
        )
        returns_rows = [
            ("Annual Saving",    f"{sym} {fmt(q['annual_saving'])}"),
            ("Payback Period",   payback_str),
            ("25-Year Net Gain", f"{sym} {fmt(q['net_25yr'])}"),
        ]
        self._draw_table(c, y, returns_rows, w)

        c.save()

    def _draw_table(self, c, y, rows, page_width, highlight_last=False):
        row_h  = 8*mm
        col1_x = 20*mm

        for i, (label, value) in enumerate(rows):
            bg = colors.HexColor("#f0f4ff") if i % 2 == 0 else colors.white
            if highlight_last and i == len(rows) - 1:
                c.setFillColor(colors.HexColor("#1a1a2e"))
                c.rect(15*mm, y - 2*mm, page_width - 30*mm, row_h, fill=True, stroke=False)
                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", 11)
            else:
                c.setFillColor(bg)
                c.rect(15*mm, y - 2*mm, page_width - 30*mm, row_h, fill=True, stroke=False)
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 11)

            c.drawString(col1_x, y + 1.5*mm, label)
            c.drawRightString(page_width - 20*mm, y + 1.5*mm, value)
            y -= row_h


# ── Usage ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    gen = QuotePDFGenerator(
        region_key="za",
        currency_key="ZAR",
        area_m2=80,
        usable=0.75,
        efficiency=0.2,
    )
    gen.generate_pdf("solar_quote.pdf")