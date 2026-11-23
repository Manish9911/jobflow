"""Compress WHY/WHAT/PROOF bullets to fit 2 pages (one-time pass 2).

Format 2: "<what + tech> to <why> — <proof>" or "To <why>, <what> — <proof>".
All three elements stay visible; ~110-135 chars per bullet (master baseline).
"""
import sys

import docx

MASTER = r"C:\Users\badug\Downloads\Manish_Badugu_AWS_SDE_II_Original_Format.docx"

# current WWP bullet -> compact WWP bullet
COMPACT = {
    "To keep subscriber provisioning running in a national telecom environment, designed, developed, and maintained enterprise Java and Spring Boot applications that now run live provisioning and subscriber-management workflows end to end.":
        "Designed and maintained enterprise Java and Spring Boot applications to keep Verizon's national telecom provisioning running — now live in production, end to end.",
    "To connect subscriber services with downstream enterprise systems, developed and maintained RESTful APIs and Spring Boot microservices that now carry provisioning requests across the platform.":
        "Developed and maintained RESTful APIs and Spring Boot microservices to connect subscriber services with downstream systems — now live across the platform.",
    "To make service activation reliable, implemented backend business logic for request processing, activation workflows, and provisioning status tracking that now drives activation flows in production.":
        "Implemented backend logic for request processing, service activation, and status tracking to make activation reliable — now driving live activation flows.",
    "To support intelligent processing across the platform, integrated application services and backend components into workflows that run in production alongside core subscriber services.":
        "Integrated application services and backend components to support intelligent processing workflows — now running in production alongside core subscriber services.",
    "To give consuming systems predictable data, developed REST APIs with structured responses that now integrate application components with downstream consumers.":
        "Developed REST APIs with structured responses to give consuming systems predictable data — now integrating components with downstream consumers.",
    "To reduce recurring production issues, investigated recurring application problems, streamlined troubleshooting, and documented root-cause findings that guide future fixes.":
        "Investigated recurring issues and documented root-cause findings to streamline troubleshooting — reducing repeat production problems.",
    "To give operations teams visibility into subscriber state, integrated backend service results into React interfaces that now surface live provisioning status and operational data.":
        "Integrated backend results into React interfaces to give operations teams visibility — now surfacing live provisioning status and subscriber data.",
    "To support subscriber operations in the UI, built and enhanced React and JavaScript components that now drive day-to-day service-management workflows.":
        "Built and enhanced React and JavaScript components to support subscriber operations — now driving day-to-day service-management workflows.",
    "To keep application records consistent, integrated backend services with SQL databases to manage provisioning data while maintaining data integrity across services.":
        "Integrated backend services with SQL databases to keep application records consistent — maintaining data integrity across services.",
    "To improve application reliability, implemented request validation, exception handling, structured logging, and consistent error responses across the provisioning API surface.":
        "Implemented request validation, exception handling, structured logging, and consistent errors to improve reliability across the API surface.",
    "To keep the platform stable, analyzed application behavior and resolved defects across APIs, backend services, database queries, and frontend integrations.":
        "Analyzed application behavior and resolved defects across APIs, services, database queries, and frontend integrations to keep the platform stable.",
    "To catch defects before they reach users, applied unit and integration testing that now validates business logic, API behavior, and application changes before every release.":
        "Applied unit and integration testing to catch defects before release — validating business logic, API behavior, and application changes.",
    "To turn business requirements into working software, collaborated with architects, product owners, and QA engineers to translate requirements into technical solutions delivered in Agile sprints.":
        "Collaborated with architects, product owners, and QA to turn business requirements into technical solutions delivered in Agile sprints.",
    "To maintain quality across releases, participated in code reviews, technical discussions, sprint planning, and release activities following Agile/Scrum practices.":
        "Participated in code reviews, technical discussions, sprint planning, and release activities to maintain quality across releases.",
    "To keep services deployable and observable, supported application deployment and troubleshooting in AWS environments where the platform runs.":
        "Supported application deployment and troubleshooting in AWS environments to keep services deployable where the platform runs.",
    "To keep the codebase maintainable, contributed reusable components, clear documentation, and consistent coding standards adopted across the team's services.":
        "Contributed reusable components, clear documentation, and consistent coding standards to keep the codebase maintainable.",
    # Equifax
    "To support credit reporting workflows at one of the largest US credit bureaus, developed and enhanced Java and Spring Boot applications that process financial data in production.":
        "Developed and enhanced Java and Spring Boot applications to support credit-reporting workflows at one of the largest US credit bureaus — live in production.",
    "To exchange data across system components, designed RESTful APIs that now integrate application services and carry credit-reporting data between them.":
        "Designed RESTful APIs to exchange data across system components — now carrying credit-reporting data between services.",
    "To keep financial records accurate, implemented backend logic to process, validate, and transform financial records while maintaining data consistency.":
        "Implemented backend logic to process, validate, and transform financial records to keep them accurate — maintaining data consistency.",
    "To bring external data into the processing pipeline, integrated API-based services with Java and Spring Boot applications for structured data processing.":
        "Integrated API-based services with Java and Spring Boot applications to bring external data into the processing pipeline.",
    "To move validated data between services, developed REST APIs that now exchange validated data between backend services and connected application components.":
        "Developed REST APIs to move validated data between backend services and connected components — now live in the data pipeline.",
    "To improve data quality, implemented data validation and preprocessing workflows that now keep credit-reporting records consistent.":
        "Implemented data validation and preprocessing workflows to improve data quality — now keeping credit-reporting records consistent.",
    "To protect sensitive financial information, integrated service results into application workflows with validation, error handling, and appropriate controls for sensitive data.":
        "Integrated service results into workflows with validation, error handling, and controls to protect sensitive financial information.",
    "To power reporting and transactions, developed SQL queries and PostgreSQL data-access components that now handle reporting, retrieval, and transaction processing.":
        "Developed SQL queries and PostgreSQL data-access components to power reporting, retrieval, and transaction processing.",
    "To present data to operations teams, built and enhanced React and JavaScript components for workflow views and data presentation.":
        "Built and enhanced React and JavaScript components to present data to operations teams in workflow views.",
    "To improve reliability, implemented input validation, exception handling, and error logging that now simplify troubleshooting across services.":
        "Implemented input validation, exception handling, and error logging to improve reliability and simplify troubleshooting.",
    "To keep services stable, investigated defects and performed root-cause analysis to resolve issues across backend services, APIs, and database operations.":
        "Investigated defects and performed root-cause analysis to keep services stable across backend, APIs, and database operations.",
    "To deliver business enhancements, collaborated with QA engineers and business analysts to clarify requirements and ship enhancements on schedule.":
        "Collaborated with QA engineers and business analysts to clarify requirements and ship enhancements on schedule.",
    "To maintain software quality, participated in code reviews, unit testing, integration testing, and Agile sprint activities across the team's releases.":
        "Participated in code reviews, unit testing, integration testing, and Agile sprint activities to maintain software quality.",
    "To keep deployments stable, supported application deployments and troubleshooting in AWS environments where the platform runs.":
        "Supported application deployments and troubleshooting in AWS environments to keep deployments stable.",
    # Polaris
    "To deliver enterprise web application enhancements, developed and maintained Java application components that now support the production platform.":
        "Developed and maintained Java application components to deliver enterprise web enhancements — now supporting the production platform.",
    "To improve code reuse, implemented backend business logic and reusable components now maintained across the enterprise application.":
        "Implemented backend business logic and reusable components to improve code reuse across the enterprise application.",
    "To connect services with the frontend, developed RESTful APIs that now connect application services and frontend components.":
        "Developed RESTful APIs to connect application services with frontend components.",
    "To manage application data, used SQL queries and database operations to retrieve, update, and manage data across the platform.":
        "Used SQL queries and database operations to retrieve, update, and manage application data across the platform.",
    "To improve stability, investigated application defects and performed root-cause analysis, implementing fixes that keep the platform stable.":
        "Investigated defects and performed root-cause analysis, implementing fixes to improve platform stability.",
    "To ship validated enhancements, collaborated with frontend developers and QA engineers to implement enhancements, resolve defects, and validate functionality.":
        "Collaborated with frontend developers and QA to implement enhancements, resolve defects, and validate functionality.",
    "To maintain code quality, participated in code reviews, unit testing, debugging, and application maintenance across releases.":
        "Participated in code reviews, unit testing, debugging, and maintenance to maintain code quality.",
    "To support the full lifecycle, owned requirements analysis, development, testing, deployment, and production support across the SDLC.":
        "Supported the full SDLC — requirements analysis, development, testing, deployment, and production support.",
}


def main():
    d = docx.Document(MASTER)
    replaced, left = 0, []
    for p in d.paragraphs:
        t = p.text.strip()
        if t in COMPACT:
            for r in list(p.runs):
                r._element.getparent().remove(r._element)
            p.add_run(COMPACT[t])
            replaced += 1
        elif t.startswith("To "):
            left.append(t)
    d.save(MASTER)
    print(f"compacted {replaced}/{len(COMPACT)}")
    if left:
        print("STILL LONG FORM:")
        for l in left:
            print("  -", l[:100])
    # average bullet length
    d2 = docx.Document(MASTER)
    bl = [len(p.text.strip()) for p in d2.paragraphs if p.text.strip().startswith(("To ", "Designed", "Developed", "Implemented", "Integrated", "Built", "Investigated", "Analyzed", "Applied", "Collaborated", "Participated", "Supported", "Contributed", "Used"))]
    print(f"bullets: {len(bl)}, avg len: {sum(bl)//len(bl)}")


if __name__ == "__main__":
    sys.exit(main())
