import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
from datetime import datetime, date

# --- 1. מנגנון אבטחה ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True

    st.markdown("<h2 style='text-align: right;'>כניסה למערכת מוגנת</h2>", unsafe_allow_html=True)
    password = st.text_input("הזן קוד גישה", type="password")
    if st.button("התחבר"):
        if password == "1234": # שנה כאן את הסיסמה שלך
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("קוד שגוי")
    return False

# --- 2. מנוע חישוב מס 2026 ---
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
    if not text: return ""
    return str(text)[::-1]

def fmt_num(num):
    return f"{float(num):,.0f}"

# --- 3. יצירת PDF מקצועי ---
def generate_pdf_report(data_dict):
    pdf = FPDF()
    pdf.add_page()
    font_reg, font_bold = "arial.ttf", "arialbd.ttf"
    
    if os.path.exists(font_reg) and os.path.exists(font_bold):
        pdf.add_font("ArialHeb", style="", fname=font_reg)
        pdf.add_font("ArialHeb", style="B", fname=font_bold)
        pdf.set_font("ArialHeb", size=10)
    else:
        pdf.set_font("Helvetica", size=10)

    # כותרת
    pdf.cell(0, 5, txt=f"{datetime.now().strftime('%d/%m/%Y')} :{hb('תאריך פלט')}", ln=True, align='L')
    if os.path.exists(font_bold): pdf.set_font("ArialHeb", style="B", size=22)
    pdf.set_text_color(0, 51, 102) # כחול כהה מקצועי
    pdf.cell(0, 15, txt=hb("דוח סימולציה - אופטימיזציית פריסה"), ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    
    pdf.ln(5)
    if os.path.exists(font_reg): pdf.set_font("ArialHeb", size=12)
    pdf.cell(0, 8, txt=hb(f"לקוח: {data_dict['client_name']} | ת.ז: {data_dict['client_id']}"), ln=True, align='R')
    pdf.cell(0, 8, txt=hb(f"סוכן מטפל: {data_dict['agent_name']}"), ln=True, align='R')
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # נתונים כספיים
    pdf.cell(0, 9, txt=f"{hb('ש''ח')} {fmt_num(data_dict['total_grant'])} :{hb('מענק ברוטו')}", ln=True, align='R')
    pdf.cell(0, 9, txt=f"{hb('ש''ח')} {fmt_num(data_dict['exempt'])} :{hb('מתוכו פטור')}", ln=True, align='R')
    pdf.cell(0, 9, txt=f"{hb('ש''ח')} {fmt_num(data_dict['taxable'])} :{hb('מתוכו חייב במס')}", ln=True, align='R')
    pdf.ln(5)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, txt=f"{hb('ש''ח')} {fmt_num(data_dict['tax_no_spread'])} :{hb('מס משוער ללא פריסה')}", ln=True, align='R', fill=True)
    
    if os.path.exists(font_bold): pdf.set_font("ArialHeb", style="B", size=16)
    pdf.set_text_color(0, 102, 0)
    pdf.cell(0, 12, txt=f"{hb('ש''ח')} {fmt_num(data_dict['savings'])} :{hb('חיסכון מס משוער בפריסה')}", ln=True, align='R')
    pdf.set_text_color(0, 0, 0)

    # טבלה
    pdf.ln(5)
    if os.path.exists(font_bold): pdf.set_font("ArialHeb", style="B", size=11)
    pdf.cell(45, 10, hb("מס שנתי"), border=1, align='C')
    pdf.cell(45, 10, hb("הכנסה שנתית"), border=1, align='C')
    pdf.cell(45, 10, hb("חלק מענק"), border=1, align='C')
    pdf.cell(25, 10, hb("שנה"), border=1, align='C')
    pdf.ln()
    
    if os.path.exists(font_reg): pdf.set_font("ArialHeb", size=10)
    for row in data_dict['table']:
        pdf.cell(45, 8, f"{hb('ש''ח')} {row['מס']}", border=1, align='C')
        pdf.cell(45, 8, f"{hb('ש''ח')} {row['הכנסה שנתית']}", border=1, align='C')
        pdf.cell(45, 8, f"{hb('ש''ח')} {row['חלק המענק']}", border=1, align='C')
        pdf.cell(25, 8, hb(row['שנה']), border=1, align='C')
        pdf.ln()

    # --- חתימות ---
    pdf.ln(15)
    pdf.cell(90, 10, hb("______________ :חתימת הסוכן"), align='R')
    pdf.cell(90, 10, hb("______________ :חתימת הלקוח"), align='R')

    # --- הבהרה משפטית מתוקנת ---
    pdf.set_y(-35)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("ArialHeb", size=8)
    
    # הנוסח שביקשת
    line1 = "הבהרה משפטית: דוח זה מהווה סימולציה ראשונית בלבד ואינו מהווה ייעוץ מס או פנסיוני מחייב."
    line2 = "הנתונים הסופיים ייקבעו על ידי רשויות המס בלבד. מומלץ לבחון כל מקרה לגופו עם איש מקצוע מוסמך לפני קבלת החלטות."
    
    pdf.cell(0, 5, txt=hb(line1), ln=True, align='R')
    pdf.cell(0, 5, txt=hb(line2), ln=True, align='R')
    
    return bytes(pdf.output())

# --- 4. ממשק המערכת ---
def main():
    st.set_page_config(page_title="סימולטור פריסה 2026", layout="wide")
    
    if not check_password():
        st.stop()

    st.markdown("<h1 style='text-align: right;'>📊 סימולטור פריסה מקצועי</h1>", unsafe_allow_html=True)
    
    curr_yr = 2026

    with st.sidebar:
        st.header("👤 פרטי התקשרות")
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
        table_data.append({"שנה": str(y), "חלק המענק": fmt_num(annual_part), "הכנסה שנתית": fmt_num(inc), "מס": fmt_num(t)})

    savings = tax_no_spread - total_tax_spread

    # תצוגת תוצאות
    c1, c2, c3 = st.columns(3)
    c1.metric("מס ללא פריסה", f"₪{fmt_num(tax_no_spread)}")
    c2.metric("מס בפריסה", f"₪{fmt_num(total_tax_spread)}")
    c3.metric("חיסכון במס", f"₪{fmt_num(savings)}", delta=f"{fmt_num(savings)}")
    
    st.divider()
    st.table(pd.DataFrame(table_data))

    if st.button("📄 הפק דוח PDF"):
        pdf_data = {
            'agent_name': agent_name, 'client_name': client_name, 'client_id': client_id, 
            'total_grant': total_grant, 'exempt': exempt_val, 'taxable': taxable_val, 
            'tax_no_spread': tax_no_spread, 'savings': savings, 'table': table_data
        }
        pdf_bytes = generate_pdf_report(pdf_data)
        st.download_button("📥 הורד דוח סופי", data=pdf_bytes, file_name=f"Tax_Plan_{client_name}.pdf")

if __name__ == "__main__":
    main()
