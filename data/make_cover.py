import sys
from fpdf import FPDF

def cover(company, role, out):
    pdf = FPDF()
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    pdf.set_x(20)
    lines = [
        "Manish Badugu",
        "Almond Willow CV, Collierville, TN 38017",
        "badugu.m7@gmail.com | +1 940-843-6058",
        "linkedin.com/in/badugu-manish-2241",
        "",
        f"Dear {company} Hiring Team,",
        "",
        f"I am writing to express my interest in the {role} position. I am a software engineer with 4+ years of",
        "experience designing and delivering production software across the full stack: Java and Spring Boot",
        "services, React applications, PostgreSQL databases, REST APIs, and AWS cloud infrastructure.",
        "",
        "In my recent role as a senior full-stack developer, I built and maintained microservice-based platforms",
        "serving high-volume transactional workloads, owned features end-to-end from requirements through",
        "deployment, and collaborated with cross-functional teams on design, code review, testing, and",
        "documentation. I am comfortable working in regulated and quality-driven environments where verification,",
        "validation, and clear engineering documentation matter.",
        "",
        "I am legally authorized to work in the United States and am currently on STEM OPT. I would welcome the",
        f"opportunity to bring my experience to {company}. Thank you for your consideration.",
        "",
        "Sincerely,",
        "Manish Badugu",
    ]
    for ln in lines:
        pdf.cell(0, 7, ln, new_x="LMARGIN", new_y="NEXT")
    pdf.output(out)
    print("wrote", out)

if __name__ == "__main__":
    cover(sys.argv[1], sys.argv[2], sys.argv[3])
