from django.core.management.base import BaseCommand
from users.models import User
from labels.models import Label
from notes.models import Note


class Command(BaseCommand):
    help = "Populate database with test notes and labels"

    def add_arguments(self, parser):
        parser.add_argument("user_id", type=int, help="User ID to populate notes for")

    def handle(self, *args, **options):
        user_id = options["user_id"]
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with ID {user_id} not found"))
            return

        # Create labels
        labels_data = [
            {"name": "Work", "color": "#FF6B6B"},
            {"name": "Personal", "color": "#4ECDC4"},
            {"name": "Ideas", "color": "#FFE66D"},
            {"name": "Learning", "color": "#95E1D3"},
        ]

        labels = {}
        for label_data in labels_data:
            label, created = Label.objects.get_or_create(
                user=user,
                name=label_data["name"],
            )
            labels[label_data["name"]] = label
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Created label: {label_data['name']}")
                )
            else:
                self.stdout.write(f"• Label already exists: {label_data['name']}")

        # Sample notes data
        notes_data = [
            {
                "title": "Python Best Practices",
                "content": "Learn about Python naming conventions, PEP 8, and code organization strategies.",
                "label": "Learning",
                "color": "#FFE66D",
                "is_pinned": True,
            },
            {
                "title": "Meeting Notes - Project Kickoff",
                "content": "Discussed project scope, timeline, and team responsibilities. Next meeting on Friday.",
                "label": "Work",
                "color": "#FF6B6B",
                "is_pinned": True,
            },
            {
                "title": "Django REST Framework Tutorial",
                "content": "Notes from DRF tutorial: serializers, viewsets, pagination, and authentication.",
                "label": "Learning",
                "color": "#FFE66D",
                "is_pinned": False,
            },
            {
                "title": "Birthday Gift Ideas",
                "content": "Consider: wireless headphones, book set, or a experience gift like cooking class.",
                "label": "Personal",
                "color": "#4ECDC4",
                "is_pinned": False,
            },
            {
                "title": "App Feature Ideas",
                "content": "1. Dark mode toggle\n2. Export notes as PDF\n3. Collaboration features\n4. Mobile app version",
                "label": "Ideas",
                "color": "#95E1D3",
                "is_pinned": True,
            },
            {
                "title": "Grocery List",
                "content": "Milk, eggs, bread, cheese, vegetables, coffee, tea, snacks",
                "label": "Personal",
                "color": "#4ECDC4",
                "is_pinned": False,
            },
            {
                "title": "Database Optimization Tips",
                "content": "Use indexes on frequently queried fields, implement caching, optimize queries with select_related.",
                "label": "Learning",
                "color": "#FFE66D",
                "is_pinned": False,
            },
            {
                "title": "Q4 Sales Report",
                "content": "Revenue increased by 25%, new customer acquisition up 40%, retention rate at 92%.",
                "label": "Work",
                "color": "#FF6B6B",
                "is_pinned": False,
            },
            {
                "title": "New API Endpoints Design",
                "content": "/api/users/ - CRUD operations\n/api/notes/ - Notes with pagination\n/api/labels/ - Label management",
                "label": "Work",
                "color": "#FF6B6B",
                "is_pinned": False,
            },
            {
                "title": "Meditation & Mindfulness",
                "content": "Started daily 10-minute meditation. Apps: Headspace, Calm. Goal: reduce stress.",
                "label": "Personal",
                "color": "#4ECDC4",
                "is_pinned": False,
            },
            {
                "title": "Microservices Architecture",
                "content": "Study plan: Docker, Kubernetes, service mesh (Istio), distributed logging (ELK stack).",
                "label": "Learning",
                "color": "#FFE66D",
                "is_pinned": False,
            },
            {
                "title": "Team Building Event",
                "content": "Planning team outing. Options: hiking, escape room, or virtual game night. Vote by Friday.",
                "label": "Work",
                "color": "#FF6B6B",
                "is_pinned": False,
            },
            {
                "title": "React Hooks Guide",
                "content": "useState, useEffect, useContext, useReducer, custom hooks. Practice with small projects.",
                "label": "Learning",
                "color": "#FFE66D",
                "is_pinned": False,
            },
            {
                "title": "Home Renovation Ideas",
                "content": "Paint living room blue, new kitchen cabinets, install smart lights, upgrade flooring.",
                "label": "Personal",
                "color": "#4ECDC4",
                "is_pinned": False,
            },
            {
                "title": "Network Security Basics",
                "content": "Firewalls, VPN, SSH keys, SSL certificates, OWASP top 10 vulnerabilities.",
                "label": "Learning",
                "color": "#FFE66D",
                "is_pinned": False,
            },
            {
                "title": "Q1 Planning Meeting",
                "content": "Discussed OKRs, budget allocation, hiring plan. Approve and send to department heads.",
                "label": "Work",
                "color": "#FF6B6B",
                "is_pinned": False,
            },
            {
                "title": "Fitness Goals 2025",
                "content": "Run a half marathon, strength training 3x/week, yoga 2x/week, maintain diet log.",
                "label": "Personal",
                "color": "#4ECDC4",
                "is_pinned": False,
            },
            {
                "title": "GraphQL vs REST",
                "content": "Comparison of GraphQL and REST APIs. When to use each. Real-world examples.",
                "label": "Learning",
                "color": "#FFE66D",
                "is_pinned": False,
            },
            {
                "title": "Client Feedback Summary",
                "content": "Requested features: better search, bulk operations, integration with Slack, dark mode.",
                "label": "Work",
                "color": "#FF6B6B",
                "is_pinned": True,
            },
            {
                "title": "Book Recommendations",
                "content": "Atomic Habits, The Pragmatic Programmer, Design Patterns, Clean Code, 12 Factor App.",
                "label": "Personal",
                "color": "#4ECDC4",
                "is_pinned": False,
            },
            {
                "title": "Cloud Deployment Strategy",
                "content": "AWS vs Azure vs GCP comparison, cost optimization, auto-scaling configuration.",
                "label": "Learning",
                "color": "#FFE66D",
                "is_pinned": False,
            },
            {
                "title": "Website Redesign Project",
                "content": "New branding, improved UX, mobile responsive, SEO optimization, CMS migration.",
                "label": "Work",
                "color": "#FF6B6B",
                "is_pinned": False,
            },
            {
                "title": "Travel Plans - Summer 2025",
                "content": "Europe: Italy, Greece, France. Budget: $5000, Duration: 3 weeks. Start planning in Feb.",
                "label": "Personal",
                "color": "#4ECDC4",
                "is_pinned": False,
            },
            {
                "title": "Machine Learning Basics",
                "content": "Supervised vs unsupervised learning, regression, classification, neural networks, TensorFlow.",
                "label": "Learning",
                "color": "#FFE66D",
                "is_pinned": False,
            },
            {
                "title": "Support Ticket Queue",
                "content": "Current: 45 open tickets. Response time: avg 2hrs. Implement chatbot for common issues.",
                "label": "Work",
                "color": "#FF6B6B",
                "is_pinned": False,
            },
            {
                "title": "Course Ideas for Next Quarter",
                "content": "Advanced JavaScript, System Design, Frontend Performance, DevOps Fundamentals.",
                "label": "Ideas",
                "color": "#95E1D3",
                "is_pinned": False,
            },
            {
                "title": "Code Review Guidelines",
                "content": "Standards for PR reviews, naming conventions, documentation requirements, test coverage minimum 80%.",
                "label": "Work",
                "color": "#FF6B6B",
                "is_pinned": False,
            },
            {
                "title": "Data Structures Deep Dive",
                "content": "Arrays, linked lists, stacks, queues, trees, graphs, hash tables. Time/space complexity analysis.",
                "label": "Learning",
                "color": "#FFE66D",
                "is_pinned": False,
            },
            {
                "title": "Product Roadmap Q2-Q3",
                "content": "Feature releases: advanced search, batch operations, integrations, analytics dashboard.",
                "label": "Work",
                "color": "#FF6B6B",
                "is_pinned": True,
            },
            {
                "title": "Weekend Project Ideas",
                "content": "1. Build a CLI tool\n2. Create open source package\n3. Contribute to GitHub projects\n4. Blog about tech topics",
                "label": "Ideas",
                "color": "#95E1D3",
                "is_pinned": False,
            },
        ]

        # Create notes
        for idx, note_data in enumerate(notes_data, 1):
            label_name = note_data.pop("label")
            label = labels.get(label_name)

            note, created = Note.objects.get_or_create(
                user=user,
                title=note_data["title"],
                defaults={
                    "content": note_data["content"],
                    "label": label,
                    "color": note_data["color"],
                    "is_pinned": note_data["is_pinned"],
                    "is_archived": False,
                },
            )

            if created:
                self.stdout.write(f"✓ {idx:2d}. Created: {note.title}")
            else:
                self.stdout.write(f"•    {idx:2d}. Already exists: {note.title}")

        # Final summary
        total_notes = Note.objects.filter(user=user).count()
        total_labels = Label.objects.filter(user=user).count()

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(
            self.style.SUCCESS(f"✓ Database populated successfully!")
        )
        self.stdout.write(f"  Total Notes: {total_notes}")
        self.stdout.write(f"  Total Labels: {total_labels}")
        self.stdout.write(self.style.SUCCESS("=" * 60))
