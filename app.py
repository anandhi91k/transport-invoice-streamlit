import streamlit as st
import pandas as pd
from datetime import date, timedelta
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm

st.set_page_config(page_title="Transport Invoice Generator", page_icon="🚚", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1200px;}
.invoice-head {background:#17365D;color:white;padding:18px 22px;border-radius:10px;margin-bottom:14px;}
.small-note {color:#64748b;font-size:0.88rem;}
@media (max-width: 640px) {.block-container {padding-left:1rem;padding-right:1rem;}}
</style>
""", unsafe_allow_html=True)

PROFILES = {
    "SARANYA TRANSPORTS": {
        "name": "SARANYA TRANSPORTS",
        "address": "4/29 B, MUTHUGOUNDANPUDHUR, KALIYAPURAM, SULUR, COIMBATORE-641406",
        "mobile": "9965508319",
        "email": "",
        "gstin": "",
        "bank": "Canara Bank / SBI",
        "account_name": "SARANYA TRANSPORTS",
        "account_number": "120938491829",
        "ifsc": "CNRB0002134",
        "branch": "Sulur Branch, Coimbatore",
        "upi": "9965508319@ibl",
    },
    "AK TEMPO SERVICE": {
        "name": "AK TEMPO SERVICE",
        "address": "1/42, SENGATHURAI ROAD, SULUR, COIMBATORE, TAMIL NADU - 641402",
        "mobile": "9443263166",
        "email": "aktemposervice@gmail.com",
        "gstin": "",
        "bank": "State Bank of India (SBI)",
        "account_name": "AK TEMPO SERVICE",
        "account_number": "",
        "ifsc": "",
        "branch": "Sulur Branch, Coimbatore",
        "upi": "",
    },
}

def money(v):
    try:
        return f"₹{float(v):,.2f}"
    except Exception:
        return "₹0.00"

def make_pdf(data):
    buff = BytesIO()
    doc = SimpleDocTemplate(buff, pagesize=A4, rightMargin=14*mm, leftMargin=14*mm,
                            topMargin=13*mm, bottomMargin=13*mm)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("InvoiceTitle", parent=styles["Title"], fontSize=17, leading=20,
                           textColor=colors.HexColor("#17365D"), alignment=TA_CENTER, spaceAfter=5)
    normal = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8.5, leading=11)
    story = []
    story.append(Paragraph(data["bill_title"].upper(), title))
    story.append(Paragraph(f"<b>{data['company_name']}</b><br/>{data['company_address']}<br/>Mobile: {data['company_mobile']}", normal))
    story.append(Spacer(1, 8))
    meta = [
        ["Invoice No.", data["invoice_no"], "Invoice Date", data["invoice_date"].strftime("%d/%m/%Y")],
        ["Billing Month", data["billing_month"], "Due Date", data["due_date"].strftime("%d/%m/%Y")],
    ]
    t = Table(meta, colWidths=[27*mm, 58*mm, 25*mm, 55*mm])
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.4,colors.grey),("BACKGROUND",(0,0),(0,-1),colors.HexColor("#EAF0F7")),
                           ("BACKGROUND",(2,0),(2,-1),colors.HexColor("#EAF0F7")),("FONTSIZE",(0,0),(-1,-1),8),
                           ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("PADDING",(0,0),(-1,-1),6)]))
    story += [t, Spacer(1, 10)]
    parties = [
        [Paragraph("<b>Bill From</b>", normal), Paragraph("<b>Bill To</b>", normal)],
        [Paragraph(f"{data['company_name']}<br/>{data['company_address']}<br/>Mobile: {data['company_mobile']}", normal),
         Paragraph(f"{data['client_name']}<br/>{data['client_address']}<br/>Mobile: {data['client_mobile']}<br/>GSTIN: {data['client_gstin']}", normal)]
    ]
    pt = Table(parties, colWidths=[82.5*mm,82.5*mm])
    pt.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.4,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#EAF0F7")),
                            ("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),7)]))
    story += [pt, Spacer(1, 10)]
    rows = [["S.No.", "Date", "Vehicle No.", "Bill No.", "From / Description", "To", "Weight", "Days", "Amount"]]
    for i, r in enumerate(data["items"], 1):
        rows.append([str(i), r["Date"], r["Vehicle No."], r["Bill No."], r["From / Description"],
                     r["To"], r["Weight"], r["Days"], money(r["Amount"])])
    widths = [10*mm,18*mm,23*mm,15*mm,33*mm,23*mm,17*mm,13*mm,26*mm]
    it = Table(rows, colWidths=widths, repeatRows=1)
    it.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17365D")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                            ("GRID",(0,0),(-1,-1),0.35,colors.grey),("FONTSIZE",(0,0),(-1,-1),7),
                            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(0,0),(3,-1),"CENTER"),
                            ("ALIGN",(-1,1),(-1,-1),"RIGHT"),("PADDING",(0,0),(-1,-1),5)]))
    story += [it, Spacer(1, 8)]
    totals = [
        ["Subtotal", money(data["subtotal"])],
        [f"GST ({data['gst_rate']}%)" if data["gst_rate"] else "GST", money(data["gst_amount"])],
        ["Advance Paid", money(data["advance"])],
        ["Grand Total", money(data["balance"])],
    ]
    tt = Table(totals, colWidths=[45*mm,35*mm], hAlign="RIGHT")
    tt.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.35,colors.grey),("ALIGN",(1,0),(1,-1),"RIGHT"),
                            ("BACKGROUND",(0,-1),(-1,-1),colors.HexColor("#EAF0F7")),("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold"),
                            ("PADDING",(0,0),(-1,-1),6),("FONTSIZE",(0,0),(-1,-1),8)]))
    story += [tt, Spacer(1, 12)]
    if data["show_bank"]:
        story.append(Paragraph("<b>Bank Details</b>", normal))
        story.append(Paragraph(f"{data['bank']} | Account Name: {data['account_name']} | Account No.: {data['account_number']}<br/>"
                               f"IFSC: {data['ifsc']} | Branch: {data['branch']} | UPI: {data['upi']}", normal))
        story.append(Spacer(1, 8))
    if data["terms"]:
        story.append(Paragraph("<b>Terms & Conditions</b>", normal))
        for term in data["terms"].splitlines():
            if term.strip():
                story.append(Paragraph("• " + term.strip(), normal))
    story += [Spacer(1, 24), Paragraph(f"<b>For {data['company_name']}</b>", ParagraphStyle("right", parent=normal, alignment=TA_RIGHT)),
              Spacer(1, 22), Paragraph("<para alignment='right'>Authorised Signatory</para>", normal)]
    doc.build(story)
    buff.seek(0)
    return buff.getvalue()

st.markdown('<div class="invoice-head"><h2 style="margin:0;color:white">🚚 Transport Invoice Generator</h2><div>Prepare, preview and download transport bills</div></div>', unsafe_allow_html=True)

profile_choice = st.sidebar.selectbox("Transport company", list(PROFILES.keys()))
profile = PROFILES[profile_choice]
st.sidebar.caption("You can edit company and bank details below for each invoice.")

with st.form("invoice_form"):
    st.subheader("1. Company details")
    c1, c2 = st.columns(2)
    with c1:
        company_name = st.text_input("Company name", profile["name"])
        company_address = st.text_area("Company address", profile["address"], height=75)
        company_mobile = st.text_input("Company mobile", profile["mobile"])
    with c2:
        bill_title = st.text_input("Bill title", "MONTHLY TRANSPORT BILL")
        invoice_no = st.text_input("Invoice number", f"INV-{date.today():%Y%m%d}-001")
        invoice_date = st.date_input("Invoice date", date.today())
        billing_month = st.text_input("Billing month", date.today().strftime("%B %Y"))
        due_date = st.date_input("Due date", date.today() + timedelta(days=15))

    st.subheader("2. Customer details")
    c1, c2 = st.columns(2)
    with c1:
        client_name = st.text_input("Customer / Bill To name")
        client_address = st.text_area("Customer address", height=75)
    with c2:
        client_mobile = st.text_input("Customer mobile")
        client_gstin = st.text_input("Customer GSTIN")

    st.subheader("3. Transport trip details")
    default_items = pd.DataFrame([{
        "Date": date.today().strftime("%d/%m/%Y"), "Vehicle No.": "", "Bill No.": "",
        "From / Description": "", "To": "", "Weight": "", "Days": "1",
        "Amount": 0.0
    }])
    edited = st.data_editor(default_items, num_rows="dynamic", use_container_width=True,
                            column_config={"Amount": st.column_config.NumberColumn("Amount (₹)", min_value=0, step=100),
                                           "Days": st.column_config.TextColumn("Duration / Days")})

    st.subheader("4. Tax and payment")
    c1, c2, c3 = st.columns(3)
    with c1:
        gst_rate = st.number_input("GST rate (%)", min_value=0.0, max_value=28.0, value=0.0, step=0.5)
    with c2:
        advance = st.number_input("Advance paid (₹)", min_value=0.0, value=0.0, step=100.0)
    with c3:
        show_bank = st.checkbox("Show bank details", value=True)

    st.subheader("5. Bank details")
    c1, c2 = st.columns(2)
    with c1:
        bank = st.text_input("Bank name", profile["bank"])
        account_name = st.text_input("Account name", profile["account_name"])
        account_number = st.text_input("Account number", profile["account_number"])
    with c2:
        ifsc = st.text_input("IFSC code", profile["ifsc"])
        branch = st.text_input("Branch", profile["branch"])
        upi = st.text_input("UPI ID", profile["upi"])

    terms = st.text_area("Terms & conditions (one per line)",
                         "Goods transported at owner's risk as per standard carriage terms.\nPayment is due within 15 days from the invoice date.\nSubject to Sulur / Coimbatore jurisdiction only.")
    submitted = st.form_submit_button("Generate invoice", type="primary", use_container_width=True)

if submitted:
    items = edited.fillna("").to_dict("records")
    clean_items = []
    for row in items:
        try:
            amount = float(row.get("Amount") or 0)
        except (ValueError, TypeError):
            amount = 0.0
        clean_items.append({**row, "Amount": amount})
    subtotal = sum(x["Amount"] for x in clean_items)
    gst_amount = subtotal * gst_rate / 100
    balance = subtotal + gst_amount - advance
    data = {
        "company_name": company_name, "company_address": company_address, "company_mobile": company_mobile,
        "bill_title": bill_title, "invoice_no": invoice_no, "invoice_date": invoice_date,
        "billing_month": billing_month, "due_date": due_date, "client_name": client_name,
        "client_address": client_address, "client_mobile": client_mobile, "client_gstin": client_gstin,
        "items": clean_items, "subtotal": subtotal, "gst_rate": gst_rate, "gst_amount": gst_amount,
        "advance": advance, "balance": balance, "show_bank": show_bank, "bank": bank,
        "account_name": account_name, "account_number": account_number, "ifsc": ifsc,
        "branch": branch, "upi": upi, "terms": terms
    }
    st.session_state["invoice_data"] = data

if "invoice_data" in st.session_state:
    d = st.session_state["invoice_data"]
    st.divider()
    st.subheader("Invoice summary")
    a, b, c = st.columns(3)
    a.metric("Subtotal", money(d["subtotal"]))
    b.metric("GST", money(d["gst_amount"]))
    c.metric("Balance payable", money(d["balance"]))
    pdf = make_pdf(d)
    st.download_button("⬇️ Download invoice as PDF", data=pdf,
                       file_name=f"{d['invoice_no']}.pdf", mime="application/pdf",
                       type="primary", use_container_width=True)
    with st.expander("View trip details"):
        st.dataframe(pd.DataFrame(d["items"]), use_container_width=True)
    st.caption("Check all invoice details before downloading or sharing.")
else:
    st.info("Enter the invoice details above and click **Generate invoice** to calculate totals and prepare your PDF.")
