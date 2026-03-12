import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
from datetime import datetime

# --- 1. אבטחה ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    st.markdown("<h2 style='text-align: right;'>כניסה למערכת</h2>", unsafe_allow_html=True)
    password = st.text_input("הזן קוד גישה", type="password")
    if st.button("התחבר"):
        if password == "1234":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("קוד שגוי")
    return False

# --- 2. חישובים ---
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

def fmt_num(num):
    return f"{float(num):,.0f}"

# --- 3. יצירת PDF (תיקון יוניקוד סופי) ---
def generate_pdf_report(data_dict, table_rows):
    # יצירת אובייקט PDF
    pdf = FPDF()
    pdf.add_page()
    
    # נתיבי פונטים
    font_regular = "arial.ttf"
    font_bold = "arialbd.ttf"
    
    if not os.path.exists(font_regular):
        raise FileNotFoundError(f"הפונט {font_regular} חסר בתיקייה הראשית.")

    # הוספת פונטים עם הגדרת יוניקוד מפורשת
    pdf.add_font("ArialHeb", style="", fname=font_regular)
    pdf.add_font("ArialHeb", style="B", fname=font_bold)
    pdf.set_font("ArialHeb", size=12)

    # פונקציית עזר לניקוי תווים בעייתיים
    def clean(t):
        return str(t).replace('"', "''").replace('"', "''")

    # תאריך
    pdf.set_font("ArialHeb", size=10)
    pdf.cell(0, 5, txt=f"תאריך: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='L')
    
    # כותרת
    pdf.set_font("ArialHeb", style="B", size=22)
    pdf.set_text_color(0, 51, 102) 
    pdf.cell(0, 15, txt=clean("דוח סימולציית נטו ופריסת מס"), ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("ArialHeb", size=12)
    pdf.cell(0, 8, txt=clean(f"לקוח: {data_dict['client_name']} | ת.ז: {data_dict['client_id']}"), ln=True, align='R')
    pdf.cell(0, 8, txt=clean(f"סוכן מטפל: {data_dict['agent_name']}"), ln=True, align='R')
    pdf.line(10, pdf.get_y()+2, 200, pdf.get_y()+2)
    
    # נתונים
    pdf.ln(10)
    pdf.set_font("ArialHeb", style="B", size=14)
    pdf.cell(0, 10, txt=clean("סיכום נתונים כספיים:"), ln=True, align='R')
    pdf.set_font("ArialHeb", size=12)
    pdf.cell(0, 8, txt=clean(f"ברוטו מענק: {fmt_num(data_dict['total_grant'])} ש''ח"), ln=True, align='R')
    pdf.cell(0, 8, txt=clean(f"חלק פטור: {fmt_num(data_dict['exempt'])} ש''ח"), ln=True, align='R')
    
    # שורת נטו מודגשת
    pdf.ln(5)
    pdf.set_fill_color(200, 255, 200)
    pdf.set_font("ArialHeb", style="B", size=15)
    pdf.cell(0, 12, txt=clean(f"נטו משוער ללקוח בפריסה: {fmt_num(data_dict['net_total'])} ש''ח"), ln=True, align='R', fill=True)
    
    pdf.set_font("ArialHeb", style="B", size=12)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(0, 10, txt=clean(f"חיסכון מס בפריסה: {fmt_num(data_dict['savings'])} ש''ח"), ln=True, align='R')
    pdf.set_text_color(0, 0, 0)

    # טבלה
    pdf.ln(10)
    pdf.set_font("ArialHeb", style="B", size=10)
    pdf.set_fill_color(230, 240, 255)
    
    # הגדרת עמודות
    col_w = [35, 35, 45, 45, 20]
    headers = ["נטו", "מס", "הכנסה כוללת", "חלק מענק", "שנה"]
    
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 10, clean(h), border=1, align='C', fill=True)
    pdf.ln()
    
    pdf.set_font("ArialHeb", size=10)
    for row in table_rows:
        pdf.cell(35, 8, clean(row['נטו']), border=1, align='C')
        pdf.cell(35, 8, clean(row['מס']), border=1, align='C')
        pdf.cell(45, 8, clean(row['הכנסה שנתית']), border=1, align='C')
        pdf.cell(45, 8, clean(row['חלק המענק']), border=1, align='C')
        pdf.cell(20, 8, clean(row['שנה']), border=1, align='C')
        pdf.ln()

    # חתימות
    pdf.ln(20)
    pdf.cell(90, 10, clean("חתימת הלקוח: ________________"), align='R')
    pdf.cell(90, 10, clean("חתימת הסוכן: ________________"), align='R')
    
    return pdf.output()

# --- 4. הממשק ---
def main():
    st.set_page_config(page_title="סימולטור פריסה", layout="wide")
    if not check_password(): st.stop()

    with st.sidebar:
        agent_name = st.text_input("שם הסוכן", "יניב")
        client_name = st.text_input("שם הלקוח", "ישראל ישראלי")
        client_id = st.text_input("ת.ז לקוח", "")
        total_grant = st.number_input("מענק ברוטו", value=500000)
        seniority = st.number_input("וותק", value=12.0)
        salary_for_exempt = st.number_input("שכר קובע", value=13750)
        exempt_val = min(total_grant, seniority * min(salary_for_exempt, 13750))
        taxable_val = total_grant - exempt_val
        st.divider()
        points = st.number_input("נקודות זיכוי", value=2.25)
        inc_now = st.number_input("הכנסה נוכחית", value=240000)
        inc_future_mo = st.number_input("הכנסה עתידית חודשית", value=7000)
        strategy = st.radio("סוג פריסה", ["פריסה קדימה", "פריסה אחורה"])
        num_years = st.slider("שנות פריסה", 1, 6, 6)

    # חישובים
    tax_no_spread = calculate_tax_detailed(inc_now + taxable_val, points) - calculate_tax_detailed(inc_now, points)
    annual_part = taxable_val / num_years
    total_tax_spread, table_data = 0, []
    
    curr_yr = 2026
    for i in range(num_years):
        y = curr_yr + i if strategy == "פריסה קדימה" else curr_yr - i
        inc = inc_now if y == curr_yr else inc_future_mo * 12
        t = calculate_tax_detailed(inc + annual_part, points) - calculate_tax_detailed(inc, points)
        total_tax_spread += t
        table_data.append({
            "שנה": str(y), "חלק המענק": fmt_num(annual_part), 
            "הכנסה שנתית": fmt_num(inc + annual_part), "מס": fmt_num(t), "נטו": fmt_num(annual_part - t)
        })

    savings = tax_no_spread - total_tax_spread
    net_total = total_grant - total_tax_spread

    st.title(f"ניתוח נטו - {client_name}")
    st.table(pd.DataFrame(table_data))

    if st.button("📄 הפק דוח PDF"):
        pdf_data = {
            'agent_name': agent_name, 'client_name': client_name, 'client_id': client_id,
            'total_grant': total_grant, 'exempt': exempt_val, 'taxable': taxable_val,
            'tax_with_spread': total_tax_spread, 'savings': savings, 'net_total': net_total
        }
        try:
            pdf_bytes = generate_pdf_report(pdf_data, table_data)
            st.download_button("📥 הורד PDF", data=bytes(pdf_bytes), file_name="report.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"שגיאה: {e}")

if __name__ == "__main__":
    main()
