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

def hb(text):
    return str(text)[::-1] if text else ""

def fmt_num(num):
    return f"{float(num):,.0f}"

# --- 3. יצירת PDF (גרסת fpdf2 עם Unicode) ---
def generate_pdf_report(data_dict, table_rows):
    pdf = FPDF()
    pdf.add_page()
    
    # נתיב לפונטים (ודא שהם קיימים ב-GitHub באותיות קטנות)
    font_path = "arial.ttf"
    font_bold_path = "arialbd.ttf"

    if not os.path.exists(font_path):
        raise FileNotFoundError("קבצי הפונטים arial.ttf ו-arialbd.ttf חסרים בשרת!")

    pdf.add_font("ArialHeb", style="", fname=font_path)
    pdf.add_font("ArialHeb", style="B", fname=font_bold_path)
    pdf.set_font("ArialHeb", size=12)

    # תאריך (צד שמאל)
    pdf.set_font("ArialHeb", size=10)
    pdf.cell(0, 5, txt=f"{datetime.now().strftime('%d/%m/%Y')} :{hb('תאריך פלט')}", ln=True, align='L')
    
    # כותרת ראשית
    pdf.set_font("ArialHeb", style="B", size=22)
    pdf.set_text_color(0, 51, 102) 
    pdf.cell(0, 15, txt=hb("דוח סימולציה - אופטימיזציית פריסה"), ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("ArialHeb", size=12)
    pdf.cell(0, 8, txt=hb(f"לקוח: {data_dict['client_name']} | ת.ז: {data_dict['client_id']}"), ln=True, align='R')
    pdf.cell(0, 8, txt=hb(f"סוכן מטפל: {data_dict['agent_name']}"), ln=True, align='R')
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    # נתונים כספיים
    pdf.ln(5)
    pdf.cell(0, 9, txt=f"{hb('ש''ח')} {fmt_num(data_dict['total_grant'])} :{hb('מענק ברוטו')}", ln=True, align='R')
    pdf.cell(0, 9, txt=f"{hb('ש''ח')} {fmt_num(data_dict['exempt'])} :{hb('מתוכו פטור')}", ln=True, align='R')
    pdf.cell(0, 9, txt=f"{hb('ש''ח')} {fmt_num(data_dict['tax_with_spread'])} :{hb('סך המס לתשלום בפריסה')}", ln=True, align='R')
    
    pdf.ln(3)
    pdf.set_fill_color(230, 242, 255)
    pdf.set_font("ArialHeb", style="B", size=15)
    pdf.cell(0, 12, txt=f"{hb('ש''ח')} {fmt_num(data_dict['net_total'])} :{hb('נטו משוער ללקוח')}", ln=True, align='R', fill=True)
    
    pdf.ln(5)
    pdf.set_font("ArialHeb", size=13)
    pdf.set_text_color(0, 102, 0)
    pdf.cell(0, 10, txt=f"{hb('ש''ח')} {fmt_num(data_dict['savings'])} :{hb('חיסכון מס משוער בפריסה')}", ln=True, align='R')
    
    # טבלה
    pdf.ln(8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("ArialHeb", style="B", size=10)
    pdf.cell(35, 10, hb("נטו שנתית"), border=1, align='C')
    pdf.cell(35, 10, hb("מס שנתי"), border=1, align='C')
    pdf.cell(45, 10, hb("הכנסה שנתית"), border=1, align='C')
    pdf.cell(45, 10, hb("חלק מענק"), border=1, align='C')
    pdf.cell(20, 10, hb("שנה"), border=1, align='C')
    pdf.ln()
    
    pdf.set_font("ArialHeb", size=9)
    for row in table_rows:
        pdf.cell(35, 8, f"{hb(row['נטו'])}", border=1, align='C')
        pdf.cell(35, 8, f"{hb(row['מס'])}", border=1, align='C')
        pdf.cell(45, 8, f"{hb(row['הכנסה שנתית'])}", border=1, align='C')
        pdf.cell(45, 8, f"{hb(row['חלק המענק'])}", border=1, align='C')
        pdf.cell(20, 8, hb(row['שנה']), border=1, align='C')
        pdf.ln()

    # חתימות
    pdf.ln(15)
    pdf.cell(90, 10, hb("______________ :חתימת הלקוח"), align='R')
    pdf.cell(90, 10, hb("______________ :חתימת הסוכן"), align='R')

    # הבהרה משפטית
    pdf.set_y(-35)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("ArialHeb", size=8)
    l1 = "הבהרה משפטית: דוח זה מהווה סימולציה ראשונית בלבד ואינו מהווה ייעוץ מס או פנסיוני מחייב."
    l2 = "הנתונים הסופיים ייקבעו על ידי רשויות המס בלבד. מומלץ לבחון כל מקרה לגופו עם איש מקצוע מוסמך לפני קבלת החלטות."
    pdf.cell(0, 5, txt=hb(l1), ln=True, align='R')
    pdf.cell(0, 5, txt=hb(l2), ln=True, align='R')
    
    return pdf.output()

# --- 4. ממשק ---
def main():
    st.set_page_config(page_title="מחשבון פרישה 2026", layout="wide")
    if not check_password(): st.stop()

    curr_yr = 2026
    # ... (שאר ממשק המשתמש נשאר זהה לחישובים שלך)
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

    # לוגיקת חישוב
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
    
    # ... תצוגת המטריקות והטבלה ...
    st.table(pd.DataFrame(table_data))

    if st.button("📄 הפק דוח PDF"):
        pdf_data = {
            'agent_name': agent_name, 'client_name': client_name, 'client_id': client_id, 
            'total_grant': total_grant, 'exempt': exempt_val, 'taxable': taxable_val, 
            'tax_with_spread': total_tax_spread, 'tax_no_spread': tax_no_spread, 
            'savings': savings, 'net_total': net_total
        }
        try:
            pdf_bytes = generate_pdf_report(pdf_data, table_data)
            st.download_button("📥 הורד דוח סופי", data=bytes(pdf_bytes), file_name=f"Tax_Plan_{client_name}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"שגיאה בהפקת ה-PDF: {e}")

if __name__ == "__main__":
    main()
