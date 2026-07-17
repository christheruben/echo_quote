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

# Used to size the system from usage. Without a collected region, we assume
# a mid-range US peak-sun value; revisit if region capture gets added back.
DEFAULT_PEAK_SUN = 4.5

ROOF_TYPE_DERATE = {
    "shingle": 1.00,
    "tile":    0.95,
    "metal":   1.00,
    "flat":    0.85,
}

PROPERTY_TYPE_LABELS = {
    "single family": "Single Family Home",
    "multifamily":   "Multifamily Property",
    "commercial":    "Commercial Property",
}


class QuotePDFGenerator:
    def __init__(self, full_name: str, address: str, property_type: str,
                 roof_type: str, monthly_bill: float, currency_key: str = "USD"):
        self.full_name = full_name
        self.address = address
        self.property_type = property_type
        self.roof_type = roof_type
        self.q = self.calculate_quote(monthly_bill, roof_type, currency_key)

    def calculate_quote(self, monthly_bill: float, roof_type: str, currency_key: str):
        cur = CURRENCIES.get(currency_key, CURRENCIES["USD"])
        derate = ROOF_TYPE_DERATE.get(roof_type.strip().lower(), 1.0)

        annual_bill    = monthly_bill * 12
        annual_kwh     = annual_bill / cur["elecRate"]
        system_kw      = (annual_kwh / (DEFAULT_PEAK_SUN * 365)) / derate
        num_panels     = max(0, round(system_kw * 1000 / 400))  # ~400W panels
        annual_saving  = annual_kwh * cur["elecRate"]
        total_cost     = system_kw * 1000 * cur["installPerW"]

        hardware  = total_cost * 0.50
        inverter  = total_cost * 0.15
        labour    = total_cost * 0.25
        misc      = total_cost * 0.10

        payback = total_cost / annual_saving if annual_saving > 0 else math.inf
        net_25  = annual_saving * 25 - total_cost

        return {
            "currency":      currency_key,
            "sym":           cur["sym"],
            "monthly_bill":  monthly_bill,
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
        c.drawString(20*mm, h - 38*mm, self.full_name)
        c.drawString(20*mm, h - 44*mm, self.address)
        c.drawString(20*mm, h - 50*mm, PROPERTY_TYPE_LABELS.get(self.property_type.strip().lower(), self.property_type))

        # ── System Summary ────────────────────────────────────────────────────
        y = h - 80*mm
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(20*mm, y, "System Summary")
        y -= 8*mm

        summary_rows = [
            ("Roof Type",         self.roof_type.title()),
            ("System Size",       f"{fmt(q['system_kw'])} kW"),
            ("Number of Panels",  str(q["num_panels"])),
            ("Annual Production", f"{fmt(q['annual_kwh'])} kWh"),
            ("Current Monthly Bill", f"{sym} {fmt(q['monthly_bill'])}"),
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
        buf.seek(0)
        return buf.getvalue()

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
        full_name="John Smith",
        address="1234 Maple Drive, San Diego, California",
        property_type="single family",
        roof_type="tile",
        monthly_bill=200.0,
        currency_key="USD",
    )
    with open("solar_quote.pdf", "wb") as f:
        f.write(gen.generate_pdf())