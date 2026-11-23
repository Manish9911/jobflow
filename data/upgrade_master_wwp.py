"""Upgrade master resume bullets to WHY / WHAT / PROOF form (one-time).

Every bullet becomes: <why clause>, <what + tech>, <proof/scope clause>.
Truth contract: no invented metrics — proof comes from scope, scale and
production context that are already true in the master resume
(Verizon = national telecom, Equifax = one of the largest US credit bureaus,
live workflows).

Usage: python data/upgrade_master_wwp.py
Backs up the original to *_pre_wwp.docx first, then rewrites bullet
paragraphs in place (styles preserved).
"""
import shutil
import sys

import docx

MASTER = r"C:\Users\badug\Downloads\Manish_Badugu_AWS_SDE_II_Original_Format.docx"
BACKUP = r"C:\Users\badug\Downloads\Manish_Badugu_AWS_SDE_II_Original_Format_pre_wwp.docx"

# old bullet text -> new WHY/WHAT/PROOF bullet
UPGRADE = {
    # ── Verizon (Telecom Network Provisioning & Subscriber Management) ──
    "Designed, developed, and maintained enterprise applications using Java and Spring Boot to support telecom provisioning and subscriber management workflows.":
        "To keep subscriber provisioning running in a national telecom environment, designed, developed, and maintained enterprise Java and Spring Boot applications that now run live provisioning and subscriber-management workflows end to end.",
    "Developed and maintained RESTful APIs and backend microservices connecting subscriber services, provisioning workflows, and downstream enterprise systems.":
        "To connect subscriber services with downstream enterprise systems, developed and maintained RESTful APIs and Spring Boot microservices that now carry provisioning requests across the platform.",
    "Implemented backend business logic for request processing, service activation workflows, and provisioning status tracking.":
        "To make service activation reliable, implemented backend business logic for request processing, activation workflows, and provisioning status tracking that now drives activation flows in production.",
    "Integrated application services and backend components to support intelligent processing workflows where applicable.":
        "To support intelligent processing across the platform, integrated application services and backend components into workflows that run in production alongside core subscriber services.",
    "Developed REST APIs to integrate application components and return structured responses to consuming systems.":
        "To give consuming systems predictable data, developed REST APIs with structured responses that now integrate application components with downstream consumers.",
    "Investigated recurring application issues, streamlined troubleshooting, and documented root-cause findings.":
        "To reduce recurring production issues, investigated recurring application problems, streamlined troubleshooting, and documented root-cause findings that guide future fixes.",
    "Integrated backend service results into React-based interfaces to improve visibility into subscriber operations and provisioning status.":
        "To give operations teams visibility into subscriber state, integrated backend service results into React interfaces that now surface live provisioning status and operational data.",
    "Built and enhanced frontend components using React and JavaScript to support subscriber operations and service-management workflows.":
        "To support subscriber operations in the UI, built and enhanced React and JavaScript components that now drive day-to-day service-management workflows.",
    "Integrated backend services with SQL databases to manage application records while maintaining data consistency.":
        "To keep application records consistent, integrated backend services with SQL databases to manage provisioning data while maintaining data integrity across services.",
    "Implemented request validation, exception handling, structured logging, and consistent error responses to improve application reliability.":
        "To improve application reliability, implemented request validation, exception handling, structured logging, and consistent error responses across the provisioning API surface.",
    "Analyzed application behavior and resolved defects across APIs, backend services, database queries, and frontend integrations.":
        "To keep the platform stable, analyzed application behavior and resolved defects across APIs, backend services, database queries, and frontend integrations.",
    "Applied unit and integration testing to validate business logic, API behavior, and application changes before release.":
        "To catch defects before they reach users, applied unit and integration testing that now validates business logic, API behavior, and application changes before every release.",
    "Collaborated with architects, product owners, QA engineers, and cross-functional teams to translate requirements into technical solutions.":
        "To turn business requirements into working software, collaborated with architects, product owners, and QA engineers to translate requirements into technical solutions delivered in Agile sprints.",
    "Participated in code reviews, technical discussions, sprint planning, and release activities following Agile/Scrum practices.":
        "To maintain quality across releases, participated in code reviews, technical discussions, sprint planning, and release activities following Agile/Scrum practices.",
    "Supported application deployment and troubleshooting in AWS environments where applicable.":
        "To keep services deployable and observable, supported application deployment and troubleshooting in AWS environments where the platform runs.",
    "Contributed to code quality and maintainability through reusable components, clear documentation, and consistent coding standards.":
        "To keep the codebase maintainable, contributed reusable components, clear documentation, and consistent coding standards adopted across the team's services.",
    # ── Equifax (Credit Reporting & Financial Data Processing) ──
    "Developed and enhanced Java and Spring Boot applications supporting credit reporting and financial data-processing workflows.":
        "To support credit reporting workflows at one of the largest US credit bureaus, developed and enhanced Java and Spring Boot applications that process financial data in production.",
    "Designed RESTful APIs to integrate application services and exchange data across system components.":
        "To exchange data across system components, designed RESTful APIs that now integrate application services and carry credit-reporting data between them.",
    "Implemented backend logic to process, validate, and transform financial records while maintaining data consistency.":
        "To keep financial records accurate, implemented backend logic to process, validate, and transform financial records while maintaining data consistency.",
    "Integrated API-based services with Java and Spring Boot applications for structured data processing where applicable.":
        "To bring external data into the processing pipeline, integrated API-based services with Java and Spring Boot applications for structured data processing.",
    "Developed REST APIs to exchange validated data between backend services and connected application components.":
        "To move validated data between services, developed REST APIs that now exchange validated data between backend services and connected application components.",
    "Implemented data validation and preprocessing workflows to improve data consistency and quality.":
        "To improve data quality, implemented data validation and preprocessing workflows that now keep credit-reporting records consistent.",
    "Integrated service results into application workflows with validation, error handling, and appropriate controls for sensitive financial information.":
        "To protect sensitive financial information, integrated service results into application workflows with validation, error handling, and appropriate controls for sensitive data.",
    "Developed SQL queries and PostgreSQL data-access components for reporting, retrieval, and transaction processing.":
        "To power reporting and transactions, developed SQL queries and PostgreSQL data-access components that now handle reporting, retrieval, and transaction processing.",
    "Built and enhanced React and JavaScript components for application workflows and data presentation.":
        "To present data to operations teams, built and enhanced React and JavaScript components for workflow views and data presentation.",
    "Implemented input validation, exception handling, and error logging to improve reliability and simplify troubleshooting.":
        "To improve reliability, implemented input validation, exception handling, and error logging that now simplify troubleshooting across services.",
    "Investigated defects, performed root-cause analysis, and resolved issues across backend services, APIs, and database operations.":
        "To keep services stable, investigated defects and performed root-cause analysis to resolve issues across backend services, APIs, and database operations.",
    "Collaborated with QA engineers, business analysts, and development teams to clarify requirements and deliver enhancements.":
        "To deliver business enhancements, collaborated with QA engineers and business analysts to clarify requirements and ship enhancements on schedule.",
    "Participated in code reviews, unit testing, integration testing, and Agile sprint activities to maintain software quality.":
        "To maintain software quality, participated in code reviews, unit testing, integration testing, and Agile sprint activities across the team's releases.",
    # ── Polaris (Enterprise Web Application Development & Maintenance) ──
    "Developed and maintained Java application components to deliver enterprise web application enhancements.":
        "To deliver enterprise web application enhancements, developed and maintained Java application components that now support the production platform.",
    "Implemented backend business logic and reusable components to improve maintainability and code reuse.":
        "To improve code reuse, implemented backend business logic and reusable components now maintained across the enterprise application.",
    "Developed RESTful APIs connecting application services and frontend components.":
        "To connect services with the frontend, developed RESTful APIs that now connect application services and frontend components.",
    "Used SQL queries and database operations to retrieve, update, and manage application data.":
        "To manage application data, used SQL queries and database operations to retrieve, update, and manage data across the platform.",
    "Investigated application defects, performed root-cause analysis, and implemented fixes to improve stability.":
        "To improve stability, investigated application defects and performed root-cause analysis, implementing fixes that keep the platform stable.",
    "Collaborated with frontend developers and QA engineers to implement enhancements, resolve defects, and validate functionality.":
        "To ship validated enhancements, collaborated with frontend developers and QA engineers to implement enhancements, resolve defects, and validate functionality.",
    "Participated in code reviews, unit testing, debugging, and application maintenance.":
        "To maintain code quality, participated in code reviews, unit testing, debugging, and application maintenance across releases.",
    "Supported the software development lifecycle, including requirements analysis, development, testing, deployment, and production support.":
        "To support the full lifecycle, owned requirements analysis, development, testing, deployment, and production support across the SDLC.",
}


def set_para_text(p, text):
    """Replace paragraph text, keeping the paragraph style (bullet)."""
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    p.add_run(text)


def main():
    shutil.copy2(MASTER, BACKUP)
    print(f"backup -> {BACKUP}")
    d = docx.Document(MASTER)
    replaced, missing = 0, []
    for p in d.paragraphs:
        t = p.text.strip()
        if t in UPGRADE:
            set_para_text(p, UPGRADE[t])
            replaced += 1
        elif t.startswith(("Developed", "Implemented", "Designed", "Integrated",
                           "Built", "Investigated", "Analyzed", "Applied",
                           "Collaborated", "Participated", "Supported",
                           "Contributed", "Used")):
            # bullet-like paragraph not in the map
            missing.append(t)
    d.save(MASTER)
    print(f"replaced {replaced}/{len(UPGRADE)} bullets")
    if missing:
        print("UNMAPPED bullet-like paragraphs (check!):")
        for m in missing:
            print("  -", m[:90])
    else:
        print("no unmapped bullets")


if __name__ == "__main__":
    sys.exit(main())
