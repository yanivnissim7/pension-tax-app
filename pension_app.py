import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
from datetime import datetime, date

# --- 1. אבטחה ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    st.markdown("<h2 style='text-align: right;'>כניסה למערכת מוגנת</h2>", unsafe_allow_html=True)
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

# --- 3. יצירת PDF (גרסת fpdf2 עם Unicode) ---
def generate_pdf_report(data_dict, table_rows):
    # הגדרת PDF תומך יוניקוד
    pdf = FPDF()
    pdf.add_page()
    
    # נתיב לפונטים
    font_path = "arial.ttf"
    font_bold_path = "arialbd.ttf"

    if not os.path.exists(font_path):
        raise FileNotFoundError("קבצי הפונטים arial.ttf ו-arialbd.ttf חסרים ב-GitHub!")

    # הוספת הפונטים עם תמיכה ביוניקוד
    pdf.add_font("ArialHeb", style="", fname=font_path)
    pdf.add_font("ArialHeb", style="B", fname=font_bold_path)
    pdf.set_font("ArialHeb", size=12)

    # כותרת ותאריך (יישור לימין באמצעות align='R')
    pdf.set_font("ArialHeb", size=10)
    pdf.cell(0, 5, txt=f"תאריך פלט: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='L')
    
    pdf.set_font("ArialHeb", style="B", size=22)
    pdf.set_text_color(0, 51, 102) 
    pdf.cell(0, 15, txt="דוח סימולציה - אופטימיזציית פריסה", ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("ArialHeb", size=12)
    pdf.cell(0, 8, txt=f"לקוח: {data_dict['client_name']} | ת.ז: {data_dict['client_id']}", ln=True, align='R')
    pdf.cell(0, 8, txt=f"סוכן מטפל: {data_dict['agent_name']}", ln=True, align='R')
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    # נתונים כספיים
    pdf.ln(5)
    pdf.cell(0, 9, txt=f"מענק ברוטו: {fmt_num(data_dict['total_grant'])} ש''ח", ln=True, align='R')
    pdf.cell(0, 9, txt=f"מתוכו פטור: {fmt_num(data_dict['exempt'])} ש''ח", ln=True, align='R')
    pdf.cell(0, 9, txt=f"סך המס לתשלום (בפריסה): {fmt_num(data_dict['tax_with_spread'])} ש''ח", ln=True, align='R')
    
    pdf.ln(3)
    pdf.set_fill_color(230, 242, 255)
    pdf.set_font("ArialHeb", style="B", size=15)
    pdf.cell(0, 12, txt=f"נטו משוער ללקוח: {fmt_num(data_dict['net_total'])} ש''ח", ln=True, align='R', fill=True)
    
    pdf.ln(5)
    pdf.set_font("ArialHeb", size=13)
    pdf.set_text_color(0, 102, 0)
    pdf.cell(0, 10, txt=f"חיסכון מס משוער בפריסה: {fmt_num(data_dict['savings'])} ש''ח", ln=True, align='R')
    
    # טבלה
    pdf.ln(8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("ArialHeb", style="B", size=10)
    # עמודות (בסדר הפוך ליישור עברית)
    pdf.cell(35, 10, "נטו שנתית", border=1, align='C')
    pdf.cell(35, 10, "מס", border=1, align='C')
    pdf.cell(45, 10, "הכנסה שנתית", border=1, align='C')
    pdf.cell(45, 10, "חלק מענק", border=1, align='C')
    pdf.cell(20, 10, "שנה", border=1, align='C')
    pdf.ln()
    
    pdf.set_font("ArialHeb", size=9)
    for row in table_rows:
        pdf.cell(35, 8, f"{row['נטו']} ש''ח", border=1, align='C')
        pdf.cell(35, 8, f"{row['מס']} ש''ח", border=1, align='C')
        pdf.cell(45, 8, f"{row['הכנסה שנתית']} ש''ח", border=1, align='C')
        pdf.cell(45, 8, f"{row['חלק המענק']} ש''ח", border=1, align='C')
        pdf.cell(20, 8, str(row['שנה']), border=1, align='C')
        pdf.ln()

    # חתימות
    pdf.ln(15)
    pdf.cell(90, 10, "חתימת הלקוח: ______________", align='R')
    pdf.cell(90, 10, "חתימת הסוכן: ______________", align='R')

    # הבהרה משפטית
    pdf.set_y(-35)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("ArialHeb", size=8)
    l1 = "הבהרה משפטית: דוח זה מהווה סימולציה ראשונית בלבד ואינו מהווה ייעוץ מס או פנסיוני מחייב."
    l2 = "הנתונים הסופיים ייקבעו על ידי רשויות המס בלבד. מומלץ לבחון כל מקרה לגופו עם איש מקצוע מוסמך לפני קבלת החלטות."
    pdf.cell(0, 5, txt=l1, ln=True, align='R')
    pdf.cell(0, 5, txt=l2, ln=True, align='R')
    
    return pdf.output()

# --- 4. ממשק ---
def main():
    st.set_page_config(page_title="מחשבון פרישה 2026", layout="wide")
    if not check_password(): st.stop()

    curr_yr = 2026
    with st.sidebar:
        agent_name = st.text_input("שם הסוכן", "יניב")
        client_name = st.text_input("שם הלקוח", "ישראל ישראלי")
        client_id = st.text_input("ת.ז לקוח", "")
        st.divider()
        total_grant = st.number_input("סך המענק ברוטו", value=500000)
        seniority = st.number_input("וותק בשנים", value=12.0)
        salary_for_exempt = st.number_input("שכר קובע", value=13750)
        exempt_val = min(total_grant, seniority * min(salary_for_exempt, 13750))
        taxable_val = total_grant - exempt_val
        st.divider()
        points = st.number_input("נקודות זיכוי", value=2.25)
        inc_now = st.number_input("הכנסה שנתית נוכחית", value=240000)
        inc_future_mo = st.number_input("הכנסה חודשית עתידית", value=7000)
        strategy = st.radio("סוג פריסה", ["פריסה קדימה", "פריסה אחורה"])
        num_years = st.slider("שנות פריסה", 1, 6, 6)

    tax_no_spread = calculate_tax_detailed(inc_now + taxable_val, points) - calculate_tax_detailed(inc_now, points)
    annual_part = taxable_val / num_years
    total_tax_spread, table_data = 0, []
    
    for i in range(num_years):
        y = curr_yr + i if strategy == "פריסה קדימה" else curr_yr - i
        inc = inc_now if y == curr_yr else inc_future_mo * 12
        t = calculate_tax_detailed(inc + annual_part, points) - calculate_tax_detailed(inc, points)
        total_tax_spread += t
        table_data.append({"שנה": str(y), "חלק המענק": fmt_num(annual_part), "הכנסה שנתית": fmt_num(inc), "מס": fmt_num(t), "נטו": fmt_num(annual_part - t)})

    savings = tax_no_spread - total_tax_spread
    net_total = total_grant - total_tax_spread

    st.markdown("<h1 style='text-align: right;'>📊 סימולטור פריסה מקצועי</h1>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ברוטו מענק", f"₪{fmt_num(total_grant)}")
    c2.metric("מס בפריסה", f"₪{fmt_num(total_tax_spread)}")
    c3.metric("נטו משוער", f"₪{fmt_num(net_total)}")
    c4.metric("חיסכון במס", f"₪{fmt_num(savings)}", delta=f"{fmt_num(savings)}")
    
    st.table(pd.DataFrame(table_data))

    if st.button("📄 הפק דוח PDF"):
        pdf_data = {
            'agent_name': agent_name, 'client_name': client_name, 'client_id': client_id, 
            'total_grant': total_grant, 'exempt': exempt_val, 'taxable': taxable_val, 
            'tax_with_spread': total_tax_spread, 'tax_no_spread': tax_no_spread, 
            'savings': savings, 'net_total': net_total
        }
        try:
            pdf_output = generate_pdf_report(pdf_data, table_data)
            st.download_button("📥 הורד דוח סופי", data=bytes(pdf_output), file_name=f"Tax_Plan_{client_name}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"שגיאה בהפקת ה-PDF: {e}")

if __name__ == "__main__":
    main()
