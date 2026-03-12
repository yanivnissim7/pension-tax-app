import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
from datetime import datetime

# --- 1. אבטחה וכניסה ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    
    st.markdown("<h2 style='text-align: right;'>כניסה למערכת סימולציה פנסיונית</h2>", unsafe_allow_html=True)
    password = st.text_input("הזן קוד גישה", type="password")
    if st.button("התחבר"):
        if password == "1234": # ניתן לשינוי לקוד שלך
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("קוד שגוי - נא לנסות שוב")
    return False

# --- 2. לוגיקת חישוב מס (כולל מס יסף ונקודות זיכוי) ---
def calculate_tax_detailed(annual_income, points=2.25):
    # מדרגות מס הכנסה לשנת 2026 (משוער)
    brackets = [
        (84120, 0.10), 
        (120720, 0.14), 
        (193800, 0.20), 
        (269280, 0.31), 
        (560280, 0.35), 
        (721560, 0.47), 
        (float('inf'), 0.50)
    ]
    tax, prev_limit = 0, 0
    for limit, rate in brackets:
        if annual_income > limit:
            tax += (limit - prev_limit) * rate
            prev_limit = limit
        else:
            tax += (annual_income - prev_limit) * rate
            break
            
    # מס יסף (3% מעל תקרת הכנסה)
    surtax = max(0, (annual_income - 721560) * 0.03)
    # זיכוי נקודות (שווי נקודה משוער 2026: 242 ש"ח לחודש = 2904 ש"ח לשנה)
    total_tax = max(0, (tax + surtax) - (points * 2904))
    return total_tax

def fmt_num(num):
    return f"{float(num):,.0f}"

# --- 3. יצירת דוח PDF מקצועי (fpdf2 Unicode) ---
def generate_pdf_report(data_dict, table_rows):
    pdf = FPDF()
    pdf.add_page()
    
    # טעינת פונטים
    font_path = "arial.ttf"
    font_bold_path = "arialbd.ttf"
    if not os.path.exists(font_path):
        raise FileNotFoundError("יש לוודא שקבצי הפונטים נמצאים בתיקייה הראשית.")

    pdf.add_font("ArialHeb", style="", fname=font_path)
    pdf.add_font("ArialHeb", style="B", fname=font_bold_path)
    
    # כותרת ותאריך
    pdf.set_font("ArialHeb", size=10)
    pdf.cell(0, 5, txt=f"תאריך הפקה: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='L')
    
    pdf.set_font("ArialHeb", style="B", size=22)
    pdf.set_text_color(0, 51, 102) 
    pdf.cell(0, 15, txt="סימולציית נטו - אופטימיזציית פריסת מס", ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("ArialHeb", size=12)
    pdf.cell(0, 8, txt=f"לקוח: {data_dict['client_name']} | ת.ז: {data_dict['client_id']}", ln=True, align='R')
    pdf.cell(0, 8, txt=f"סוכן מטפל: {data_dict['agent_name']}", ln=True, align='R')
    pdf.line(10, pdf.get_y()+2, 200, pdf.get_y()+2)
    
    # ניתוח המענק
    pdf.ln(10)
    pdf.set_font("ArialHeb", style="B", size=14)
    pdf.cell(0, 10, txt="ניתוח מענקי פרישה:", ln=True, align='R')
    pdf.set_font("ArialHeb", size=12)
    pdf.cell(0, 8, txt=f"סך מענק ברוטו: {fmt_num(data_dict['total_grant'])} ש''ח", ln=True, align='R')
    pdf.cell(0, 8, txt=f"חלק פטור (סעיף 9(7א)): {fmt_num(data_dict['exempt'])} ש''ח", ln=True, align='R')
    pdf.cell(0, 8, txt=f"חלק חייב במס לפריסה: {fmt_num(data_dict['taxable'])} ש''ח", ln=True, align='R')

    # השוואת נטו
    pdf.ln(5)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, txt=f"מס ללא פריסה (תשלום מיידי): {fmt_num(data_dict['tax_no_spread'])} ש''ח", ln=True, align='R', fill=True)
    pdf.cell(0, 10, txt=f"מס משוער בפריסה אופטימלית: {fmt_num(data_dict['tax_with_spread'])} ש''ח", ln=True, align='R')
    
    # שורת הרווח
    pdf.ln(5)
    pdf.set_fill_color(200, 255, 200)
    pdf.set_font("ArialHeb", style="B", size=16)
    pdf.set_text_color(0, 80, 0)
    pdf.cell(0, 15, txt=f"נטו סופי ללקוח: {fmt_num(data_dict['net_total'])} ש''ח", ln=True, align='R', fill=True)
    pdf.set_font("ArialHeb", style="B", size=13)
    pdf.cell(0, 10, txt=f"חיסכון מס (תוספת נטו לכיס): {fmt_num(data_dict['savings'])} ש''ח", ln=True, align='R')

    # טבלת פריסה שנתית
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("ArialHeb", style="B", size=10)
    pdf.set_fill_color(230, 240, 255)
    pdf.cell(35, 10, "נטו שנתי", border=1, align='C', fill=True)
    pdf.cell(35, 10, "מס", border=1, align='C', fill=True)
    pdf.cell(45, 10, "הכנסה כוללת", border=1, align='C', fill=True)
    pdf.cell(45, 10, "חלק המענק", border=1, align='C', fill=True)
    pdf.cell(20, 10, "שנה", border=1, align='C', fill=True)
    pdf.ln()
    
    pdf.set_font("ArialHeb", size=10)
    for row in table_rows:
        pdf.cell(35, 8, f"{row['נטו']}", border=1, align='C')
        pdf.cell(35, 8, f"{row['מס']}", border=1, align='C')
        pdf.cell(45, 8, f"{row['הכנסה שנתית']}", border=1, align='C')
        pdf.cell(45, 8, f"{row['חלק המענק']}", border=1, align='C')
        pdf.cell(20, 8, str(row['שנה']), border=1, align='C')
        pdf.ln()

    # הבהרה משפטית
    pdf.set_y(-30)
    pdf.set_font("ArialHeb", size=8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, txt="דוח זה הינו סימולציה בלבד המבוססת על נתוני הלקוח. הנתונים הסופיים ייקבעו ע''י רשויות המס.", ln=True, align='C')
    
    return pdf.output()

# --- 4. הממשק הראשי ---
def main():
    st.set_page_config(page_title="סימולטור פריסה 2026", layout="wide")
    if not check_password(): st.stop()

    curr_yr = 2026
    
    with st.sidebar:
        st.header("📋 פרטי לקוח וסוכן")
        agent_name = st.text_input("שם הסוכן", "יניב")
        client_name = st.text_input("שם הלקוח", "ישראל ישראלי")
        client_id = st.text_input("ת.ז לקוח", "")
        st.divider()
        st.header("💰 נתוני המענק")
        total_grant = st.number_input("סך מענק פרישה (ברוטו)", value=500000, step=1000)
        seniority = st.number_input("שנות וותק", value=12.0, step=0.5)
        salary_for_exempt = st.number_input("שכר קובע לפטור", value=13750)
        exempt_val = min(total_grant, seniority * min(salary_for_exempt, 13750))
        taxable_val = total_grant - exempt_val
        st.info(f"חלק פטור: ₪{fmt_num(exempt_val)} | חייב: ₪{fmt_num(taxable_val)}")
        st.divider()
        st.header("📈 נתוני הכנסה ופריסה")
        points = st.number_input("נקודות זיכוי", value=2.25)
        inc_now = st.number_input("הכנסה שנתית נוכחית (חייבת)", value=240000)
        inc_future_mo = st.number_input("הכנסה חודשית עתידית (צפויה)", value=7000)
        strategy = st.radio("אסטרטגיית פריסה", ["פריסה קדימה", "פריסה אחורה"])
        num_years = st.slider("מספר שנות פריסה", 1, 6, 6)

    # חישוב מס ללא פריסה (כדי להראות חיסכון)
    tax_no_spread = calculate_tax_detailed(inc_now + taxable_val, points) - calculate_tax_detailed(inc_now, points)
    
    # חישוב פריסה שנתית
    annual_part = taxable_val / num_years
    total_tax_spread, table_data = 0, []
    
    for i in range(num_years):
        y = curr_yr + i if strategy == "פריסה קדימה" else curr_yr - i
        # בשנה הראשונה משתמשים בהכנסה נוכחית, בשאר בעתידית
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

    # תצוגה במסך
    st.markdown(f"<h1 style='text-align: right;'>דוח אופטימיזציה עבור {client_name}</h1>", unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("ברוטו כולל", f"₪{fmt_num(total_grant)}")
    m2.metric("מס בפריסה", f"₪{fmt_num(total_tax_spread)}", delta=f"-₪{fmt_num(savings)}", delta_color="normal")
    m3.metric("נטו סופי ללקוח", f"₪{fmt_num(net_total)}")
    m4.metric("חיסכון במס", f"₪{fmt_num(savings)}")

    st.subheader("פירוט פריסה שנתית")
    st.table(pd.DataFrame(table_data))

    if st.button("📄 הפק דוח PDF מיידי ללקוח"):
        pdf_data = {
            'agent_name': agent_name, 'client_name': client_name, 'client_id': client_id,
            'total_grant': total_grant, 'exempt': exempt_val, 'taxable': taxable_val,
            'tax_with_spread': total_tax_spread, 'tax_no_spread': tax_no_spread,
            'savings': savings, 'net_total': net_total
        }
        try:
            pdf_bytes = generate_pdf_report(pdf_data, table_data)
            st.download_button(
                label="📥 הורד דוח PDF",
                data=bytes(pdf_bytes),
                file_name=f"סימולציה_{client_name}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"שגיאה בהפקת הדוח: {e}")

if __name__ == "__main__":
    main()
