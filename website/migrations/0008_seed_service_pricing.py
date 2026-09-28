"""Fill in the open pricing the redesigned services screen shows."""

from django.db import migrations


SERVICE_PRICING = {
    "ai-automation": {
        "short_name": "AI & automation",
        "price_from": 85,
        "addon_factor": 1.1,
        "timeline": "4–8 weeks",
        "deliverable": "Agents live in your workflow",
        "summary": (
            "Custom AI agents that handle the repetitive, high-volume work your team shouldn't "
            "be doing manually: WhatsApp and chat agents running 24/7, workflow automation for "
            "invoices and reporting, M-Pesa and CRM integrations, and document processing that "
            "reads receipts, forms and PDFs on its own."
        ),
        "highlights": [
            "WhatsApp & chat agents",
            "Workflow automation",
            "AI-powered integrations",
            "Document & data processing",
        ],
    },
    "software-development": {
        "short_name": "custom software",
        "price_from": 180,
        "addon_factor": 1.35,
        "timeline": "8–14 weeks",
        "deliverable": "MVP in production",
        "summary": (
            "Production-grade software, not tech demos. MVPs that test your market hypothesis in "
            "weeks, multi-tenant SaaS platforms with billing and user management, internal tools "
            "that replace spreadsheets, and cross-platform mobile apps that work offline and "
            "speak M-Pesa."
        ),
        "highlights": [
            "MVPs & prototypes",
            "SaaS platforms",
            "Internal tools & dashboards",
            "Mobile apps & APIs",
        ],
    },
    "digital-transformation": {
        "short_name": "digital transformation",
        "price_from": 120,
        "addon_factor": 1.15,
        "timeline": "6–12 weeks",
        "deliverable": "Systems your team actually uses",
        "summary": (
            "Most SMEs run critical operations on WhatsApp groups, paper ledgers and spreadsheets "
            "held together with hope. We digitise systematically — automated M-Pesa "
            "reconciliation, ERP/CRM set up around how you really work, inventory and approval "
            "chains off paper, and a move off fragile local servers."
        ),
        "highlights": [
            "Payment & M-Pesa integration",
            "ERP & CRM setup",
            "Process digitisation",
            "Cloud migration",
        ],
    },
    "web-design": {
        "short_name": "web & product design",
        "price_from": 65,
        "addon_factor": 1.0,
        "timeline": "3–8 weeks",
        "deliverable": "Web app + design system",
        "summary": (
            "Your web presence is a business tool, not a brochure. Data-driven web applications "
            "with accounts and dashboards, eCommerce with M-Pesa checkout and inventory sync, "
            "UI/UX grounded in user research, and landing pages built to convert with tracking "
            "baked in."
        ),
        "highlights": [
            "Web applications",
            "E-commerce & marketplaces",
            "UI/UX design",
            "Landing pages & funnels",
        ],
    },
    "data-analytics": {
        "short_name": "data & BI",
        "price_from": 75,
        "addon_factor": 0.95,
        "timeline": "4–8 weeks",
        "deliverable": "Live dashboard + auto reports",
        "summary": (
            'You already have the data — sales, customers, M-Pesa, traffic. We connect the '
            'scattered sources into one reliable view, build dashboards that answer “how are we '
            'doing?” in under 30 seconds, and automate the reports nobody wants to assemble by '
            'hand.'
        ),
        "highlights": [
            "Custom dashboards",
            "Automated reporting",
            "Data pipeline setup",
            "AI-powered insights",
        ],
    },
    "tech-advisory": {
        "short_name": "tech advisory",
        "price_from": 45,
        "addon_factor": 0.6,
        "is_retainer": True,
        "timeline": "One-off or monthly",
        "deliverable": "Roadmap, audit, hiring support",
        "summary": (
            "Hands-on tech strategy on a fractional basis: prioritised roadmaps tied to business "
            "goals, honest architecture and code audits, unbiased build-vs-buy calls, help hiring "
            "and structuring your technical team, and technical documentation for investors and "
            "due diligence."
        ),
        "highlights": [
            "Tech strategy & roadmaps",
            "Architecture & code audits",
            "Vendor & tool selection",
            "Team building & hiring",
        ],
    },
}


def seed_pricing(apps, schema_editor):
    Service = apps.get_model("website", "Service")
    for slug, data in SERVICE_PRICING.items():
        service = Service.objects.filter(slug=slug).first()
        if service is None:
            continue
        service.short_name = data["short_name"]
        service.price_from = data["price_from"]
        service.addon_factor = data["addon_factor"]
        service.is_retainer = data.get("is_retainer", False)
        service.timeline = data["timeline"]
        service.deliverable = data["deliverable"]
        service.summary = data["summary"]
        service.highlights = "\n".join(data["highlights"])
        service.save()


def clear_pricing(apps, schema_editor):
    Service = apps.get_model("website", "Service")
    Service.objects.filter(slug__in=SERVICE_PRICING).update(
        short_name="",
        price_from=0,
        addon_factor=1.0,
        is_retainer=False,
        timeline="",
        deliverable="",
        summary="",
        highlights="",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("website", "0007_case_study_and_enquiry_fields"),
    ]

    operations = [
        migrations.RunPython(seed_pricing, clear_pricing),
    ]
