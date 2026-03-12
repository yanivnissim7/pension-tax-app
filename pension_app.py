import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
from datetime import datetime, date

# פונקציית עזר להיפוך טקסט
def hb(text): 
    return str(text)[::-1] if text else ""

def fmt_num(num): 
    return f"{float(num):,.0f}"

def generate_pdf_report(data_dict):
    # שימוש ב-fpdf2 תומך יוניקוד
    pdf = FPDF()
    pdf.add_page()
    
    font_reg = "arial.ttf"
    font_bold = "arialbd.ttf"
    
    # בדיקה אם הקבצים פיזית קיימים
    if not os.path.exists(font_reg):
        st.error(f"קובץ הפונט {font_reg} לא נמצא בתיקייה! וודא שהעלית אותו ל-GitHub.")
        st.stop()

    # טעינת הפונטים - חובה עבור עברית
    pdf.add_font("ArialHeb", style="", fname=font_reg)
    pdf.add_font("ArialHeb", style="B", fname=font_bold)
    pdf.set_font("ArialHeb", size=10)

    # כותרת (שימוש ב-hb להיפוך)
    pdf.cell(0, 5, txt=f"{datetime.now().strftime('%d/%m/%Y')} :{hb('תאריך פלט')}", ln=True, align='L')
    pdf.set_font("ArialHeb", style="B", size=20)
    pdf.cell(0, 15, txt=hb("דוח אופטימיזציית פריסה"), ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_font("ArialHeb", size=12)
    pdf.cell(0, 7, txt=hb(f"לקוח: {data_dict['client_name']} | ת.ז: {data_dict['client_id']}"), ln=True, align='R')
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    # תוצאות כספיות (החלפתי את המירכאות במילה 'שח' כדי למנוע תקלות קידוד)
    pdf.ln(5)
    pdf.cell(0, 9, txt=f"{hb('שח')} {fmt_num(data_dict['total_grant'])} :{hb('מענק ברוטו')}", ln=True, align='R')
    pdf.cell(0, 9, txt=f"{hb('שח')} {fmt_num(data_dict['savings'])} :{hb('חיסכון מס משוער')}", ln=True, align='R')

    # טבלה
    pdf.ln(10)
    pdf.set_font("ArialHeb", style="B", size=10)
    pdf.cell(45, 10, hb("מס שנתי"), border=1, align='C')
    pdf.cell(45, 10, hb("הכנסה"), border=1, align='C')
    pdf.cell(25, 10, hb("שנה"), border=1, align='C')
    pdf.ln()
    
    pdf.set_font("ArialHeb", size=10)
    for row in data_dict['table']:
        pdf.cell(45, 8, f"{row['מס']}", border=1, align='C')
        pdf.cell(45, 8, f"{row['הכנסה שנתית']}", border=1, align='C')
        pdf.cell(25, 8, hb(row['שנה']), border=1, align='C')
        pdf.ln()
    
    # הבהרה משפטית
    pdf.set_y(-30)
    pdf.set_font("ArialHeb", size=8)
    disclaimer = "הבהרה: סימולציה זו אינה מהווה ייעוץ מס מחייב. הנתונים בכפוף לאישור רשויות המס."
    pdf.multi_cell(0, 5, txt=hb(disclaimer), align='R')
    
    # חשוב: פלט בפורמט bytes עבור Streamlit
    return pdf.output()

# --- ממשק האפליקציה ---
def main():
    st.set_page_config(page_title="מחשבון פריסה")
    
    # (כאן מגיע הקוד של האבטחה והחישובים שלך...)
    # נניח שחישבת את הנתונים לתוך pdf_data
    
    if st.button("📄 הפק דוח PDF"):
        # נתוני דוגמה לצורך הבדיקה
        pdf_data = {
            'client_name': "ישראל ישראלי",
            'client_id': "123456789",
            'total_grant': 500000,
            'savings': 45000,
            'table': [{"שנה": "2026", "הכנסה שנתית": "240,000", "מס": "12,000"}]
        }
        
        try:
            pdf_out = generate_pdf_report(pdf_data)
            st.download_button(
                label="📥 הורד דוח PDF",
                data=pdf_out,
                file_name="tax_report.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"שגיאה בהפקה: {e}")

if __name__ == "__main__":
    main()
