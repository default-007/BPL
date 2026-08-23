from django.db import migrations


NEW_SERVICES = [
    {
        "name": "AI Solutions & Automation",
        "tagline": "Put AI to work across your business",
        "icons": "pr-line-lightbulb",
        "slug": "ai-automation",
        "order": 1,
        "description": (
            "## Intelligent systems that run while you sleep\n\n"
            "AI isn't a buzzword — it's the biggest operational leverage available to SMEs today. "
            "We build **custom AI agents** that handle the repetitive, high-volume work your team "
            "shouldn't be doing manually.\n\n"
            "### What we build\n\n"
            "- **WhatsApp & chat agents** — Customer support, order-taking, appointment booking, "
            "and follow-ups that run 24/7 on the channels your customers already use\n"
            "- **Workflow automation** — Invoice processing, data entry, report generation, and "
            "internal ops that used to eat hours of your week\n"
            "- **AI-powered integrations** — Connect your M-Pesa, CRM, inventory, and comms into "
            "one intelligent pipeline\n"
            "- **Document & data processing** — Extract, classify, and act on information from "
            "receipts, forms, emails, and PDFs automatically\n\n"
            "### Why it matters\n\n"
            "Your competitors are still hiring people to do work that software can handle faster, "
            "cheaper, and around the clock. We help you skip that phase entirely.\n\n"
            "Every solution we build is designed to integrate with the tools you already use — "
            "no rip-and-replace, no steep learning curves."
        ),
    },
    {
        "name": "Custom Software & MVP Development",
        "tagline": "From concept to working product, fast",
        "icons": "pr-line-desktop",
        "slug": "software-development",
        "order": 2,
        "description": (
            "## Your idea, built and shipped\n\n"
            "Whether you're validating a new product or scaling an existing one, we build "
            "production-grade software that solves real problems — not tech demos.\n\n"
            "### What we deliver\n\n"
            "- **MVPs & prototypes** — Test your market hypothesis with a working product in "
            "weeks, not months. Built lean, designed to scale\n"
            "- **SaaS platforms** — Multi-tenant web applications with subscription billing, "
            "user management, and the infrastructure to grow\n"
            "- **Internal tools & dashboards** — Stop running your business on spreadsheets. "
            "Custom tools built around your actual workflows\n"
            "- **Mobile applications** — Cross-platform apps that work offline, integrate with "
            "M-Pesa, and handle East African network realities\n"
            "- **API development & integrations** — Connect your systems, expose your data, "
            "and build the plumbing that makes everything work together\n\n"
            "### Our approach\n\n"
            "We ship in short cycles — you see working software every two weeks, not a big reveal "
            "after three months. Every build includes proper testing, documentation, and a clear "
            "path to hand-off or continued iteration."
        ),
    },
    {
        "name": "Digital Transformation",
        "tagline": "Modernise your operations without the chaos",
        "icons": "pr-line-refresh",
        "slug": "digital-transformation",
        "order": 3,
        "description": (
            "## Move from manual to modern\n\n"
            "Most SMEs are running critical operations on WhatsApp groups, paper ledgers, and "
            "spreadsheets held together with hope. We help you digitise systematically — "
            "without disrupting what's already working.\n\n"
            "### What this looks like\n\n"
            "- **Payment & M-Pesa integration** — Automated reconciliation, real-time transaction "
            "tracking, and payment workflows that eliminate manual matching\n"
            "- **ERP & CRM setup** — Odoo, ERPNext, or custom solutions configured for how your "
            "business actually operates, not how a manual says it should\n"
            "- **Process digitisation** — Inventory management, HR workflows, procurement, and "
            "approval chains moved from paper and chat to proper systems\n"
            "- **Cloud migration** — Move off fragile local servers to infrastructure that's "
            "secure, backed up, and accessible from anywhere\n\n"
            "### Why SMEs choose us\n\n"
            "We've implemented these systems for businesses across Kenya — from beauty parlours "
            "to logistics companies. We know the real constraints: intermittent connectivity, "
            "staff who aren't tech-native, and budgets that demand ROI within months, not years."
        ),
    },
    {
        "name": "Web Applications & Product Design",
        "tagline": "Digital experiences that convert",
        "icons": "pr-line-browser",
        "slug": "web-design",
        "order": 4,
        "description": (
            "## Beyond templates and page builders\n\n"
            "Your web presence isn't a brochure — it's a business tool. We design and build "
            "web applications that look sharp, load fast, and drive measurable results.\n\n"
            "### What we build\n\n"
            "- **Web applications** — Dynamic, data-driven platforms with user accounts, "
            "dashboards, and real functionality — not static pages\n"
            "- **E-commerce & marketplaces** — Online stores with M-Pesa checkout, inventory "
            "sync, and order management built in\n"
            "- **UI/UX design** — User research, wireframes, and polished interfaces designed "
            "for your actual users, not design award juries\n"
            "- **Landing pages & conversion funnels** — Performance-focused pages built to turn "
            "visitors into customers, with tracking and A/B testing baked in\n\n"
            "### Design philosophy\n\n"
            "Good design is invisible — it gets out of the user's way and lets them accomplish "
            "what they came to do. We build interfaces that work on the devices and connections "
            "your customers actually have."
        ),
    },
    {
        "name": "Data & Business Intelligence",
        "tagline": "See what your numbers are actually telling you",
        "icons": "pr-line-bargraph",
        "slug": "data-analytics",
        "order": 5,
        "description": (
            "## Turn your data into decisions\n\n"
            "You're sitting on more data than you realise — sales records, customer interactions, "
            "M-Pesa transactions, website traffic. The problem isn't collecting it. It's making "
            "sense of it.\n\n"
            "### What we deliver\n\n"
            "- **Custom dashboards** — Real-time visibility into the metrics that actually matter "
            "for your business, accessible from any device\n"
            "- **Automated reporting** — Daily, weekly, or monthly reports generated and delivered "
            "automatically — no more manual number-crunching\n"
            "- **Data pipeline setup** — Connect your scattered data sources into a single, "
            "reliable view of your business\n"
            "- **AI-powered insights** — Pattern detection, anomaly alerts, and predictive "
            "analytics that surface opportunities and risks before they're obvious\n\n"
            "### The goal\n\n"
            "Every decision-maker in your business should be able to answer \"how are we doing?\" "
            "in under 30 seconds, without asking someone to pull a report."
        ),
    },
    {
        "name": "Fractional CTO & Tech Advisory",
        "tagline": "Senior tech leadership without the full-time cost",
        "icons": "pr-line-strategy",
        "slug": "tech-advisory",
        "order": 6,
        "description": (
            "## Strategic tech guidance for growing businesses\n\n"
            "You need senior technical leadership but can't justify — or find — a full-time CTO. "
            "We provide hands-on tech strategy, architecture decisions, and team guidance on a "
            "fractional basis.\n\n"
            "### What you get\n\n"
            "- **Tech strategy & roadmaps** — A clear, prioritised plan for your technology "
            "investments aligned with your business goals\n"
            "- **Architecture & code audits** — Honest assessment of your current systems — "
            "what's solid, what's fragile, and what needs attention now\n"
            "- **Vendor & tool selection** — Unbiased guidance on build-vs-buy decisions, "
            "SaaS selection, and technology partnerships\n"
            "- **Team building & hiring** — Help writing job specs, evaluating candidates, "
            "and structuring your technical team for the stage you're at\n"
            "- **Investor & due diligence support** — Technical documentation and architecture "
            "presentations for fundraising and partnerships\n\n"
            "### How it works\n\n"
            "Engagements range from a one-off architecture review to ongoing weekly advisory. "
            "You get the thinking and decision-making of an experienced CTO at a fraction of "
            "the cost — and without the equity ask."
        ),
    },
]


def seed_services(apps, schema_editor):
    Service = apps.get_model('website', 'Service')
    # Clear existing services
    Service.objects.all().delete()
    # Create new ones
    for svc in NEW_SERVICES:
        Service.objects.create(**svc)


def reverse_seed(apps, schema_editor):
    # No-op — manual restore if needed
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0003_service_tagline_service_order'),
    ]

    operations = [
        migrations.RunPython(seed_services, reverse_seed),
    ]
