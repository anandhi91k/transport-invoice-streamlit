
import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from pathlib import Path
import textwrap
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
)
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

st.set_page_config(
    page_title="Transport Bill Generator",
    page_icon="🚚",
    layout="wide"
)

DEFAULT_COMPANY_NAME = "Sri Selvamurugan Transports"
DEFAULT_COMPANY_ADDRESS = (
    "3/211-14, Silver Springs, Kangayempalayam, Sulur-641402"
)
DEFAULT_COMPANY_MOBILE = "9865412175"
DEFAULT_BILL_TITLE = "TRANSPORT BILL"

DEFAULT_CUSTOMER_NAME = "Gargi Huttensils - Albertus Pvt Ltd"
DEFAULT_CUSTOMER_ADDRESS = (
    "272/B, KALIYAPURAM, NORTH SULUR, COIMBATORE-641406"
)

SIGNATURE_PATH = Path(__file__).resolve().parent / "default_esign.png"

st.markdown("""
<style>
.stApp {background:#f4f7fb;color:#172b4d}
[data-testid="stHeader"] {background:#f4f7fb}
[data-testid="stSidebar"] {background:#edf2f8;border-right:1px solid #dce4ef}
.block-container {max-width:1240px;padding-top:1.5rem;padding-bottom:3rem}
h1,h2,h3 {color:#17365d!important}
div[data-testid="stForm"] {
  background:white;border:1px solid #dce4ef;border-radius:14px;
  padding:1.25rem;box-shadow:0 3px 14px #142d500d
}
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stDateInput"] input,
div[data-testid="stNumberInput"] input {
  background:white!important;color:#172b4d!important;
  border:1px solid #cbd5e1!important;border-radius:8px!important
}
div[data-testid="stMetric"] {
  background:white;border:1px solid #dce4ef;border-radius:12px;padding:14px
}
div[data-testid="stMetricValue"] {color:#17365d!important}
.stButton button,.stDownloadButton button,
button[kind="primaryFormSubmit"] {
  background:#17365d!important;color:white!important;border:0!important;
  border-radius:9px!important;font-weight:650!important;min-height:2.8rem
}
.app-banner {
  background:linear-gradient(115deg,#17365d,#24558e);color:white;
  border-radius:16px;padding:24px 28px;margin-bottom:18px;
  box-shadow:0 8px 22px #17365d24
}
.app-banner h1 {color:white!important;margin:0 0 5px;font-size:2rem}
.app-banner p {color:#e8f0fa!important;margin:0}
.section-note {color:#64748b;font-size:.9rem;margin-top:-8px;margin-bottom:12px}
hr {border-color:#dce4ef!important}
@media(max-width:700px) {
  .block-container {padding-left:.8rem;padding-right:.8rem}
  .app-banner {padding:18px}
  .app-banner h1 {font-size:1.45rem}
}
</style>
""", unsafe_allow_html=True)


def money(value):
    try:
        return f"{float(value or 0):,.2f}"
    except (TypeError, ValueError):
        return "0.00"


def make_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm
    )

    styles = getSampleStyleSheet()
    navy = colors.HexColor("#17365D")
    pale = colors.HexColor("#EAF0F7")

    body = ParagraphStyle(
        "InvoiceSmall",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=11
    )
    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=17,
        textColor=navy,
        alignment=1,
        spaceAfter=5
    )
    bill_number_style = ParagraphStyle(
        "BillNumber",
        parent=body,
        fontSize=6.5,
        leading=8,
        wordWrap="CJK",
        splitLongWords=1
    )
    destination_style = ParagraphStyle(
        "Destination",
        parent=body,
        fontSize=6.5,
        leading=8,
        wordWrap="CJK",
        splitLongWords=1
    )

    story = [
        Paragraph(data["bill_title"].upper(), title_style),
        Paragraph(
            f"<b>{data['company_name']}</b><br/>"
            f"{data['company_address']}<br/>"
            f"Mobile: {data['company_mobile']}",
            body
        ),
        Spacer(1, 8)
    ]

    invoice_meta = [[
        "Invoice No.", data["invoice_no"],
        "Invoice Date", data["invoice_date"].strftime("%d/%m/%Y")
    ], [
        "Billing Month", data["billing_month"], "", ""
    ]]
    meta_table = Table(
        invoice_meta,
        colWidths=[25 * mm, 58 * mm, 24 * mm, 58 * mm]
    )
    meta_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), pale),
        ("BACKGROUND", (2, 0), (2, 0), pale),
        ("SPAN", (2, 1), (3, 1)),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    story.extend([meta_table, Spacer(1, 9)])

    parties = [
        [Paragraph("<b>COMPANY</b>", body), Paragraph("<b>BILL TO</b>", body)],
        [
            Paragraph(
                f"<b>{data['company_name']}</b><br/>"
                f"{data['company_address']}<br/>"
                f"Mobile: {data['company_mobile']}",
                body
            ),
            Paragraph(
                f"<b>{data['client_name']}</b><br/>{data['client_address']}",
                body
            )
        ]
    ]
    parties_table = Table(parties, colWidths=[82.5 * mm, 82.5 * mm])
    parties_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), pale),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 7)
    ]))
    story.extend([parties_table, Spacer(1, 9)])

    rows = [[
        "S.No.", "Date", "Vehicle No.", "Bill No(s)",
        "To", "Weight", "Timing", "Amount"
    ]]

    for index, row in enumerate(data["items"], start=1):
        rows.append([
            str(index),
            str(row.get("Date", "")),
            str(row.get("Vehicle No.", "")),
            Paragraph(
                "<br/>".join(
                    escape(line.strip())
                    for line in str(row.get("Bill No", "")).splitlines()
                    if line.strip()
                ),
                bill_number_style
            ),
            Paragraph(
                "<br/>".join(
                    escape(line)
                    for line in textwrap.wrap(
                        str(row.get("To", "")).strip(),
                        width=19,
                        break_long_words=True,
                        break_on_hyphens=True
                    )
                ),
                destination_style
            ),
            str(row.get("Weight", "")),
            str(row.get("Timing", "")),
            money(row.get("Amount", 0))
        ])

    trips_table = Table(
        rows,
        colWidths=[
            9 * mm, 16 * mm, 22 * mm, 38 * mm,
            40 * mm, 18 * mm, 25 * mm, 18 * mm
        ],
        repeatRows=1
    )
    trips_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#9AA9BC")),
        ("FONTSIZE", (0, 0), (-1, 0), 6.8),
        ("FONTSIZE", (0, 1), (-1, -1), 6.8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (3, -1), "CENTER"),
        ("ALIGN", (5, 1), (-1, -1), "CENTER"),
        ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
        ("WORDWRAP", (0, 0), (-1, -1), "CJK"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
    ]))
    story.extend([trips_table, Spacer(1, 8)])

    total_table = Table(
        [["GRAND TOTAL", money(data["grand_total"])]],
        colWidths=[43 * mm, 35 * mm],
        hAlign="RIGHT"
    )
    total_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (-1, -1), pale),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9)
    ]))
    story.extend([total_table, Spacer(1, 12)])

    bank_lines = [
        ("Bank Name", data["bank"]),
        ("Account Name", data["account_name"]),
        ("Account Number", data["account_number"]),
        ("IFSC", data["ifsc"]),
        ("Branch", data["branch"]),
        ("UPI ID", data["upi"])
    ]
    filled_bank_lines = [
        f"<b>{label}:</b> {value}"
        for label, value in bank_lines if value.strip()
    ]
    story.append(Paragraph("<b>Bank Details</b>", body))
    if filled_bank_lines:
        story.append(Paragraph("<br/>".join(filled_bank_lines), body))
    else:
        story.append(Paragraph("Bank details will be added later.", body))
    story.append(Spacer(1, 18))

    if SIGNATURE_PATH.exists():
        try:
            image_reader = ImageReader(str(SIGNATURE_PATH))
            image_width, image_height = image_reader.getSize()
            target_width = 42 * mm
            target_height = target_width * image_height / image_width
            signature = RLImage(
                str(SIGNATURE_PATH),
                width=target_width,
                height=target_height,
                hAlign="RIGHT"
            )
            story.extend([
                Table(
                    [[signature]],
                    colWidths=[75 * mm],
                    hAlign="RIGHT",
                    style=TableStyle([
                        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0)
                    ])
                ),
                Spacer(1, 2)
            ])
        except Exception:
            story.append(Paragraph("[Signature image could not be loaded]", body))
    else:
        story.append(Paragraph(
            "<i>Signature image file not found. Add default_esign.png "
            "beside app.py.</i>",
            body
        ))

    signoff = Table(
        [
            [Paragraph(f"<b>For {data['company_name']}</b>", body)],
            [Paragraph("Authorised Signatory", body)]
        ],
        colWidths=[75 * mm],
        hAlign="RIGHT"
    )
    signoff.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2)
    ]))
    story.append(signoff)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


st.markdown(
    '<div class="app-banner">'
    '<h1>🚚 Transport Bill Generator</h1>'
    '<p>Create transport bills and download a professionally formatted PDF.</p>'
    '</div>',
    unsafe_allow_html=True
)

with st.sidebar:
    st.markdown("### Company profile")
    st.caption("Default company: Sri Selvamurugan Transports")
    st.caption("Company and bank details can be edited in the form.")
    st.markdown("---")
    st.markdown("**Workflow**")
    st.caption("1. Confirm company and customer details")
    st.caption("2. Add transport trip rows")
    st.caption("3. Generate and download the PDF")

st.markdown("## 01 · Company and invoice details")
st.markdown(
    '<div class="section-note">Company information and invoice reference.</div>',
    unsafe_allow_html=True
)

left, right = st.columns(2)
with left:
    company_name = st.text_input("Company name", DEFAULT_COMPANY_NAME)
    company_address = st.text_area(
        "Company address", DEFAULT_COMPANY_ADDRESS, height=85
    )
    company_mobile = st.text_input(
        "Company mobile number", DEFAULT_COMPANY_MOBILE
    )
with right:
    bill_title = st.text_input("Bill title", DEFAULT_BILL_TITLE)
    invoice_no = st.text_input(
        "Invoice number", f"INV-{date.today():%Y%m%d}-001"
    )
    invoice_date = st.date_input("Invoice date", date.today())
    billing_month = st.text_input(
        "Billing month", date.today().strftime("%B %Y")
    )

st.markdown("---")
st.markdown("## 02 · Customer details")
left, right = st.columns(2)
with left:
    client_name = st.text_input(
        "Customer / Bill To name", DEFAULT_CUSTOMER_NAME
    )
    client_address = st.text_area(
        "Customer address", DEFAULT_CUSTOMER_ADDRESS, height=85
    )
with right:
    st.info("Customer mobile number and GSTIN are not included.")

st.markdown("---")
st.markdown("## 03 · Transport trip details")
st.markdown(
    '<div class="section-note">Add a row for each trip. '
    'Enter the charge in the final column.</div>',
    unsafe_allow_html=True
)

default_trips = pd.DataFrame([{
    "Date": date.today().strftime("%d/%m/%Y"),
    "Vehicle No.": "",
    "To": "",
    "Weight": "",
    "Timing": "10am-3pm",
    "Amount": 0.0
}])

trips = st.data_editor(
    default_trips,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Amount": st.column_config.NumberColumn(
            "Amount", min_value=0, step=100, format="%.2f"
        ),
        "To": st.column_config.TextColumn(
            "To / Destination", width="medium"
        ),
        "Timing": st.column_config.TextColumn(
            "Timing", width="medium"
        )
    },
    key="trip_editor"
)

st.markdown("### Bill number(s) for each S.No.")
st.caption(
    "Enter bill numbers up to 25 characters (letters, digits and symbols). "
    "Press Enter for another bill number on the same S.No.; long numbers "
    "will wrap within the PDF column."
)

bill_numbers_by_row = []
for row_index in range(len(trips)):
    existing_bill = str(trips.iloc[row_index].get("Bill No", "") or "")
    bill_text = st.text_area(
        f"Bill No – S.No. {row_index + 1}",
        value=existing_bill,
        key=f"bill_numbers_row_{row_index}",
        height=68,
        placeholder="Up to 25 characters; press Enter for the next bill number."
    )
    bill_numbers_by_row.append(bill_text)

st.markdown("---")
st.markdown("## 04 · Bank details")
st.caption("You can enter these details later, once finalised.")
col_a, col_b = st.columns(2)
with col_a:
    bank = st.text_input("Bank name", value="")
    account_name = st.text_input("Account name", value="")
    account_number = st.text_input("Account number", value="")
with col_b:
    ifsc = st.text_input("IFSC code", value="")
    branch = st.text_input("Branch", value="")
    upi = st.text_input("UPI ID (optional)", value="")

terms = st.text_area(
    "Terms and conditions (one per line)",
    "Goods transported at owner's risk as per standard carriage terms.\n"
    "Subject to Sulur / Coimbatore jurisdiction only."
)

submitted = st.button(
    "Generate invoice",
    type="primary",
    use_container_width=True
)

if submitted:
    items = []
    for row_index, row in enumerate(trips.fillna("").to_dict("records")):
        row["Bill No"] = (
            bill_numbers_by_row[row_index]
            if row_index < len(bill_numbers_by_row)
            else str(row.get("Bill No", ""))
        )
        amount = pd.to_numeric(row.get("Amount", 0), errors="coerce")
        row["Amount"] = float(amount) if pd.notna(amount) else 0.0
        items.append(row)

    grand_total = sum(item["Amount"] for item in items)

    st.session_state.invoice_data = {
        "company_name": company_name,
        "company_address": company_address,
        "company_mobile": company_mobile,
        "bill_title": bill_title,
        "invoice_no": invoice_no,
        "invoice_date": invoice_date,
        "billing_month": billing_month,
        "client_name": client_name,
        "client_address": client_address,
        "items": items,
        "grand_total": grand_total,
        "bank": bank,
        "account_name": account_name,
        "account_number": account_number,
        "ifsc": ifsc,
        "branch": branch,
        "upi": upi,
        "terms": terms
    }

if "invoice_data" in st.session_state:
    data = st.session_state.invoice_data
    st.markdown("---")
    st.markdown("## Invoice summary")
    st.metric("GRAND TOTAL", money(data["grand_total"]))

    st.download_button(
        "⬇ Download Transport Bill PDF",
        make_pdf(data),
        file_name=f"{data['invoice_no']}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )

    with st.expander("Review trip entries"):
        st.dataframe(
            pd.DataFrame(data["items"]),
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        "Please verify the invoice details and amount before issuing the bill."
    )
else:
    st.info(
        "Confirm the details above, add the trip entries, and select "
        "**Generate invoice** to prepare the PDF."
    )
