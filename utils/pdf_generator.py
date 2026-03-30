from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os, datetime

# Colors
DARK  = colors.HexColor("#1E293B")
GREEN = colors.HexColor("#10B981")
GREENL= colors.HexColor("#D1FAE5")
BLUE  = colors.HexColor("#3B82F6")
BLUEL = colors.HexColor("#DBEAFE")
GREY  = colors.HexColor("#64748B")
GREYL = colors.HexColor("#F8FAFC")
WHITE = colors.white
GOLD  = colors.HexColor("#F59E0B")

W, H = A4
MARGIN = 18*mm
CW = W - 2*MARGIN

def make_pdf(quote, customer, items, seller_name, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=14*mm, bottomMargin=14*mm)

    def S(name, **kw):
        return ParagraphStyle(name, **kw)

    story = []

    # ── HEADER ──────────────────────────────────────────────────────────────
    hdr_data = [[
        Paragraph(f"<b>OFFERT</b>", S("ht", fontName="Helvetica-Bold",
                   fontSize=28, textColor=WHITE, leading=32)),
        Paragraph(f"#{quote['id']:04d}<br/>"
                  f"<font size='9' color='#94A3B8'>{datetime.date.today().strftime('%d %B %Y')}</font>",
                  S("hn", fontName="Helvetica-Bold", fontSize=16, textColor=WHITE,
                    alignment=TA_RIGHT, leading=22)),
    ]]
    hdr_t = Table(hdr_data, colWidths=[CW*0.6, CW*0.4], rowHeights=[60])
    hdr_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), DARK),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",(0,0), (-1,-1), 16),
        ("RIGHTPADDING",(0,0),(-1,-1), 16),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(hdr_t)
    story.append(Spacer(1, 6*mm))

    # ── CUSTOMER + SELLER ────────────────────────────────────────────────────
    info_data = [[
        Paragraph(
            f"<b>Till:</b> {customer.get('company_name','')}<br/>"
            f"{customer.get('contact_person','')} &nbsp;|&nbsp; {customer.get('phone','')}<br/>"
            f"{customer.get('email','')}<br/>"
            f"{customer.get('address','')} {customer.get('city','')}",
            S("ci", fontName="Helvetica", fontSize=10, textColor=DARK, leading=15)
        ),
        Paragraph(
            f"<b>Från:</b> {seller_name}<br/>"
            f"Giltigt t.o.m.: <b>{quote.get('valid_until','')}</b><br/><br/>"
            f"<font color='#64748B' size='9'>Frågor? Ring eller maila oss.</font>",
            S("si", fontName="Helvetica", fontSize=10, textColor=DARK,
              leading=15, alignment=TA_RIGHT)
        ),
    ]]
    info_t = Table(info_data, colWidths=[CW*0.55, CW*0.45])
    info_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), GREYL),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("LEFTPADDING",(0,0),(0,-1), 14),
        ("RIGHTPADDING",(-1,0),(-1,-1), 14),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("LINEBELOW",  (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
    ]))
    story.append(info_t)
    story.append(Spacer(1, 8*mm))

    # ── SAVINGS HERO ─────────────────────────────────────────────────────────
    monthly = quote.get("monthly_saving", 0) or 0
    yearly  = quote.get("yearly_saving", 0) or 0

    savings_data = [[
        Paragraph(f"<b>Besparing/månad</b><br/>"
                  f"<font size='22' color='#10B981'><b>{monthly:,.0f} kr</b></font>",
                  S("sm", fontName="Helvetica", fontSize=10, textColor=GREY,
                    alignment=TA_CENTER, leading=28)),
        Paragraph(f"<b>Besparing/år</b><br/>"
                  f"<font size='22' color='#10B981'><b>{yearly:,.0f} kr</b></font>",
                  S("sy", fontName="Helvetica", fontSize=10, textColor=GREY,
                    alignment=TA_CENTER, leading=28)),
        Paragraph(f"<b>Nuv. total/mån</b><br/>"
                  f"<font size='18' color='#1E293B'><b>{quote.get('total_current',0):,.0f} kr</b></font>",
                  S("sc", fontName="Helvetica", fontSize=10, textColor=GREY,
                    alignment=TA_CENTER, leading=26)),
        Paragraph(f"<b>Vårt pris/mån</b><br/>"
                  f"<font size='18' color='#3B82F6'><b>{quote.get('total_offered',0):,.0f} kr</b></font>",
                  S("so", fontName="Helvetica", fontSize=10, textColor=GREY,
                    alignment=TA_CENTER, leading=26)),
    ]]
    sav_t = Table(savings_data, colWidths=[CW/4]*4, rowHeights=[56])
    sav_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (1,-1), GREENL),
        ("BACKGROUND", (2,0), (2,-1), GREYL),
        ("BACKGROUND", (3,0), (3,-1), BLUEL),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("GRID",       (0,0), (-1,-1), 0.5, WHITE),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(sav_t)
    story.append(Spacer(1, 8*mm))

    # ── ITEMS TABLE ──────────────────────────────────────────────────────────
    story.append(Paragraph("TJÄNSTER — JÄMFÖRELSE",
                            S("th", fontName="Helvetica-Bold", fontSize=9,
                              textColor=GREY, leading=12)))
    story.append(Spacer(1, 3*mm))

    col_w = [CW*0.16, CW*0.17, CW*0.12, CW*0.17, CW*0.12, CW*0.12, CW*0.14]
    tbl_hdr = [
        Paragraph(h, S("th2", fontName="Helvetica-Bold", fontSize=8.5,
                        textColor=WHITE, leading=11, alignment=TA_CENTER))
        for h in ["Tjänst", "Nuv. leverantör", "Nuv. pris/mån",
                   "Vår leverantör", "Vårt pris/mån", "Bindningstid", "Besparing/mån"]
    ]
    table_data = [tbl_hdr]

    for i, item in enumerate(items):
        row_bg = GREYL if i % 2 == 0 else WHITE
        saving = (item.get("price_current") or 0) - (item.get("price_offered") or 0)
        row = [
            Paragraph(item.get("service_type",""), S("td", fontName="Helvetica-Bold",
                       fontSize=9, textColor=DARK, leading=12)),
            Paragraph(item.get("provider_current","—"), S("td2", fontName="Helvetica",
                       fontSize=9, textColor=GREY, leading=12, alignment=TA_CENTER)),
            Paragraph(f"{item.get('price_current',0):,.0f} kr",
                      S("td3", fontName="Helvetica", fontSize=9, textColor=DARK,
                        leading=12, alignment=TA_CENTER)),
            Paragraph(item.get("provider_offered","—"), S("td4", fontName="Helvetica-Bold",
                       fontSize=9, textColor=BLUE, leading=12, alignment=TA_CENTER)),
            Paragraph(f"{item.get('price_offered',0):,.0f} kr",
                      S("td5", fontName="Helvetica-Bold", fontSize=9, textColor=BLUE,
                        leading=12, alignment=TA_CENTER)),
            Paragraph(f"{item.get('binding_months',0)} mån",
                      S("td6", fontName="Helvetica", fontSize=9, textColor=GREY,
                        leading=12, alignment=TA_CENTER)),
            Paragraph(f"+{saving:,.0f} kr",
                      S("td7", fontName="Helvetica-Bold", fontSize=9,
                        textColor=GREEN if saving >= 0 else colors.red,
                        leading=12, alignment=TA_CENTER)),
        ]
        table_data.append(row)

    # Total row
    total_saving = sum((i.get("price_current",0) or 0) - (i.get("price_offered",0) or 0) for i in items)
    table_data.append([
        Paragraph("TOTALT / MÅN", S("tot", fontName="Helvetica-Bold", fontSize=9,
                   textColor=WHITE, leading=12)),
        Paragraph("", S("_")),
        Paragraph(f"{quote.get('total_current',0):,.0f} kr",
                  S("tot2", fontName="Helvetica-Bold", fontSize=9, textColor=WHITE,
                    leading=12, alignment=TA_CENTER)),
        Paragraph("", S("_")),
        Paragraph(f"{quote.get('total_offered',0):,.0f} kr",
                  S("tot3", fontName="Helvetica-Bold", fontSize=9, textColor=GOLD,
                    leading=12, alignment=TA_CENTER)),
        Paragraph("", S("_")),
        Paragraph(f"+{total_saving:,.0f} kr",
                  S("tot4", fontName="Helvetica-Bold", fontSize=10, textColor=GREEN,
                    leading=12, alignment=TA_CENTER)),
    ])

    items_t = Table(table_data, colWidths=col_w)
    style_list = [
        ("BACKGROUND", (0,0), (-1,0), DARK),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#1E293B")),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING",(0,0), (-1,-1), 8),
        ("RIGHTPADDING",(0,0),(-1,-1), 8),
        ("GRID",       (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
    ]
    for i in range(1, len(table_data)-1):
        bg = GREYL if i % 2 == 1 else WHITE
        style_list.append(("BACKGROUND", (0,i), (-1,i), bg))

    items_t.setStyle(TableStyle(style_list))
    story.append(items_t)
    story.append(Spacer(1, 10*mm))

    # ── FOOTER NOTE ──────────────────────────────────────────────────────────
    footer_text = (
        f"Denna offert är giltig till och med {quote.get('valid_until','')}. "
        "Priser anges exklusive moms om inget annat anges. "
        "Vi förbehåller oss rätten till eventuella prisändringar. "
        "Kontakta oss om du har frågor."
    )
    story.append(Paragraph(footer_text,
                            S("ft", fontName="Helvetica-Oblique", fontSize=8,
                              textColor=GREY, leading=12, alignment=TA_CENTER)))
    story.append(Spacer(1, 6*mm))

    # Brand line
    brand_data = [[
        Paragraph("Tack för att du väljer oss! Vi ser fram emot ett gott samarbete.",
                  S("br", fontName="Helvetica-Bold", fontSize=10, textColor=WHITE,
                    alignment=TA_CENTER, leading=14))
    ]]
    brand_t = Table(brand_data, colWidths=[CW], rowHeights=[36])
    brand_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), DARK),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(brand_t)

    doc.build(story)
    return output_path
