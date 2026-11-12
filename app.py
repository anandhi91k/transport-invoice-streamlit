import streamlit as st
import pandas as pd
from datetime import date, timedelta
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm

st.set_page_config(page_title="Transport Invoice Generator", page_icon="🚚", layout="wide")
st.markdown("""
<style>
.stApp{background:#f4f7fb;color:#172b4d}
[data-testid="stHeader"]{background:#f4f7fb}
[data-testid="stSidebar"]{background:#edf2f8;border-right:1px solid #dce4ef}
.block-container{max-width:1240px;padding-top:1.5rem;padding-bottom:3rem}
h1,h2,h3{color:#17365d!important}
div[data-testid="stForm"]{background:white;border:1px solid #dce4ef;border-radius:14px;padding:1.25rem;box-shadow:0 3px 14px #142d500d}
div[data-testid="stTextInput"] input,div[data-testid="stTextArea"] textarea,div[data-testid="stDateInput"] input,div[data-testid="stNumberInput"] input{background:white!important;color:#172b4d!important;border:1px solid #cbd5e1!important;border-radius:8px!important}
div[data-testid="stSelectbox"] div[data-baseweb="select"]>div{background:white!important;border-color:#cbd5e1!important}
div[data-testid="stMetric"]{background:white;border:1px solid #dce4ef;border-radius:12px;padding:14px}
div[data-testid="stMetricValue"]{color:#17365d!important}
.stButton button,.stDownloadButton button,button[kind="primaryFormSubmit"]{background:#17365d!important;color:white!important;border:0!important;border-radius:9px!important;font-weight:650!important;min-height:2.8rem}
.app-banner{background:linear-gradient(115deg,#17365d,#24558e);color:white;border-radius:16px;padding:24px 28px;margin-bottom:18px;box-shadow:0 8px 22px #17365d24}
.app-banner h1{color:white!important;margin:0 0 5px;font-size:2rem}
.app-banner p{color:#e8f0fa!important;margin:0}
.section-note{color:#64748b;font-size:.9rem;margin-top:-8px;margin-bottom:12px}
hr{border-color:#dce4ef!important}
@media(max-width:700px){.block-container{padding-left:.8rem;padding-right:.8rem}.app-banner{padding:18px}.app-banner h1{font-size:1.45rem}}
</style>
""", unsafe_allow_html=True)

PROFILES={
 "SARANYA TRANSPORTS":{"name":"SARANYA TRANSPORTS","address":"4/29 B, MUTHUGOUNDANPUDHUR, KALIYAPURAM, SULUR, COIMBATORE-641406","mobile":"9965508319","bank":"Canara Bank","account_name":"SARANYA TRANSPORTS","account_number":"","ifsc":"","branch":"Sulur Branch, Coimbatore","upi":""},
 "AK TEMPO SERVICE":{"name":"AK TEMPO SERVICE","address":"1/42, SENGATHURAI ROAD, SULUR, COIMBATORE, TAMIL NADU - 641402","mobile":"9443263166","bank":"State Bank of India","account_name":"AK TEMPO SERVICE","account_number":"","ifsc":"","branch":"Sulur Branch, Coimbatore","upi":""}
}
def money(v): return f"₹{float(v or 0):,.2f}"

def make_pdf(d):
    buf=BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=12*mm,leftMargin=12*mm,topMargin=12*mm,bottomMargin=12*mm)
    styles=getSampleStyleSheet(); navy=colors.HexColor("#17365D"); pale=colors.HexColor("#EAF0F7")
    body=ParagraphStyle("small",parent=styles["BodyText"],fontSize=8,leading=11)
    title=ParagraphStyle("title",parent=styles["Title"],fontSize=17,textColor=navy,alignment=1)
    story=[Paragraph(d["bill_title"].upper(),title),Paragraph(f"<b>{d['company_name']}</b><br/>{d['company_address']}<br/>Mobile: {d['company_mobile']}",body),Spacer(1,8)]
    meta=[["Invoice No.",d["invoice_no"],"Invoice Date",d["invoice_date"].strftime("%d/%m/%Y")],["Billing Month",d["billing_month"],"Due Date",d["due_date"].strftime("%d/%m/%Y")]]
    t=Table(meta,colWidths=[25*mm,58*mm,24*mm,58*mm])
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.4,colors.grey),("BACKGROUND",(0,0),(0,-1),pale),("BACKGROUND",(2,0),(2,-1),pale),("FONTSIZE",(0,0),(-1,-1),8),("PADDING",(0,0),(-1,-1),6)]))
    story += [t,Spacer(1,9)]
    parties=[[Paragraph("<b>FROM</b>",body),Paragraph("<b>BILL TO</b>",body)],[Paragraph(f"<b>{d['company_name']}</b><br/>{d['company_address']}<br/>Mobile: {d['company_mobile']}",body),Paragraph(f"<b>{d['client_name']}</b><br/>{d['client_address']}<br/>Mobile: {d['client_mobile']}<br/>GSTIN: {d['client_gstin']}",body)]]
    pt=Table(parties,colWidths=[82.5*mm,82.5*mm])
    pt.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.4,colors.grey),("BACKGROUND",(0,0),(-1,0),pale),("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),7)]))
    story += [pt,Spacer(1,9)]
    rows=[["S.No.","Date","Vehicle No.","Bill No.","From / Description","To","Weight","Days","Amount"]]
    for i,r in enumerate(d["items"],1):
        rows.append([str(i),str(r.get("Date","")),str(r.get("Vehicle No.","")),str(r.get("Bill No","")),str(r.get("From / Description","")),str(r.get("To","")),str(r.get("Weight","")),str(r.get("Days","")),money(r.get("Amount",0))])
    tab=Table(rows,colWidths=[9*mm,17*mm,23*mm,14*mm,34*mm,21*mm,15*mm,12*mm,26*mm],repeatRows=1)
    tab.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),navy),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.35,colors.grey),("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(0,0),(3,-1),"CENTER"),("ALIGN",(-1,1),(-1,-1),"RIGHT"),("PADDING",(0,0),(-1,-1),5)]))
    story += [tab,Spacer(1,8)]
    totals=Table([["Subtotal",money(d["subtotal"])],[f"GST ({d['gst_rate']}%)",money(d["gst_amount"])],["Advance Paid",money(d["advance"])],["Balance Payable",money(d["balance"])]],colWidths=[43*mm,35*mm],hAlign="RIGHT")
    totals.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.35,colors.grey),("ALIGN",(1,0),(1,-1),"RIGHT"),("PADDING",(0,0),(-1,-1),6),("BACKGROUND",(0,-1),(-1,-1),pale),("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold")]))
    story += [totals,Spacer(1,10)]
    if d["show_bank"]:
        story += [Paragraph("<b>Bank Details</b>",body),Paragraph(f"{d['bank']} | Account Name: {d['account_name']} | Account No.: {d['account_number']}<br/>IFSC: {d['ifsc']} | Branch: {d['branch']} | UPI: {d['upi']}",body),Spacer(1,8)]
    if d["terms"]:
        story.append(Paragraph("<b>Terms &amp; Conditions</b>",body))
        for line in d["terms"].splitlines():
            if line.strip(): story.append(Paragraph("• "+line.strip(),body))
    story += [Spacer(1,24),Paragraph(f"<para alignment='right'><b>For {d['company_name']}</b></para>",body),Spacer(1,22),Paragraph("<para alignment='right'>Authorised Signatory</para>",body)]
    doc.build(story); buf.seek(0); return buf.getvalue()

st.markdown('<div class="app-banner"><h1>🚚 Transport Invoice Generator</h1><p>Create transport bills, calculate totals and download a professionally formatted PDF.</p></div>',unsafe_allow_html=True)
with st.sidebar:
    st.markdown("### Company profile")
    profile_key=st.selectbox("Select transport company",list(PROFILES))
    profile=PROFILES[profile_key]
    st.caption("Company and bank details are editable for each invoice.")
    st.markdown("---")
    st.markdown("**Workflow**")
    st.caption("1. Enter issuer and customer details")
    st.caption("2. Add transport trip rows")
    st.caption("3. Generate and download the PDF")

with st.form("invoice_form"):
    st.markdown("## 01 · Company and invoice details")
    st.markdown('<div class="section-note">Issuer information and invoice reference.</div>',unsafe_allow_html=True)
    l,r=st.columns(2)
    with l:
        company_name=st.text_input("Company name",profile["name"])
        company_address=st.text_area("Company address",profile["address"],height=85)
        company_mobile=st.text_input("Company mobile",profile["mobile"])
    with r:
        bill_title=st.text_input("Bill title","MONTHLY TRANSPORT BILL")
        invoice_no=st.text_input("Invoice number",f"INV-{date.today():%Y%m%d}-001")
        invoice_date=st.date_input("Invoice date",date.today())
        billing_month=st.text_input("Billing month",date.today().strftime("%B %Y"))
        due_date=st.date_input("Due date",date.today()+timedelta(days=15))
    st.markdown("---")
    st.markdown("## 02 · Customer details")
    l,r=st.columns(2)
    with l:
        client_name=st.text_input("Customer / Bill To name")
        client_address=st.text_area("Customer address",height=85)
    with r:
        client_mobile=st.text_input("Customer mobile")
        client_gstin=st.text_input("Customer GSTIN")
    st.markdown("---")
    st.markdown("## 03 · Transport trip details")
    st.markdown('<div class="section-note">Add a row for each trip. Enter the charge in the final column.</div>',unsafe_allow_html=True)
    default=pd.DataFrame([{"Date":date.today().strftime("%d/%m/%Y"),"Vehicle No.":"","Bill No":"","From / Description":"","To":"","Weight":"","Days":"1","Amount (₹)":0.0}])
    trips=st.data_editor(default,num_rows="dynamic",use_container_width=True,column_config={"Amount (₹)":st.column_config.NumberColumn(min_value=0,step=100,format="₹%.2f")},key="trip_editor")
    st.markdown("---")
    st.markdown("## 04 · Tax and payment")
    a,b,c=st.columns(3)
    with a: gst_rate=st.number_input("GST rate (%)",0.0,28.0,0.0,0.5)
    with b: advance=st.number_input("Advance paid (₹)",0.0,step=100.0)
    with c: show_bank=st.checkbox("Include bank details",True)
    st.markdown("---")
    st.markdown("## 05 · Bank details")
    a,b=st.columns(2)
    with a:
        bank=st.text_input("Bank name",profile["bank"])
        account_name=st.text_input("Account name",profile["account_name"])
        account_number=st.text_input("Account number",profile["account_number"])
    with b:
        ifsc=st.text_input("IFSC code",profile["ifsc"])
        branch=st.text_input("Branch",profile["branch"])
        upi=st.text_input("UPI ID",profile["upi"])
    terms=st.text_area("Terms and conditions (one per line)","Goods transported at owner's risk as per standard carriage terms.\nPayment is due within 15 days from the invoice date.\nSubject to Sulur / Coimbatore jurisdiction only.")
    submitted=st.form_submit_button("Generate invoice",type="primary",use_container_width=True)

if submitted:
    items=[]
    for row in trips.fillna("").to_dict("records"):
        val=pd.to_numeric(row.get("Amount (₹)",0),errors="coerce")
        row["Amount"]=float(val) if pd.notna(val) else 0.0
        items.append(row)
    subtotal=sum(x["Amount"] for x in items); gst_amount=subtotal*gst_rate/100; balance=subtotal+gst_amount-advance
    st.session_state.invoice_data={"company_name":company_name,"company_address":company_address,"company_mobile":company_mobile,"bill_title":bill_title,"invoice_no":invoice_no,"invoice_date":invoice_date,"billing_month":billing_month,"due_date":due_date,"client_name":client_name,"client_address":client_address,"client_mobile":client_mobile,"client_gstin":client_gstin,"items":items,"subtotal":subtotal,"gst_rate":gst_rate,"gst_amount":gst_amount,"advance":advance,"balance":balance,"show_bank":show_bank,"bank":bank,"account_name":account_name,"account_number":account_number,"ifsc":ifsc,"branch":branch,"upi":upi,"terms":terms}

if "invoice_data" in st.session_state:
    d=st.session_state.invoice_data
    st.markdown("---")
    st.markdown("## Invoice summary")
    x,y,z=st.columns(3)
    x.metric("Subtotal",money(d["subtotal"])); y.metric("GST",money(d["gst_amount"])); z.metric("Balance payable",money(d["balance"]))
    st.download_button("⬇  Download professionally formatted PDF",make_pdf(d),file_name=f"{d['invoice_no']}.pdf",mime="application/pdf",type="primary",use_container_width=True)
    with st.expander("Review trip entries"): st.dataframe(pd.DataFrame(d["items"]),use_container_width=True,hide_index=True)
    st.caption("Verify all company, customer, tax and bank details before issuing the invoice.")
else:
    st.info("Complete the sections above and select **Generate invoice** to calculate the bill and prepare the PDF.")
