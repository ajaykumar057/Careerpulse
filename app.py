import gradio as gr
from groq import Groq
import docx2txt
import re
from fpdf import FPDF
import smtplib
from email.message import EmailMessage
import os

# ---------- CONFIG ----------
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or "your-groq-api-key"
EMAIL_SENDER = "ajayburdak266@gmail.com"
EMAIL_PASSWORD = "pnvp rgog gjrv xvcv"  # Use Gmail app password

client = Groq(api_key=GROQ_API_KEY)

cert_data = {
    "Full Stack Developer": [
        "Meta Full Stack Developer – Coursera",
        "Docker + Jenkins Mastery – Udemy"
    ],
    "DevOps Engineer": [
        "AWS DevOps Engineer – Coursera",
        "Docker & Kubernetes – Udemy"
    ],
    "Frontend Web Developer": [
        "React Front-End Developer – Meta",
        "W3Cx Front-End Developer Certification"
    ],
    "Backend Web Developer": [
        "Python + Django Backend – Udemy",
        "Advanced SQL – LinkedIn Learning"
    ]
}

# ---------- UTILITIES ----------
def extract_resume_data(file):
    try:
        text = docx2txt.process(file)
        skills = re.findall(
            r"(Python|SQL|React|Node\.js|UI/UX|Data Science|ML|AI|HTML|CSS|Docker|Jenkins|Django|JavaScript)",
            text, re.IGNORECASE
        )
        return list(set([s.lower() for s in skills]))
    except Exception as e:
        print("⚠️ Resume error:", e)
        return []

def suggest_certifications(careers):
    certs = ""
    for career in careers:
        if career in cert_data:
            certs += f"\n{career} Certifications:\n"
            for c in cert_data[career]:
                certs += f"- {c}\n"
    return certs

def generate_pdf(name, content, path="CareerReport.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Career Report for {name}\n\n{content}")
    pdf.output(path)
    return path

def send_email(receiver, file_path, name):
    try:
        msg = EmailMessage()
        msg["Subject"] = "Your CareerPulse Report"
        msg["From"] = EMAIL_SENDER
        msg["To"] = receiver
        msg.set_content(f"Hi {name},\n\nAttached is your personalized Career Report from CareerPulse 🚀")

        with open(file_path, "rb") as f:
            msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="CareerReport.pdf")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print("📧 Email error:", e)
        return False

# ---------- MAIN BOT FUNCTION ----------
def career_advisor(name, email, interests, skills, goals, experience, resume):
    print("▶️ Function called!")
    try:
        extracted = extract_resume_data(resume) if resume else []
        combined_skills = f"{skills}, " + ", ".join(extracted)

        prompt = f"""
You are CareerPulse, a smart career guidance AI.

Analyze the following:
- Name: {name}
- Experience: {experience}
- Interests: {interests}
- Skills: {combined_skills}
- Goals: {goals}

Suggest 2-3 suitable career paths with reasons.
List required skills or certifications if applicable.
"""

        res = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )

        output = res.choices[0].message.content.strip()

        # Extract career titles
        suggested_careers = []
        for line in output.split("\n"):
            if line.strip().startswith("1.") or line.strip().startswith("- "):
                suggested_careers.append(line.split(".")[-1].strip())

        certs = suggest_certifications(suggested_careers[:2])
        final_output = output + "\n\n" + certs

        pdf_path = generate_pdf(name, final_output)
        email_status = send_email(email, pdf_path, name)

        if email_status:
            notice = f"✅ Report sent to {email}\n\n"
        else:
            notice = f"⚠️ Email failed. Report saved locally as PDF\n\n"

        return notice + final_output

    except Exception as e:
        print("❌ Error:", e)
        return f"Something went wrong: {str(e)}"

# ---------- GRADIO UI ----------
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🎯 CareerPulse – Smart Career Guidance Chatbot")

    with gr.Row():
        name = gr.Textbox(label="Your Name")
        email = gr.Textbox(label="Your Email")
        experience = gr.Dropdown(["Student", "Fresher", "1-3 years", "3+ years"], label="Experience Level")

    interests = gr.Textbox(label="Your Interests")
    skills = gr.Textbox(label="Your Key Skills")
    goals = gr.Textbox(label="Career Goals")
    resume = gr.File(label="Upload Resume (.docx)", file_types=[".docx"])

    submit = gr.Button("Get Career Report 🚀")
    output = gr.Textbox(label="Your Career Report", lines=25)

    submit.click(
        career_advisor,
        inputs=[name, email, interests, skills, goals, experience, resume],
        outputs=output
    )

if __name__ == "__main__":
    demo.launch(share=True, ssr_mode=False)
