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

# --- 3. יצירת PDF (תיקון Unicode סופי) ---
def generate_pdf_report(data_dict, table_rows):
    # הגדרת אובייקט עם תמיכה ביוניקוד
    pdf = FPDF()
    pdf.add_page()
    
    # בדיקת קיום פונטים
    font_path = "arial.ttf"
    font_bold_path = "arialbd.ttf"
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"הקובץ {font_path} לא נמצא בתיקיית השרת.")

    # הוספת פונטים - כאן התיקון הקריטי
    pdf.add_font("ArialHeb", style="", fname=font_path)
    pdf.add_font("ArialHeb", style="B", fname=font_bold_path)
    
    # קביעת הפונט כברירת מחדל לכל הדוח
    pdf.set_font("ArialHeb", size=12)

    # כותרת ותאריך
    pdf.set_font("ArialHeb", size=10)
    pdf.cell(0, 5, txt=f"תאריך הפקה: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='R')
    
    pdf.set_font("ArialHeb", style="B", size=22)
    pdf.set_text_color(0, 51, 102) 
    pdf.cell(0, 15, txt="דוח סימולציית נטו ופריסת מס", ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("ArialHeb", size=12)
    pdf.cell(0, 8, txt=f"לקוח: {data_dict['client_name']} | ת.ז: {data_dict['client_id']}", ln=True, align='R')
    pdf.cell(0, 8, txt=f"סוכן מטפל: {data_dict['agent_name']}", ln=True, align='R')
    pdf.line(10, pdf.get_y()+2, 200, pdf.get_y()+2)
    
    # נתונים כספיים
    pdf.ln(10)
    pdf.set_font("ArialHeb", style="B", size=14)
    pdf.cell(0, 10, txt="סיכום ערכי המענק:", ln=True, align='R')
    pdf.set_font("ArialHeb", size=12)
    pdf.cell(0, 8, txt=f"ברוטו מענק: {fmt_num(data_dict['total_grant'])} ש''ח", ln=True, align='R')
    pdf.cell(0, 8, txt=f"חלק פטור: {fmt_num(data_dict['exempt'])} ש''ח", ln=True, align='R')
    pdf.cell(0, 8, txt=f"חלק חייב בפריסה: {fmt_num(data_dict['taxable'])} ש''ח", ln=True, align='R')

    # שורת הרווח בנטו
    pdf.ln(5)
    pdf.set_fill_color(200, 255, 200)
    pdf.set_font("ArialHeb", style="B", size=16)
    pdf.cell(0, 15, txt=f"נטו סופי ללקוח (לאחר פריסה): {fmt_num(data_dict['net_total'])} ש''ח", ln=True, align='R', fill=True)
    
    pdf.set_font("ArialHeb", style="B", size=13)
    pdf.set_text_color(0, 80, 0)
    pdf.cell(0, 10, txt=f"חיסכון מס משוער בפריסה: {fmt_num(data_dict['savings'])} ש''ח", ln=True, align='R')
    pdf.set_text_color(0, 0, 0)

    # טבלה
    pdf.ln(10)
    pdf.set_font("ArialHeb", style="B", size=10)
    pdf.set_fill_color(230, 240, 255)
    # סדר עמודות מימין לשמאל
    cols = [("נטו", 35), ("מס", 35), ("הכנסה כוללת", 45), ("חלק מענק", 45), ("שנה", 20)]
    for text, width in cols:
        pdf.cell(width, 10, text, border=1, align='C', fill=True)
    pdf.ln()
    
    pdf.set_font("ArialHeb", size=10)
    for row in table_rows:
        pdf.cell(35, 8, row['נטו'], border=1, align='C')
        pdf.cell(35, 8, row['מס'], border=1, align='C')
        pdf.cell(45, 8, row['הכנסה שנתית'], border=1, align='C')
        pdf.cell(45, 8, row['חלק המענק'], border=1, align='C')
        pdf.cell(20, 8, str(row['שנה']), border=1, align='C')
        pdf.ln()

    # חתימות והבהרה
    pdf.ln(20)
    pdf.cell(90, 10, "חתימת הלקוח: ________________", align='R')
    pdf.cell(90, 10, "חתימת הסוכן: ________________", align='R')
    
    pdf.set_y(-25)
    pdf.set_font("ArialHeb", size=8)
    pdf.cell(0, 5, "הבהרה: המידע בסימולציה זו מוערך בלבד ואינו מהווה אישור סופי מרשויות המס.", ln=True, align='C')
    
    return pdf.output()

# --- 4. הממשק ---
def main():
    st.set_page_config(page_title="מחשבון פריסה 2026", layout="wide")
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
        inc_now = st.number_input("הכנסה שנתית נוכחית", value=240000)
        inc_future_mo = st.number_input("הכנסה חודשית עתידית", value=7000)
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
            "שנה": str(y), 
            "חלק המענק": fmt_num(annual_part), 
            "הכנסה שנתית": fmt_num(inc + annual_part), 
            "מס": fmt_num(t), 
            "נטו": fmt_num(annual_part - t)
        })

    savings = tax_no_spread - total_tax_spread
    net_total = total_grant - total_tax_spread

    # תצוגה
    st.title(f"ניתוח נטו עבור {client_name}")
    col1, col2, col3 = st.columns(3)
    col1.metric("נטו סופי ללקוח", f"₪{fmt_num(net_total)}")
    col2.metric("חיסכון במס", f"₪{fmt_num(savings)}")
    col3.metric("סה''כ מס לתשלום", f"₪{fmt_num(total_tax_spread)}")
    
    st.table(pd.DataFrame(table_data))

    if st.button("📄 הפק דוח PDF"):
        pdf_data = {
            'agent_name': agent_name, 'client_name': client_name, 'client_id': client_id,
            'total_grant': total_grant, 'exempt': exempt_val, 'taxable': taxable_val,
            'tax_with_spread': total_tax_spread, 'tax_no_spread': tax_no_spread,
            'savings': savings, 'net_total': net_total
        }
        try:
            pdf_out = generate_pdf_report(pdf_data, table_data)
            st.download_button("📥 הורד דוח PDF", data=bytes(pdf_out), file_name=f"Report_{client_name}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"שגיאה בהפקת PDF: {e}")

if __name__ == "__main__":
    main()
