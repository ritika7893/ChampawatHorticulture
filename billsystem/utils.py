import os
from datetime import datetime
from weasyprint import HTML, CSS
from django.core.files.base import ContentFile
from decimal import Decimal,InvalidOperation
def normalize_json(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, list):
        return [normalize_json(i) for i in obj]
    if isinstance(obj, dict):
        return {k: normalize_json(v) for k, v in obj.items()}
    return obj

def safe_decimal(val):
    try:
        return Decimal(str(val))
    except:
        return Decimal("0.00")
def demand_by_center_to_dict(instance):
    return {
        "demand_id": instance.demand_id_id,   # FK already string
        "center_name": instance.center_name,
        "demanded_quantity": str(instance.demanded_quantity),
    }
def demand_model_to_dict(instance):
    return {
        "demand_id": instance.demand_id,
        "sub_investment_name": instance.sub_investment_name,
        "unit": instance.unit,
        "allocated_quantity": str(instance.allocated_quantity),
        "rate": str(instance.rate),
    }
def get_client_ip(request):
    """
    Returns real client IP address
    Works behind proxy / load balancer
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs
        # client, proxy1, proxy2
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip

def model_to_dict(instance):
    return {
        "center_name": instance.center_name,
       
        "investment_name": instance.investment_name,
        "sub_investment_name": instance.sub_investment_name,
        "unit": instance.unit,
        "allocated_quantity": str(instance.allocated_quantity),
        "rate": str(instance.rate),
        "updated_quantity": str(instance.updated_quantity),
        "scheme_name": instance.scheme_name,
        "vikas_khand_name": instance.vikas_khand_name,
        "vidhan_sabha_name": instance.vidhan_sabha_name,
    }
def nursery_financial_model_to_dict(instance):
    return {
        "nursery_name": instance.nursery_name,
        "standard_item": instance.standard_item,
       
        "allocated_amount": str(instance.allocated_amount),
        "spent_amount": str(instance.spent_amount),
        "description": instance.description,
        "created_at": instance.created_at.isoformat() if instance.created_at else None,
    }
def beneficiary_model_to_dict(instance):
    return {
        "beneficiary_id": instance.beneficiary_id,
        "farmer_name": instance.farmer_name,
        "father_name": instance.father_name,
        "address": instance.address,
        "vikas_khand_name": instance.vikas_khand_name,
        "vidhan_sabha_name": instance.vidhan_sabha_name,
        "center_name": instance.center_name,
        "supplied_item_name": instance.supplied_item_name,
        "unit": instance.unit,
        "quantity": str(instance.quantity),
        "rate": str(instance.rate),
        "amount": str(instance.amount),
        "aadhaar_number": instance.aadhaar_number,
        "bank_account_number": instance.bank_account_number,
        "ifsc_code": instance.ifsc_code,
        "mobile_number": instance.mobile_number,
        "category": instance.category,
        "scheme_name": instance.scheme_name,
    }
def generate_billing_report_pdf(report, cancelled=False):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FONT_PATH = os.path.join(BASE_DIR, "fonts", "MANGAL.TTF")
    EN_FONT_PATH = os.path.join(BASE_DIR, "fonts", "NotoSans-Regular.ttf")
    # ---------------- DYNAMIC TABLE ROWS ----------------
    table_rows = ""
    total_amount = Decimal("0.00")

    component_data = normalize_json(report.component_data)
    num_dynamic_rows = len(component_data)
    total_rows = 14
    num_empty_rows = max(0, total_rows - num_dynamic_rows)
    for idx, comp in enumerate(component_data, start=1):
        component = comp[1] if len(comp) > 1 else ""
    
        quantity = comp[6] if len(comp) > 6 else ""   # updated_quantity
        rate = safe_decimal(comp[5] if len(comp) > 5 else "0")
        amount = safe_decimal(comp[8] if len(comp) > 8 else "0")
        ledger = comp[10] if len(comp) > 10 else ""
    
        total_amount += amount
    
        table_rows += f"""
        <tr>
            <td class="center">{idx}</td>
            <td class="en">{component}</td>
            <td class="center">{quantity}</td>
            <td class="center">{rate:.2f}</td>
            <td class="center">{amount:.2f}</td>
            <td class="en">{ledger}</td>
        </tr>
        """
               

    # Add empty rows to match the original format
    empty_rows = ""
    for _ in range(num_empty_rows):  # Increased to 5 empty rows
        empty_rows += """
        <tr>
            <td class="center">&nbsp;</td>
            <td>&nbsp;</td>
            <td class="center">&nbsp;</td>
            <td class="center">&nbsp;</td>
            <td class="center">&nbsp;</td>
            <td class="right">&nbsp;</td>
            <td>&nbsp;</td>
        </tr>
        """

    # ---------------- WATERMARK ----------------
    watermark_html = ""
    if cancelled:
        watermark_html = """
        <div class="en" style="
            position: fixed;
            top: 40%;
            left: 15%;
            font-size: 60px;
            color: rgba(255,0,0,0.2);
            transform: rotate(-45deg);
            z-index: 9999;
            pointer-events: none;">
            CANCELLED
        </div>
        """

    billing_date_str = (
        report.billing_date.strftime("%d/%m/%Y") if report.billing_date else ""
    )
    billing_center_name = report.center_name
    bill_report_id=report.bill_report_id
    # ---------------- HTML CONTENT ----------------
    html_content = f"""
<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<style>
@font-face {{
    font-family: "Mangal";
    src: url("file:///{FONT_PATH.replace(os.sep, "/")}");
}}
@font-face {{
    font-family: "EnglishFont";
    src: url("file:///{EN_FONT_PATH.replace(os.sep, "/")}");
}}
table {{
    width: 100%;
    table-layout: fixed;
    border-collapse: collapse;
}}

.bill-id-vertical{{
    position: absolute;
    top: 97px;          /* adjust slightly if needed */
    left: 122px;          /* aligns like paper */
    transform: rotate(90deg);
    font-size: 20px;
    font-weight: bold;
    letter-spacing: 3px;
}}
body {{
    font-family: "Mangal", "EnglishFont", sans-serif;
    font-size: 8px;  /* Increased font size for better visibility */
    line-height: 1.4;
    margin: 0;
    padding: 0;
}}
.en {{
    font-family: "EnglishFont", sans-serif;
}}

.container {{
    width: 100%;
    padding: 0;
    box-sizing: border-box;
    margin: 0;
}}

.center {{ text-align: center; }}
.right {{ text-align: right; }}
.bold {{ font-weight: bold; }}

.row {{
    display: flex;
    justify-content: space-between;
    margin: 4px 0;
}}

.dotted {{
    border-bottom: 1px dotted #000;
    display: inline-block;
    min-width: 190px;
}}
.dotted-new {{
    border-bottom: 1px dotted #000;
    display: inline-block;
    min-width: 150px;
}}
.dotted-date {{
    border-bottom: 1px dotted #000;
    display: inline-block;
    min-width: 109px;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 6px;
    font-size: 11px;  /* Increased table font size */
    table-layout: fixed; /* Fixed table layout */
}}

.gov-style {{
    margin-top: 6px;
}}

th, td {{
    border: 1px solid #000;
    padding: 5px 4px; 
    vertical-align: middle;
    height: 14px;  /* Increased row height */
}}

th {{
    text-align: center;
    font-weight: bold;
   
    font-size: 10px;
}}

.footer-text {{
    margin-top: 6px;
    font-size: 8px;  /* Increased footer font size */
}}

.header-row {{
    margin-bottom: 5px;
}}

/* Compact table header */
thead th {{
    padding: 4px 8px;
    line-height: 1.1;
    font-size: 9px;
    vertical-align: middle;
}}

/* Only body rows fixed height */
tbody tr {{
    height: 18px;
}}

thead tr {{
    height: auto;
}}

/* Tighten grouped header spacing */
thead tr:first-child th {{
    padding-bottom: 1px;
}}

thead tr:nth-child(2) th {{
    padding-top: 1px;
}}


table tfoot tr {{
  
    font-weight: bold;
}}
.dotted-center{{
   border-bottom: 1px dotted #000;
    display: inline-block;
    width: 330px;
}}
.dotted-udan{{
   border-bottom: 1px dotted #000;
    display: inline-block;
    width: 315px;
}}
.section-spacing {{
    margin-top: 8px;
}}

/* Column width adjustments */
.col-serial {{ width: 2%; }}
.col-item {{ width: 42%; }}
.col-quantity {{ width: 10%; }}

.col-rate {{ width: 2%; }}
.col-amount {{ width: 3%; }}
.col-ledger {{ width: 25%; }}
</style>
</head>
<body>
{watermark_html}

<div class="container">
 <div class="right bold" style="width:100%; font-size:8px;">डी-40</div>
<!-- HEADER -->
<div class="row header-row" style="margin-bottom: 10px;">
    <div class="center bold" style="font-size:13px; width: 100%;">
        उद्यान एवं खाद्य प्रसंस्करण विभाग, उत्तराखण्ड
    </div>
   
</div>

<div class="row" style="margin-top:10px;">
    <div style="width: 70%; font-size:8px;">
        सम्भरण (सप्लाई) विपन्न संख्या<span class="dotted">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>
    </div>
    <div  style="width: 30%; font-weight: bold; font-size:11px;" >दिनांक<span class="dotted-date">{billing_date_str}</span></div>
</div>

<div class="row" style="width: 100%; position: relative;">
  <div style="font-size:11px; margin-left:161px;">
    <div class="dotted-center">
     <div class="bold" style="margin-left:60px;">
    प्र० उ० स० द० केंद्र {billing_center_name}
</div>
    </div>
  </div>
  
  <!-- Positioned outside, but aligned -->
  <span style="position: absolute; right: 0; top: 0; font-size:8px;" class="bold">ऋणी</span>
</div>
<div class="row" style="width: 100%;">
  <div style="font-size:11px; margin-left:161px;">
  <div class="bill-id-vertical">
    {bill_report_id}
</div>
<div class="dotted-udan">


<div class="bold" style="margin-left:80px;">उद्यान विशेषज्ञ कोटद्वार

</div>
</div>
</div> <span style="margin-left:100px;">ऋणदाता</span>
</div>

<div class="row gov-style" style="margin-top:10px;">
    <div style="width: 100%; font-size:8px;">
        आपका आदेश संख्या <span class="dotted"></span> दिनांक <span class="dotted-new"></span>
    </div>
</div>

<div class="row" style="margin-top:5px;">
    <div style="width: 100%;font-size:8px;">
        रेलवे रसीद संख्या <span class="dotted"></span> दिनांक <span class="dotted-new"></span>
    </div>
</div>

<!-- TABLE -->
<table style="margin-top:15px;">

    <colgroup>
        <col style="width:4%">
        <col style="width:39%">   <!-- col-item -->
        <col style="width:12%">
        <col style="width:10%">
        <col style="width:15%">
        <col style="width:20%">   <!-- col-ledger -->
    </colgroup>

    <thead>
        <tr>
            <th rowspan="2">क्रं. सं०</th>
            <th rowspan="2">सम्भारित वस्तु का नाम</th>
            <th rowspan="2">संख्या का परिमाण</th>
            <th colspan="2">मूल्य</th>
            <th rowspan="2">
                स्टोर खाता<br>(Ledger) का पेज नं०
            </th>
        </tr>
        <tr>
            <th>दर</th>
            <th>धनराशि</th>
        </tr>
    </thead
  

<tbody>
{table_rows}
{empty_rows}
</tbody>
<tfoot>

<tr>
<td></td>
    <td>अग्रिम के रूप में प्राप्त धनराशि को घटाइये</td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
</tr>
<tr>
    <td></td>
    <td>शेष धनराशि</td>
     <td></td>
    <td></td>
    <td class="center">{total_amount:.2f}</td>
    <td></td>
</tr>
</tfoot>
</table>

<div class="footer-text">
    <span style="display:block; padding-left:45px;">
        यदि इस विपन्न के दिनांक से एक मास के भीतर न धनराशि भुगतान की गयी तो
    </span>
    <span>
        प्रतिवर्ष 10 प्रतिशत की दर से ब्याज लिया जायेगा ।
    </span>
</div>
<div class="footer-text" style="margin: 0 20px; font-size:8px;">

  <table style="width:100%; border-collapse:collapse; border:none;">

    <!-- Row 1: सामान्य खाता पृष्ठ -->
    <tr>
      <td style="height:18px; line-height:18px; padding:0; border:none;">
        सामान्य खाता पृष्ठ ......................
      </td>
    </tr>

    <!-- Row 2: ऋणी का पृष्ठ -->
    <tr>
      <td style="height:18px; line-height:18px; padding:0; border:none;">
        ऋणी का पृष्ठ ......................
      </td>
    </tr>

    <!-- Row 3: ऋणदाता का पृष्ठ with dotted line + अधिकारी -->
    <tr>
      <td style="padding:0; border:none;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; height:36px;">
          
          <!-- Left content -->
          <span style="line-height:18px;">
            ऋणदाता का पृष्ठ ....................
          </span>

          <!-- Right content: dotted line above, text below -->
          <div style="display:flex; flex-direction:column; align-items:flex-end; justify-content:flex-start; line-height:18px;">
            <span style="border-bottom:1px dotted #000; display:block; width:100px;">&nbsp;</span>
            <span>निर्गमन अधिकारी</span>
          </div>

        </div>
      </td>
    </tr>

  </table>
</div>

<div class="footer-text" style=" padding:0; font-size: 8px;">
    पी०एस०यू० (आर०ई०) 3 उद्यान / 106-5-7-2011-5,000 बुक्स (कम्प्यूटर/ऑफसेट)
</div>



</div>
</body>
</html>
"""

    # ---------------- PDF GENERATION ----------------
    pdf_data = HTML(string=html_content).write_pdf(
        stylesheets=[
            CSS(string='''
                @page {
                    size: 148mm 210mm;   /* A5 size */
                    margin: 6mm;         /* Proper margin */
                    padding: 0;
                }
                
                /* Ensure proper font rendering for Hindi */
                * {
                    -webkit-font-feature-settings: "kern" 1;
                    font-feature-settings: "kern" 1;
                    text-rendering: optimizeLegibility;
                }
                
                /* Adjust table row heights */
                tr {
                    height: 18px;
                }
                
                /* Remove default body margin */
                body {
                    margin: 0;
                    padding: 0;
                }
                
                /* Container adjustments */
                .container {
                    width: 100%;
                    padding: 0;
                    margin: 0;
                }
            ''')
        ]
    )

    report.recipt_file.save(
        f"{report.bill_report_id}.pdf",
        ContentFile(pdf_data),
        save=True
    )

    return report.recipt_file.url