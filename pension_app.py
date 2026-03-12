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

def hb(text): return str(text)[::-1] if text else ""
def fmt_num(num): return f"{float(num):,.0f}"

# --- 3. לוגיקת פריסה גנרית ---
def run_spread_calc(start_year, num_years, taxable_val, inc_now, inc_future_mo, points):
    annual_part = taxable_val / num_years
    total_tax = 0
    details = []
    actual_start_year = 2026 
    
    for i in range(num_years):
        year = start_year + i
        annual_inc = inc_now if year == actual_start_year else inc_future_mo * 12
        
        tax_on_income = calculate_tax_detailed(annual_inc, points)
        tax_with_grant = calculate_tax_detailed(annual_inc + annual_part, points)
        annual_tax = tax_with_grant - tax_on_income
        
        total_tax += annual_tax
        details.append({
            "שנה": str(year),
            "חלק המענק": fmt_num(annual_part),
            "הכנסה שנתית": fmt_num(annual_inc + annual_part),
            "מס": fmt_num(annual_tax)
        })
    return total_tax, details

# --- 4. יצירת דוח PDF (תיקון שגיאת Space ורינדור הערות) ---
def generate_pdf_report(data_dict):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("ArialHeb", style="", fname="arial.ttf")
    pdf.add_font("ArialHeb", style="B", fname="arialbd.ttf")
    pdf.set_font("ArialHeb", size=10)

    # תאריך פלט
    today_str = datetime.now().strftime('%d/%m/%Y')
    pdf.cell(190, 5, txt=f"{today_str} :{hb('תאריך פלט')}", ln=True, align='L')
    
    pdf.set_font("ArialHeb", style="B", size=20)
    pdf.cell(190, 15, txt=hb("דוח אופטימיזציית פריסת מענקים"), ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_font("ArialHeb", size=12)
    pdf.cell(190, 7, txt=hb(f"לקוח: {data_dict['client_name']} | ת.ז: {data_dict['client_id']}"), ln=True, align='R')
    pdf.cell(190, 7, txt=f"{data_dict['ret_date']} :{hb('תאריך פרישה')}", ln=True, align='R')
    
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # נתונים כספיים
    pdf.set_font("ArialHeb", size=11)
    pdf.cell(190, 8, txt=f"{hb('שח')} {fmt_num(data_dict['total_grant'])} :{hb('מענק ברוטו כולל')}", ln=True, align='R')
    pdf.set_text_color(0, 100, 0)
    pdf.cell(190, 8, txt=f"{hb('שח')} {fmt_num(data_dict['exempt'])} :{hb('מענק פטור ממס')}", ln=True, align='R')
    pdf.set_text_color(150, 0, 0)
    pdf.cell(190, 8, txt=f"{hb('שח')} {fmt_num(data_dict['taxable'])} :{hb('מענק חייב במס (לפריסה)')}", ln=True, align='R')
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 8, txt=f"{hb('שח')} {fmt_num(data_dict['savings'])} :{hb('חיסכון מס משוער בפריסה')}", ln=True, align='R')
    
    # שורת הנטו
    pdf.ln(4)
    pdf.set_fill_color(220, 255, 220)
    pdf.set_font("ArialHeb", style="B", size=14)
    net_total = data_dict['total_grant'] - data_dict['tax_with_spread']
    pdf.cell(190, 12, txt=f"{hb('שח')} {fmt_num(net_total)} :{hb('נטו משוער ללקוח לאחר פריסה')}", ln=True, align='R', fill=True)

    # טבלת פירוט
    pdf.ln(10)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("ArialHeb", style="B", size=10)
    # מרכז את הטבלה ידנית מעט
    pdf.set_x(20)
    pdf.cell(45, 10, hb("מס שנתי"), border=1, align='C', fill=True)
    pdf.cell(45, 10, hb("הכנסה כוללת"), border=1, align='C', fill=True)
    pdf.cell(45, 10, hb("חלק מענק"), border=1, align='C', fill=True)
    pdf.cell(25, 10, hb("שנה"), border=1, align='C', fill=True)
    pdf.ln()
    
    pdf.set_font("ArialHeb", size=10)
    for row in data_dict['table']:
        pdf.set_x(20)
        pdf.cell(45, 8, f"{row['מס']}", border=1, align='C')
        pdf.cell(45, 8, f"{row['הכנסה שנתית']}", border=1, align='C')
        pdf.cell(45, 8, f"{row['חלק המענק']}", border=1, align='C')
        pdf.cell(25, 8, row['שנה'], border=1, align='C')
        pdf.ln()

    # הערה משפטית - שימוש ברוחב קבוע למניעת השגיאה
    pdf.set_y(-45)
    pdf.set_x(10)
    pdf.set_font("ArialHeb", size=8)
    disclaimer_main = "הבהרה: דוח זה מהווה סימולציה ראשונית בלבד ואינו מהווה ייעוץ מס מחייב. הנתונים הסופיים ייקבעו על ידי רשויות המס."
    disclaimer_extra = "החישוב יוצא מתוך הנחה שההכנסה היחידה בשנות הפריסה היא הקצבה שהוזנה. במידה ותהיה הכנסה נוספת (משכורת, עסק וכיו''ב), חבות המס השנתית תגדל בהתאם."
    
    pdf.multi_cell(190, 5, txt=hb(disclaimer_main), align='R')
    pdf.multi_cell(190, 5, txt=hb(disclaimer_extra), align='R')

    return bytes(pdf.output())

# --- 5. ממשק המשתמש ---
def main():
    st.set_page_config(page_title="מחשבון פרישה מקצועי", layout="wide")
    if not check_password(): st.stop()

    st.markdown("<h1 style='text-align: right;'>📊 סימולטור פריסה והשוואת כדאיות</h1>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("פרטי פרישה")
        agent_name = st.text_input("שם הסוכן", "יניב")
        client_name = st.text_input("שם הלקוח", "ישראל ישראלי")
        client_id = st.text_input("ת.ז לקוח", "")
        ret_date = st.date_input("תאריך סיום העסקה", value=date(2026, 10, 1))
        
        st.divider()
        total_grant = st.number_input("סך המענק ברוטו", value=500000)
        seniority = st.number_input("שנות וותק", value=12.0)
        salary_for_exempt = st.number_input("שכר קובע", value=13750)
        
        exempt_val = min(total_grant, seniority * min(salary_for_exempt, 13750))
        taxable_val = total_grant - exempt_val
        
        st.divider()
        points = st.number_input("נקודות זיכוי", value=2.25)
        inc_now = st.number_input("הכנסה שנתית ב-2026 (ברוטו)", value=240000)
        inc_future_mo = st.number_input("הכנסה חודשית עתידית צפויה", value=7000)
        num_years = st.slider("שנות פריסה", 1, 6, 6)

    this_year = 2026
    tax_now, table_now = run_spread_calc(this_year, num_years, taxable_val, inc_now, inc_future_mo, points)
    tax_next, table_next = run_spread_calc(this_year + 1, num_years, taxable_val, inc_now, inc_future_mo, points)
    
    tax_no_spread = (calculate_tax_detailed(inc_now + taxable_val, points) - calculate_tax_detailed(inc_now, points))
    
    diff = tax_now - tax_next
    if diff > 100:
        st.success(f"💡 המלצה מקצועית: עדיף להתחיל פריסה מ-{this_year + 1}. חיסכון נוסף של ₪{fmt_num(diff)}")
        start_choice = st.radio("בחר שנת התחלה:", [this_year, this_year + 1], index=1)
    else:
        st.info(f"💡 המלצה מקצועית: התחלה מ-{this_year} היא המשתלמת ביותר.")
        start_choice = st.radio("בחר שנת התחלה:", [this_year, this_year + 1], index=0)

    final_tax, final_table = (tax_now, table_now) if start_choice == this_year else (tax_next, table_next)
    savings = tax_no_spread - final_tax
    net_total = total_grant - final_tax

    c1, c2, c3 = st.columns(3)
    c1.metric("נטו סופי ללקוח", f"₪{fmt_num(net_total)}")
    c2.metric("חיסכון מס בפריסה", f"₪{fmt_num(savings)}")
    c3.metric("סה''כ מס לתשלום", f"₪{fmt_num(final_tax)}")
    
    st.table(pd.DataFrame(final_table))

    if st.button("📄 הפק דוח PDF"):
        pdf_data = {
            'agent_name': agent_name, 'client_name': client_name, 'client_id': client_id, 
            'ret_date': ret_date.strftime('%d/%m/%Y'), 'total_grant': total_grant, 
            'exempt': exempt_val, 'taxable': taxable_val,
            'tax_with_spread': final_tax, 'savings': savings, 'table': final_table
        }
        try:
            pdf_bytes = generate_pdf_report(pdf_data)
            st.download_button(label="📥 הורד PDF סופי", data=pdf_bytes, file_name=f"Tax_Report_{client_name}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"שגיאה בהפקה: {e}")

if __name__ == "__main__":
    main()
