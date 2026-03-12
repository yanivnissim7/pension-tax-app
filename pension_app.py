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
        if password == "1234":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("קוד שגוי. הגישה חסומה.")
    return False

# --- 2. מנוע חישוב מס ---
def calculate_tax_detailed(annual_income, points=2.25):
    # מדרגות מס 2026 (משוערך)
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

# פונקציות עזר לעברית ועיצוב
def hb(text): 
    return str(text)[::-1] if text else ""

def fmt_num(num): 
    return f"{float(num):,.0f}"

# --- 3. יצירת דוח PDF ---
def generate_pdf_report(data_dict):
    # יצירת אובייקט PDF (תומך fpdf2)
    pdf = FPDF()
    pdf.add_page()
    
    font_reg = "arial.ttf"
    font_bold = "arialbd.ttf"
    
    # טעינת פונטים (חובה לוודא שהם ב-GitHub באותיות קטנות)
    pdf.add_font("ArialHeb", style="", fname=font_reg)
    pdf.add_font("ArialHeb", style="B", fname=font_bold)
    pdf.set_font("ArialHeb", size=10)

    # כותרת ותאריך
    pdf.cell(0, 5, txt=f"{datetime.now().strftime('%d/%m/%Y')} :{hb('תאריך פלט')}", ln=True, align='L')
    pdf.set_font("ArialHeb", style="B", size=20)
    pdf.cell(0, 15, txt=hb("דוח אופטימיזציית פריסת מענקים"), ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_font("ArialHeb", size=12)
    pdf.cell(0, 7, txt=hb(f"לקוח: {data_dict['client_name']} | ת.ז: {data_dict['client_id']}"), ln=True, align='R')
    pdf.cell(0, 7, txt=hb(f"סוכן מטפל: {data_dict['agent_name']}"), ln=True, align='R')
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # נתונים כספיים
    pdf.set_font("ArialHeb", size=12)
    pdf.cell(0, 9, txt=f"{hb('שח')} {fmt_num(data_dict['total_grant'])} :{hb('מענק ברוטו כולל')}", ln=True, align='R')
    pdf.cell(0, 9, txt=f"{hb('שח')} {fmt_num(data_dict['exempt'])} :{hb('מתוכו פטור ממס')}", ln=True, align='R')
    pdf.cell(0, 9, txt=f"{hb('שח')} {fmt_num(data_dict['savings'])} :{hb('חיסכון מס משוער בפריסה')}", ln=True, align='R')
    
    # שורת הנטו המודגשת
    pdf.ln(3)
    pdf.set_fill_color(220, 255, 220) # רקע ירוק עדין
    pdf.set_font("ArialHeb", style="B", size=14)
    net_total = data_dict['total_grant'] - data_dict['tax_with_spread']
    pdf.cell(0, 12, txt=f"{hb('שח')} {fmt_num(net_total)} :{hb('נטו משוער ללקוח לאחר פריסה')}", ln=True, align='R', fill=True)
    pdf.set_font("ArialHeb", size=10)

    # טבלת פריסה
    pdf.ln(10)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("ArialHeb", style="B", size=10)
    pdf.cell(45, 10, hb("מס שנתי"), border=1, align='C', fill=True)
    pdf.cell(45, 10, hb("הכנסה כוללת"), border=1, align='C', fill=True)
    pdf.cell(45, 10, hb("חלק מענק"), border=1, align='C', fill=True)
    pdf.cell(25, 10, hb("שנה"), border=1, align='C', fill=True)
    pdf.ln()
    
    pdf.set_font("ArialHeb", size=10)
    for row in data_dict['table']:
        pdf.cell(45, 8, f"{row['מס']}", border=1, align='C')
        pdf.cell(45, 8, f"{row['הכנסה שנתית']}", border=1, align='C')
        pdf.cell(45, 8, f"{row['חלק המענק']}", border=1, align='C')
        pdf.cell(25, 8, hb(row['שנה']), border=1, align='C')
        pdf.ln()

    # חתימות
    pdf.ln(15)
    pdf.set_font("ArialHeb", size=11)
    pdf.cell(90, 10, hb("________________ :חתימת הלקוח"), align='R')
    pdf.cell(90, 10, hb("________________ :חתימת הסוכן"), align='R')

    # הערה משפטית בתחתית
    pdf.set_y(-30)
    pdf.set_font("ArialHeb", size=8)
    disclaimer = "הבהרה: דוח זה מהווה סימולציה ראשונית בלבד ואינו מהווה ייעוץ מס מחייב. הנתונים הסופיים ייקבעו על ידי רשויות המס."
    pdf.multi_cell(0, 5, txt=hb(disclaimer), align='R')
    
    # התיקון הקריטי: המרה מ-bytearray ל-bytes עבור Streamlit
    return bytes(pdf.output())

# --- 4. ממשק המשתמש (Streamlit) ---
def main():
    st.set_page_config(page_title="מחשבון פריסה 2026", layout="wide")
    
    if not check_password():
        st.stop()

    st.markdown("<h1 style='text-align: right;'>📊 סימולטור פריסה מקצועי</h1>", unsafe_allow_html=True)
    
    # סרגל צד - קלט נתונים
    with st.sidebar:
        st.header("פרטי דוח")
        agent_name = st.text_input("שם הסוכן", "יניב")
        client_name = st.text_input("שם הלקוח", "ישראל ישראלי")
        client_id = st.text_input("ת.ז לקוח", "")
        st.divider()
        total_grant = st.number_input("סך המענק ברוטו", value=500000)
        seniority = st.number_input("שנות וותק", value=12.0)
        salary_for_exempt = st.number_input("שכר קובע", value=13750)
        
        # חישוב פטור (תקרת פיצויים 2026)
        exempt_val = min(total_grant, seniority * min(salary_for_exempt, 13750))
        taxable_val = total_grant - exempt_val
        
        st.divider()
        points = st.number_input("נקודות זיכוי", value=2.25)
        inc_now = st.number_input("הכנסה שנתית (שנת פרישה)", value=240000)
        inc_future_mo = st.number_input("הכנסה חודשית עתידית צפויה", value=7000)
        strategy = st.radio("כיוון פריסה", ["פריסה קדימה", "פריסה אחורה"])
        num_years = st.slider("מספר שנות פריסה", 1, 6, 6)

    # לוגיקת חישוב
    tax_no_spread = calculate_tax_detailed(inc_now + taxable_val, points) - calculate_tax_detailed(inc_now, points)
    annual_part = taxable_val / num_years
    total_tax_spread, table_data = 0, []
    
    current_year = 2026
    for i in range(num_years):
        year = current_year + i if strategy == "פריסה קדימה" else current_year - i
        annual_inc = inc_now if year == current_year else inc_future_mo * 12
        
        tax_on_income_only = calculate_tax_detailed(annual_inc, points)
        tax_with_grant = calculate_tax_detailed(annual_inc + annual_part, points)
        annual_tax = tax_with_grant - tax_on_income_only
        
        total_tax_spread += annual_tax
        table_data.append({
            "שנה": str(year), 
            "חלק המענק": fmt_num(annual_part), 
            "הכנסה שנתית": fmt_num(annual_inc + annual_part), 
            "מס": fmt_num(annual_tax)
        })

    savings = tax_no_spread - total_tax_spread
    net_total = total_grant - total_tax_spread

    # תצוגה במסך
    c1, c2, c3 = st.columns(3)
    c1.metric("נטו סופי (בפריסה)", f"₪{fmt_num(net_total)}")
    c2.metric("חיסכון במס", f"₪{fmt_num(savings)}")
    c3.metric("סה''כ מס בפריסה", f"₪{fmt_num(total_tax_spread)}")
    
    st.markdown("### פירוט פריסת המס")
    st.table(pd.DataFrame(table_data))

    # כפתור הפקת PDF
    if st.button("📄 הפק דוח PDF"):
        pdf_data = {
            'agent_name': agent_name, 'client_name': client_name, 'client_id': client_id, 
            'total_grant': total_grant, 'exempt': exempt_val, 'taxable': taxable_val, 
            'tax_no_spread': tax_no_spread, 'tax_with_spread': total_tax_spread,
            'savings': savings, 'table': table_data
        }
        try:
            # הפקת ה-bytes מהפונקציה
            pdf_bytes = generate_pdf_report(pdf_data)
            
            # הורדה ב-Streamlit
            st.download_button(
                label="📥 הורד דוח PDF חתום",
                data=pdf_bytes,
                file_name=f"Tax_Report_{client_name}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"שגיאה בהפקת הקובץ: {e}")

if __name__ == "__main__":
    main()
