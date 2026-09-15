from flask import Flask, render_template, request

app = Flask(__name__)

LANGUAGES = {"de", "en"}
DEFAULT_LANGUAGE = "de"
LANGUAGE_COOKIE_NAME = "site_lang"

TRANSLATIONS = {
    "de": {
        "site_name": "A.C.E",
        "home_aria_label": "A.C.E Startseite",
        "main_navigation": "Hauptnavigation",
        "language_switch": "Sprachauswahl",
        "nav_home": "Home",
        "nav_about": "Über uns",
        "nav_team": "Team",
        "nav_car": "Unser Auto",
        "nav_project": "Projekt",
        "nav_sponsors": "Sponsoren",
        "nav_contact": "Kontakt",
        "skip_to_content": "Zum Inhalt springen",
        "menu_open": "Menü öffnen",
        "menu_close": "Menü schließen",
        "home_hero_description": "Technik. Teamwork. Innovation. Gemeinsam entwickeln wir unseren eigenen Rennwagen.",
        "home_about": "Über uns",
        "home_car": "Unser Auto",
        "section_project": "UNSER PROJEKT",
        "project_heading": "Engineering the Future",
        "home_project_intro": "Wir sind ein neu gegründetes Team und nehmen am STEM-Racing-Projekt teil.",
        "card_team_title": "TEAM",
        "card_team_text": "Lernen Sie unser Team und unsere Aufgaben kennen.",
        "card_team_link": "Mehr erfahren →",
        "card_engineering_title": "ENGINEERING",
        "card_engineering_text": "Von der Idee über CAD bis zum fertigen Rennwagen.",
        "card_engineering_link": "Unser Projekt →",
        "card_racing_title": "RACING",
        "card_racing_text": "Unser Ziel: einen möglichst schnellen und gut entwickelten Rennwagen zu bauen.",
        "card_racing_link": "Unser Auto →",
        "about_title": "Über uns",
        "about_header": "Wer sind wir?",
        "about_intro": "Wir sind ein neu gegründetes Team des Einhard-Gymnasiums Aachen und nehmen am STEM-Racing-Projekt teil.",
        "about_idea": "Unsere Idee",
        "about_idea_text_1": "Bei STEM Racing verbinden wir Technik, Konstruktion, Kreativität und Teamarbeit.",
        "about_idea_text_2": "Unser Ziel ist es, gemeinsam einen möglichst schnellen und gut entwickelten Rennwagen zu konstruieren und dabei möglichst viel über moderne Ingenieurarbeit zu lernen.",
        "about_focus": "Unser Fokus",
        "about_experience": "Unsere bisherigen Erfahrungen",
        "about_experience_text": "Durch unsere bisherigen Erfahrungen mit LEGO, Technik und Teamarbeit konnten wir bereits wichtige Schritte für unser Projekt lernen.",
        "team_page_title": "Team",
        "team_header": "Das Team",
        "team_section_label": "MEET THE TEAM",
        "team_section_title": "Unser Team",
        "team_photo": "TEAMFOTO",
        "team_photo_subtitle": "Bild folgt",
        "team_card_1_role": "Head of IT & Media, Teil des Konstruktionsteams/Forschung",
        "team_card_2_role": "Teamleader, Teil des Konstruktionsteams/Forschung",
        "team_card_3_role": "Head of Production, Teil des Konstruktionsteams/Forschung",
        "team_card_4_role": "Head of Graphics/Designing und Social Media",
        "team_card_5_role": "Head of PR & Marketing",
        "team_philosophy": "Gemeinsam statt allein.",
        "team_philosophy_text_1": "STEM Racing ist mehr als nur ein Rennwagen. Wir arbeiten gemeinsam an Konstruktion, Technik, Planung und Präsentation.",
        "team_philosophy_text_2": "Jeder von uns bringt eigene Interessen, Ideen und Fähigkeiten mit. Genau diese Kombination macht unser Team aus.",
        "team_summary_title": "A.C.E",
        "team_summary_1": "5 Teammitglieder",
        "team_summary_2": "STEM Racing 2026/27",
        "team_summary_3": "Einhard-Gymnasium Aachen",
        "team_summary_4": "Engineering & Racing",
        "contact_page_title": "Kontakt",
        "contact_intro": "Sie möchten mehr über unser Team oder unser STEM-Racing-Projekt erfahren? Schreiben Sie uns gerne.",
        "contact_label": "CONTACT",
        "contact_heading": "Kontaktieren Sie uns.",
        "contact_text": "Ob Fragen zu unserem Projekt, Interesse an einer Partnerschaft oder einfach Interesse an unserem Team – wir freuen uns über Ihre Nachricht.",
        "contact_person_minh": "Kontaktdaten: Minh Dao (IT & Media, Konstruktion & Forschung)",
        "contact_person_omar": "Kontaktdaten: Omar Ahmed (Head of PR & Marketing)",
        "contact_person_tri": "Kontaktdaten: Tri-Dung Tran (Graphics, Design & Social Media)",
        "contact_person_yashmith": "Kontaktdaten: Yashmith Gettam (Teamleader, Konstruktion & Forschung)",
        "contact_person_darius": "Kontaktdaten: Darius Melian Flamand (Production, Konstruktion & Forschung)",
        "contact_write": "schreiben",
        "contact_box_title": "A.C.E",
        "project_page_title": "Projekt",
        "project_header": "Engineering the Future",
        "project_intro": "STEM Racing verbindet Technik, Kreativität und Organisation in einem echten Teamprojekt.",
        "project_phase_title": "Projektphasen",
        "project_phase_1": "Recherche und Planung",
        "project_phase_2": "CAD und Konstruktion",
        "project_phase_3": "Fertigung und Tests",
        "project_phase_4": "Präsentation und Rennen",
        "project_label_1": "VON DER IDEE ZUM RENNEN",
        "project_subtitle": "Ein Projekt mit vielen Perspektiven.",
        "project_text_1": "Wir arbeiten gemeinsam an Konstruktion, Fertigung, Marketing und Teamorganisation. Jede Aufgabe trägt dazu bei, dass unser Projekt auf und neben der Strecke funktioniert.",
        "project_text_2": "Unsere Arbeitsweise bleibt übersichtlich: Ziele festlegen, ausprobieren, auswerten und die nächste Version bauen.",
        "sponsors_page_title": "Sponsoren",
        "sponsors_header": "Unsere Partner",
        "sponsors_intro": "Noch am Anfang – aber mit großen Zielen. Wir suchen Unternehmen und Partner, die unser STEM-Racing-Projekt unterstützen möchten.",
        "sponsors_cta_title": "Werden Sie unser Partner.",
        "sponsors_cta_text": "Dieser Bereich ist für zukünftige Sponsoren und Partner reserviert.",
        "sponsors_why_title": "Gemeinsam Zukunft entwickeln.",
        "sponsors_why_text_1": "STEM Racing verbindet Technik, Konstruktion, Digitalisierung, Teamarbeit und Motorsport.",
        "sponsors_why_text_2": "Als neu gegründetes Team möchten wir unser Projekt von Anfang an professionell aufbauen und unsere Entwicklung transparent zeigen.",
        "sponsors_why_text_3": "Mit der Unterstützung von Partnern können wir unsere technischen Möglichkeiten erweitern und unser Projekt weiterentwickeln.",
        "sponsors_benefits_title": "Was wir bieten",
        "sponsors_benefit_1": "Präsentation unseres Projekts",
        "sponsors_benefit_2": "Team- und Projektpräsentationen",
        "sponsors_benefit_3": "Sichtbarkeit bei Veranstaltungen",
        "footer_navigation": "Navigation",
        "footer_impressum": "Impressum",
        "footer_map": "Jetzt anreisen",
        "footer_all_impressum": "Alle Impressumsangaben",
        "footer_team_email": "Team Email",
        "footer_phone": "Telefon",
        "copyright": "© 2026 A.C.E",
        "legal_notice": "Impressum",
        "legal_intro": "Kontakt und Anschrift unseres STEM-Racing-Teams.",
        "legal_title": "A.C.E",
        "legal_contact": "Kontakt",
        "legal_box_title": "A.C.E",
        "car_page_title": "Unser Auto",
        "car_header": "Unser Auto",
        "car_intro": "Vom ersten Entwurf bis zur Rennstrecke: jedes Detail entsteht mit einem klaren Ziel.",
        "car_section_label": "DESIGN & ENTWICKLUNG",
        "car_section_title": "Präzision, die Geschwindigkeit schafft.",
        "car_text_1": "Wir entwickeln einen kleinen, aerodynamischen Rennwagen und verbinden Konstruktion, Tests und Teamarbeit in einem gemeinsamen Prozess.",
        "car_text_2": "Jede Änderung wird begründet, geplant und überprüft. So wird aus einer Idee Schritt für Schritt ein zuverlässiges Rennauto.",
        "car_focus_title": "Unser Fokus",
        "car_focus_1": "Aerodynamik",
        "car_focus_2": "Leichtbau",
        "car_focus_3": "CAD & Prototyping",
        "car_focus_4": "Tests und Optimierung",
        "lang_de": "DE",
        "lang_en": "EN"
    },
    "en": {
        "site_name": "A.C.E",
        "home_aria_label": "A.C.E home page",
        "main_navigation": "Main navigation",
        "language_switch": "Language selection",
        "nav_home": "Home",
        "nav_about": "About us",
        "nav_team": "Team",
        "nav_car": "Our car",
        "nav_project": "Project",
        "nav_sponsors": "Sponsors",
        "nav_contact": "Contact",
        "skip_to_content": "Skip to content",
        "menu_open": "Open menu",
        "menu_close": "Close menu",
        "home_hero_description": "Technology. Teamwork. Innovation. Together we develop our own racing car.",
        "home_about": "About us",
        "home_car": "Our car",
        "section_project": "OUR PROJECT",
        "project_heading": "Engineering the Future",
        "home_project_intro": "We are a newly founded team and take part in the STEM Racing project.",
        "card_team_title": "TEAM",
        "card_team_text": "Get to know our team and our roles.",
        "card_team_link": "Learn more →",
        "card_engineering_title": "ENGINEERING",
        "card_engineering_text": "From the idea to CAD and the finished race car.",
        "card_engineering_link": "Our project →",
        "card_racing_title": "RACING",
        "card_racing_text": "Our goal is to build a fast, well-developed racing car.",
        "card_racing_link": "Our car →",
        "about_title": "About us",
        "about_header": "Who are we?",
        "about_intro": "We are a newly founded team from Einhard-Gymnasium Aachen and take part in the STEM Racing project.",
        "about_idea": "Our idea",
        "about_idea_text_1": "At STEM Racing we combine technology, design, creativity and teamwork.",
        "about_idea_text_2": "Our goal is to build a fast and well-developed racing car together while learning as much as possible about modern engineering.",
        "about_focus": "Our focus",
        "about_experience": "Our previous experience",
        "about_experience_text": "Through our previous experience with LEGO, technology and teamwork, we have already learned important steps for our project.",
        "team_page_title": "Team",
        "team_header": "The team",
        "team_section_label": "MEET THE TEAM",
        "team_section_title": "Our team",
        "team_photo": "TEAM PHOTO",
        "team_photo_subtitle": "Coming soon",
        "team_card_1_role": "Head of IT & Media, part of the design and research team",
        "team_card_2_role": "Team leader, part of the design and research team",
        "team_card_3_role": "Head of Production, part of the design and research team",
        "team_card_4_role": "Head of Graphics/Design and Social Media",
        "team_card_5_role": "Head of PR & Marketing",
        "team_philosophy": "Together, not alone.",
        "team_philosophy_text_1": "STEM Racing is more than just a race car. We work together on design, technology, planning and presentation.",
        "team_philosophy_text_2": "Each of us brings different interests, ideas and skills. This combination is what makes our team special.",
        "team_summary_title": "A.C.E",
        "team_summary_1": "5 team members",
        "team_summary_2": "STEM Racing 2026/27",
        "team_summary_3": "Einhard-Gymnasium Aachen",
        "team_summary_4": "Engineering & Racing",
        "contact_page_title": "Contact",
        "contact_intro": "Would you like to learn more about our team or our STEM Racing project? Please feel free to get in touch.",
        "contact_label": "CONTACT",
        "contact_heading": "Get in touch.",
        "contact_text": "Whether you have questions about our project, are interested in a partnership, or simply want to learn more about our team – we are happy to hear from you.",
        "contact_person_minh": "Contact: Minh Dao (IT & Media, design and research)",
        "contact_person_omar": "Contact: Omar Ahmed (Head of PR & Marketing)",
        "contact_person_tri": "Contact: Tri-Dung Tran (Graphics, Design & Social Media)",
        "contact_person_yashmith": "Contact: Yashmith Gettam (Team leader, design and research)",
        "contact_person_darius": "Contact: Darius Melian Flamand (Production, design and research)",
        "contact_write": "write",
        "contact_box_title": "A.C.E",
        "project_page_title": "Project",
        "project_header": "Engineering the Future",
        "project_intro": "STEM Racing combines technology, creativity and organisation in a real team project.",
        "project_phase_title": "Project phases",
        "project_phase_1": "Research and planning",
        "project_phase_2": "CAD and design",
        "project_phase_3": "Production and testing",
        "project_phase_4": "Presentation and racing",
        "project_label_1": "FROM IDEA TO RACE",
        "project_subtitle": "A project with many perspectives.",
        "project_text_1": "We work together on design, production, marketing and team organisation. Every task helps our project function on and off the track.",
        "project_text_2": "We keep our workflow clear: define goals, test, evaluate and build the next version.",
        "sponsors_page_title": "Sponsors",
        "sponsors_header": "Our partners",
        "sponsors_intro": "Still at the beginning – but with big goals. We are looking for companies and partners who want to support our STEM Racing project.",
        "sponsors_cta_title": "Become our partner.",
        "sponsors_cta_text": "This area is reserved for future sponsors and partners.",
        "sponsors_why_title": "Building the future together.",
        "sponsors_why_text_1": "STEM Racing combines technology, engineering, digitalisation, teamwork and motorsport.",
        "sponsors_why_text_2": "As a newly founded team, we want to build our project professionally from the start and present our progress transparently.",
        "sponsors_why_text_3": "With support from partners, we can expand our technical possibilities and continue developing our project.",
        "sponsors_benefits_title": "What we offer",
        "sponsors_benefit_1": "Presentation of our project",
        "sponsors_benefit_2": "Team and project presentations",
        "sponsors_benefit_3": "Visibility at events",
        "footer_navigation": "Navigation",
        "footer_impressum": "Legal notice",
        "footer_map": "Get directions",
        "footer_all_impressum": "All legal information",
        "footer_team_email": "Team email",
        "footer_phone": "Phone",
        "copyright": "© 2026 A.C.E",
        "legal_notice": "Legal notice",
        "legal_intro": "Contact details and address of our STEM Racing team.",
        "legal_title": "A.C.E",
        "legal_contact": "Contact",
        "legal_box_title": "A.C.E",
        "car_page_title": "Our car",
        "car_header": "Our car",
        "car_intro": "From the first concept to the race track: every detail is created with a clear goal.",
        "car_section_label": "DESIGN & DEVELOPMENT",
        "car_section_title": "Precision that creates speed.",
        "car_text_1": "We develop a small, aerodynamic racing car and combine design, testing and teamwork in one process.",
        "car_text_2": "Every change is explained, planned and checked. This turns an idea into a reliable race car step by step.",
        "car_focus_title": "Our focus",
        "car_focus_1": "Aerodynamics",
        "car_focus_2": "Lightweight design",
        "car_focus_3": "CAD & prototyping",
        "car_focus_4": "Testing and optimisation",
        "lang_de": "DE",
        "lang_en": "EN"
    }
}


@app.after_request
def persist_language(response):
    requested_lang = request.args.get("lang")
    if requested_lang in LANGUAGES:
        response.set_cookie(
            LANGUAGE_COOKIE_NAME,
            requested_lang,
            max_age=60 * 60 * 24 * 365,
            samesite="Lax",
            secure=True,
            httponly=True,
        )
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), geolocation=(), microphone=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.context_processor
def inject_language_state():
    current_lang = request.args.get("lang") or request.cookies.get(LANGUAGE_COOKIE_NAME) or DEFAULT_LANGUAGE
    if current_lang not in LANGUAGES:
        current_lang = DEFAULT_LANGUAGE

    def translate(key, default=None):
        return TRANSLATIONS.get(current_lang, TRANSLATIONS[DEFAULT_LANGUAGE]).get(key, default or key)

    return {
        "current_lang": current_lang,
        "t": translate,
        "language_options": ["de", "en"],
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/team")
def team():
    return render_template("team.html")


@app.route("/car")
def car():
    return render_template("car.html")


@app.route("/project")
def project():
    return render_template("project.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/impressum")
def impressum():
    return render_template("impressum.html")


@app.route("/sponsors")
def sponsors():
    return render_template("sponsors.html")


if __name__ == "__main__":
    app.run()