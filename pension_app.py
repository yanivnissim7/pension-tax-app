import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
from datetime import datetime

# --- 1. פונקציית עזר לעברית (היפוך טקסט) ---
def hb(text):
    if not text:
        return ""
    # הופך את הטקסט כדי שיוצג נכון ב-PDF ללא Unicode מלא
    return str(text)[::-1]

def fmt_num(num):
    return f"{float(num):,.0f}"

# --- 2. אבטחה ---
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

# --- 3. לוגיקת חישוב מס ---
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

# --- 4. יצירת PDF (גרסת Visual Hebrew היציבה) ---
def generate_pdf_report(data_dict, table_rows):
    pdf = FPDF()
    pdf.add_page()
    
    # טעינת פונטים (וודא שהם קיימים בתיקייה הראשית ב-GitHub)
    pdf.add_font('Arial', '', 'arial.ttf', uni=True)
    pdf.add_font('Arial', 'B', 'arialbd.ttf', uni=True)
    pdf.set_font('Arial', '', 12)

    # כותרת ותאריך
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, hb(f"תאריך הפקה: {datetime.now().strftime('%d/%m/%Y')}"), ln=1, align='L')
    
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 15, hb("דוח סימולציית נטו ופריסת מס"), ln=1, align='C')
    
    pdf.set_font('Arial', '', 12)
    pdf.ln(5)
    pdf.cell(0, 8, hb(f"לקוח: {data_dict['client_name']} | ת.ז: {data_dict['client_id']}"), ln=1, align='R')
    pdf.cell(0, 8, hb(f"סוכן מטפל: {data_dict['agent_name']}"), ln=1, align='R')
    pdf.line(10, pdf.get_y()+2, 200, pdf.get_y()+2)
    
    # נתונים כספיים
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, hb("סיכום נתוני נטו ללקוח:"), ln=1, align='R')
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, hb(f"סך מענק ברוטו: {fmt_num(data_dict['total_grant'])} ש\"ח"), ln=1, align='R')
    pdf.cell(0, 8, hb(f"חלק פטור ממס: {fmt_num(data_dict['exempt'])} ש\"ח"), ln=1, align='R')
    pdf.cell(0, 8, hb(f"מס שנחסך בפריסה: {fmt_num(data_dict['savings'])} ש\"ח"), ln=1, align='R')
    
    # שורת הנטו המודגשת
    pdf.ln(5)
    pdf.set_fill_color(220, 255, 220)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 15, hb(f"נטו סופי ללקוח (לאחר פריסה): {fmt_num(data_dict['net_total'])} ש\"ח"), ln=1, align='R', fill=True)
    
    # טבלת פריסה שנתית
    pdf.ln(10)
    pdf.set_fill_color(230, 240, 255)
    pdf.set_font('Arial', 'B', 10)
    # כותרות הטבלה (מימין לשמאל)
    pdf.cell(35, 10, hb("נטו שנתי"), 1, 0, 'C', True)
    pdf.cell(35, 10, hb("מס שנתי"), 1, 0, 'C', True)
    pdf.cell(45, 10, hb("הכנסה כוללת"), 1, 0, 'C', True)
    pdf.cell(45, 10, hb("חלק המענק"), 1, 0, 'C', True)
    pdf.cell(20, 10, hb("שנה"), 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 10)
    for row in table_rows:
        pdf.cell(35, 8, hb(row['נטו']), 1, 0, 'C')
        pdf.cell(35, 8, hb(row['מס']), 1, 0, 'C')
        pdf.cell(45, 8, hb(row['הכנסה שנתית']), 1, 0, 'C')
        pdf.cell(45, 8, hb(row['חלק המענק']), 1, 0, 'C')
        pdf.cell(20, 8, hb(row['שנה']), 1, 1, 'C')

    pdf.ln(15)
    pdf.set_font('Arial', '', 11)
    pdf.cell(90, 10, hb("________________ :חתימת הלקוח"), 0, 0, 'R')
    pdf.cell(90, 10, hb("________________ :חתימת הסוכן"), 0, 1, 'R')

    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 5. הממשק הראשי ---
def main():
    st.set_page_config(page_title="מחשבון פריסה 2026", layout="wide")
    if not check_password(): st.stop()

    curr_yr = 2026
    with st.sidebar:
        st.header("פרטי דוח")
        agent_name = st.text_input("שם הסוכן", "יניב")
        client_name = st.text_input("שם הלקוח", "ישראל ישראלי")
        client_id = st.text_input("ת.ז לקוח", "")
        st.divider()
        total_grant = st.number_input("סך המענק ברוטו", value=500000)
        seniority = st.number_input("שנות וותק", value=12.0)
        salary_for_exempt = st.number_input("שכר קובע", value=13750)
        exempt_val = min(total_grant, seniority * min(salary_for_exempt, 13750))
        taxable_val = total_grant - exempt_val
        st.divider()
        points = st.number_input("נקודות זיכוי", value=2.25)
        inc_now = st.number_input("הכנסה שנתית נוכחית", value=240000)
        inc_future_mo = st.number_input("הכנסה עתידית חודשית", value=7000)
        strategy = st.radio("סוג פריסה", ["פריסה קדימה", "פריסה אחורה"])
        num_years = st.slider("שנות פריסה", 1, 6, 6)

    # חישובים
    tax_no_spread = calculate_tax_detailed(inc_now + taxable_val, points) - calculate_tax_detailed(inc_now, points)
    annual_part = taxable_val / num_years
    total_tax_spread, table_data = 0, []
    
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

    st.markdown(f"<h1 style='text-align: right;'>סימולציית נטו - {client_name}</h1>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("נטו סופי ללקוח", f"₪{fmt_num(net_total)}")
    c2.metric("חיסכון במס", f"₪{fmt_num(savings)}")
    c3.metric("סה''כ מס בפריסה", f"₪{fmt_num(total_tax_spread)}")
    
    st.table(pd.DataFrame(table_data))

    if st.button("📄 הפק דוח PDF"):
        pdf_data = {
            'agent_name': agent_name, 'client_name': client_name, 'client_id': client_id,
            'total_grant': total_grant, 'exempt': exempt_val, 'taxable': taxable_val,
            'tax_with_spread': total_tax_spread, 'savings': savings, 'net_total': net_total
        }
        try:
            pdf_bytes = generate_pdf_report(pdf_data, table_data)
            st.download_button("📥 הורד דוח PDF", data=pdf_bytes, file_name=f"Tax_Plan_{client_name}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"שגיאה בהפקת ה-PDF: {e}")

if __name__ == "__main__":
    main()
