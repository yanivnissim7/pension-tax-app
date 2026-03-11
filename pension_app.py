import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
from datetime import datetime, date

# --- 1. מנוע חישוב מס (2026) ---
def calculate_tax_detailed(annual_income, points=2.25):
    brackets = [(84120, 0.10), (120720, 0.14), (193800, 0.20), (269280, 0.31), (560280, 0.35), (721560, 0.47), (float('inf'), 0.50)]
    tax, prev_limit = 0, 0
    for limit, rate in brackets:
        if annual_income > limit:
            tax += (limit - prev_limit) * rate
            prev_limit = limit
        else:
            tax += (annual_income - prev_limit) * rate
            break
    surtax = max(0, (annual_income - 721560) * 0.03)
    return max(0, (tax + surtax) - (points * 2904))

def hb(text):
    return str(text)[::-1] if text else ""

def fmt_num(num):
    return f"{float(num):,.0f}"

# --- 2. מנוע יצירת PDF ---
def generate_pdf_report(data_dict):
    pdf = FPDF()
    pdf.add_page()
    
    font_reg = r"C:\Windows\Fonts\arial.ttf"
    font_bold = r"C:\Windows\Fonts\arialbd.ttf"
    if not os.path.exists(font_reg): font_reg = "arial.ttf"
    if not os.path.exists(font_bold): font_bold = "arialbd.ttf"
    
    pdf.add_font("ArialHeb", style="", fname=font_reg)
    pdf.add_font("ArialHeb", style="B", fname=font_bold)
    
    pdf.set_font("ArialHeb", size=10)
    pdf.cell(0, 5, txt=f"{datetime.now().strftime('%d/%m/%Y')} :{hb('תאריך הפקה')}", ln=True, align='L')
    pdf.set_font("ArialHeb", style="B", size=20)
    pdf.cell(0, 15, txt=hb("דוח ניתוח אופטימיזציית פריסה"), ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_font("ArialHeb", size=14)
    pdf.cell(0, 8, txt=hb(f"לקוח: {data_dict['client_name']} | ת.ז: {data_dict['client_id']}"), ln=True, align='R')
    pdf.cell(0, 8, txt=hb(f"סוכן מטפל: {data_dict['agent_name']}"), ln=True, align='R')
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)

    pdf.set_font("ArialHeb", size=13)
    pdf.cell(0, 9, txt=f"{hb('ש''ח')} {fmt_num(data_dict['total_grant'])} :{hb('מענק ברוטו')}", ln=True, align='R')
    pdf.cell(0, 9, txt=f"{hb('ש''ח')} {fmt_num(data_dict['exempt'])} :{hb('מתוכו פטור ממס')}", ln=True, align='R')
    pdf.cell(0, 9, txt=f"{hb('ש''ח')} {fmt_num(data_dict['taxable'])} :{hb('מתוכו חייב במס')}", ln=True, align='R')
    
    pdf.ln(2)
    pdf.cell(0, 9, txt=f"{hb('ש''ח')} {fmt_num(data_dict['tax_no_spread'])} :{hb('מס ללא פריסה')}", ln=True, align='R')
    pdf.set_font("ArialHeb", style="B", size=15)
    pdf.cell(0, 10, txt=f"{hb('ש''ח')} {fmt_num(data_dict['savings'])} :{hb('סך החיסכון במס בפריסה')}", ln=True, align='R')
    
    pdf.ln(5)
    pdf.set_font("ArialHeb", size=12)
    pdf.cell(0, 9, txt=f"{data_dict['years']} :{hb('(שנים)')} {hb('תקופת פריסה')}", ln=True, align='R')

    pdf.ln(10)
    pdf.set_font("ArialHeb", style="B", size=11)
    pdf.cell(45, 10, hb("מס שנתי"), border=1, align='C')
    pdf.cell(45, 10, hb("הכנסה שנתית"), border=1, align='C')
    pdf.cell(45, 10, hb("חלק מענק"), border=1, align='C')
    pdf.cell(25, 10, hb("שנה"), border=1, align='C')
    pdf.ln()
    
    pdf.set_font("ArialHeb", size=10)
    for row in data_dict['table']:
        pdf.cell(45, 8, f"{hb('ש''ח')} {row['מס']}", border=1, align='C')
        pdf.cell(45, 8, f"{hb('ש''ח')} {row['הכנסה שנתית']}", border=1, align='C')
        pdf.cell(45, 8, f"{hb('ש''ח')} {row['חלק המענק']}", border=1, align='C')
        pdf.cell(25, 8, hb(row['שנה']), border=1, align='C')
        pdf.ln()

    return bytes(pdf.output())

# --- 3. ממשק Streamlit ---
def main():
    st.set_page_config(page_title="מתכנן פרישה 2026", layout="wide")
    st.markdown("<h1 style='text-align: right;'>📊 סימולטור אופטימיזציית פרישה</h1>", unsafe_allow_html=True)

    curr_yr = datetime.now().year

    with st.sidebar:
        st.header("👤 פרטי הלקוח והסוכן")
        agent_name = st.text_input("שם הסוכן", "יניב")
        client_name = st.text_input("שם הלקוח", "ישראל ישראלי")
        client_id = st.text_input("ת.ז לקוח", "")
        retirement_date = st.date_input("תאריך סיום העסקה", value=date(curr_yr, 10, 1))
        
        st.divider()
        total_grant = st.number_input("סך המענק ברוטו", value=500000)
        
        seniority = st.number_input("וותק בשנים", value=12.0)
        salary_for_exempt = st.number_input("שכר קובע", value=13750)
        
        exempt_val = min(total_grant, seniority * min(salary_for_exempt, 13750))
        taxable_val = total_grant - exempt_val
        
        # הצגת הנתונים מתחת לברוטו
        st.write(f"🟢 **סכום פטור:** ₪{fmt_num(exempt_val)}")
        st.write(f"🔴 **סכום חייב במס:** ₪{fmt_num(taxable_val)}")
        
        st.divider()
        points = st.number_input("נקודות זיכוי", value=2.25)
        inc_now = st.number_input(f"הכנסה שנתית {curr_yr}", value=240000)
        inc_future_mo = st.number_input("הכנסה חודשית צפויה בעתיד", value=7000)
        
        st.divider()
        strategy = st.radio("סוג פריסה", ["פריסה קדימה", "פריסה אחורה"])
        start_year_choice = st.selectbox("שנת תחילת פריסה", [curr_yr, curr_yr + 1])

    # לוגיקת סעיף 8ג
    is_late_retirement = retirement_date.month >= 10
    base_max_years = max(1, min(6, int(seniority // 4 if strategy == "פריסה קדימה" else seniority)))
    
    if start_year_choice > curr_yr and not is_late_retirement:
        final_max_years = base_max_years - 1
    else:
        final_max_years = base_max_years

    with st.sidebar:
        num_years = st.slider("מספר שנות פריסה בפועל", 1, max(1, final_max_years), final_max_years)

    # חישובים לתוצאות
    tax_no_spread = calculate_tax_detailed(inc_now + taxable_val, points) - calculate_tax_detailed(inc_now, points)
    
    total_tax_spread = 0
    report_data = []
    annual_part = taxable_val / num_years
    
    for i in range(num_years):
        year_label = start_year_choice + i if strategy == "פריסה קדימה" else start_year_choice - i
        inc_loop = inc_now if year_label == curr_yr else inc_future_mo * 12
        tax_val = calculate_tax_detailed(inc_loop + annual_part, points) - calculate_tax_detailed(inc_loop, points)
        total_tax_spread += tax_val
        report_data.append({"שנה": str(year_label), "חלק המענק": fmt_num(annual_part), "הכנסה שנתית": fmt_num(inc_loop), "מס": fmt_num(tax_val)})

    if strategy == "פריסה אחורה":
        report_data = sorted(report_data, key=lambda x: x['שנה'])

    savings = tax_no_spread - total_tax_spread

    # תצוגה ראשית
    col1, col2, col3 = st.columns(3)
    col1.metric("מס ללא פריסה", f"₪{fmt_num(tax_no_spread)}")
    col2.metric("מס בפריסה", f"₪{fmt_num(total_tax_spread)}")
    col3.metric("חיסכון במס", f"₪{fmt_num(savings)}", delta=f"{fmt_num(savings)}")

    st.divider()
    st.subheader("📋 פירוט פריסה שנתי")
    st.table(pd.DataFrame(report_data))

    if st.button("📄 הפק דוח PDF"):
        pdf_data = {
            'agent_name': agent_name,
            'client_name': client_name, 'client_id': client_id, 'total_grant': total_grant,
            'exempt': exempt_val, 'taxable': taxable_val, 'tax_no_spread': tax_no_spread,
            'tax_with_spread': total_tax_spread, 'savings': savings, 'years': num_years,
            'table': report_data, 'start_year': start_year_choice
        }
        pdf_bytes = generate_pdf_report(pdf_data)
        st.download_button("📥 הורד PDF", data=pdf_bytes, file_name=f"Tax_Plan_{client_name}.pdf")

if __name__ == "__main__":
    main()
