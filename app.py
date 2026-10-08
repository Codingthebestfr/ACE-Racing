import os
import re
import ssl
import time
import json
import hashlib
import secrets
import sqlite3
import urllib.request
import urllib.error
import unicodedata
from datetime import date, timedelta
from html.parser import HTMLParser
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

LANGUAGES = {"de", "en"}
DEFAULT_LANGUAGE = "de"
LANGUAGE_COOKIE_NAME = "site_lang"
CONTACT_SUBMISSIONS = {}
CONTACT_TOPICS = {"sponsoring", "engineering", "mentoring", "school", "press", "general"}
DEFAULT_CONTACT_RECIPIENT = "contact@ace-racing.de"
CONTACT_CONFIRMATION_TTL_SECONDS = 30 * 60

SEARCH_PAGES = (
    ("home", {"de": "Home", "en": "Home"}),
    ("about", {"de": "Über uns", "en": "About us"}),
    ("team", {"de": "Team", "en": "Team"}),
    ("car", {"de": "Auto & Projekt", "en": "Car & Project"}),
    ("roadmap", {"de": "Zeitplan", "en": "Roadmap"}),
    ("legacy", {"de": "Unsere Geschichte", "en": "Our history"}),
    ("media", {"de": "Media Center", "en": "Media Center"}),
    ("sponsors", {"de": "Sponsoren", "en": "Sponsors"}),
    ("contact", {"de": "Kontakt", "en": "Contact"}),
    ("impressum", {"de": "Impressum", "en": "Legal notice"}),
    ("datenschutz", {"de": "Datenschutz", "en": "Privacy"}),
)

SEARCH_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "for", "from", "how", "in", "is", "it", "of", "on", "or", "the", "to", "was", "we", "what", "where", "who", "with", "you",
    "aber", "als", "am", "an", "auf", "aus", "bei", "das", "der", "des", "die", "durch", "ein", "eine", "einer", "eines", "für", "im", "in", "ist", "mit", "oder", "und", "von", "was", "wer", "wie", "wir", "zu",
}

SEARCH_FAQS = {
    "de": (
        {"question": "Was ist STEM Racing?", "answer": "Ein internationaler, von Formula 1 unterstützter Bildungswettbewerb. Teams entwerfen, bauen, testen und präsentieren Miniatur-Rennwagen.", "keywords": "wettbewerb formel 1 rennwagen schule", "endpoint": "about"},
        {"question": "Wer ist ACE Racing?", "answer": "Wir sind das fünfköpfige STEM-Racing-Team des Einhard-Gymnasiums Aachen für die Saison 2026/27.", "keywords": "team mitglieder schüler aachen schule", "endpoint": "team"},
        {"question": "Was entwickelt das Team?", "answer": "Wir entwickeln einen kompakten Rennwagen. Dazu gehören CAD-Konstruktion mit Autodesk Fusion 360, 3D-Druck von Prototypen, Tests und Optimierung.", "keywords": "auto projekt konstruktion cad fusion 360 prototyping 3d druck", "endpoint": "car"},
        {"question": "Wie ist der aktuelle Projektstand?", "answer": "Das Team befindet sich in der frühen Projektphase und arbeitet an Recherche, Projektdokumentation, Konzeptideen und dem ersten Prototyp.", "keywords": "fortschritt status aktueller stand prototype prototyp", "endpoint": "car"},
        {"question": "Wie kann ich ACE Racing unterstützen?", "answer": "Auf der Sponsoren-Seite erklären wir, wie Unternehmen und Partner das STEM-Racing-Projekt unterstützen können.", "keywords": "sponsor partner sponsoring unterstützen", "endpoint": "sponsors"},
        {"question": "Wie kann ich das Team kontaktieren?", "answer": "Nutze das Kontaktformular oder die veröffentlichten Kontaktdaten auf der Kontaktseite.", "keywords": "email telefon nachricht kontakt erreichen", "endpoint": "contact"},
        {"question": "Welche Aufgaben hat das Team?", "answer": "Die Aufgaben umfassen Konstruktion, Produktion, IT, Forschung und Entwicklung sowie Grafik, Medien und Kommunikation.", "keywords": "rollen aufgaben it marketing grafik konstruktion produktion", "endpoint": "team"},
        {"question": "Wo ist ACE Racing zuhause?", "answer": "ACE Racing ist das Team des Einhard-Gymnasiums in Aachen.", "keywords": "adresse standort schule einhard", "endpoint": "impressum"},
    ),
    "en": (
        {"question": "What is STEM Racing?", "answer": "An international, Formula 1-endorsed education competition. Teams design, build, test and present miniature race cars.", "keywords": "competition formula 1 race car school", "endpoint": "about"},
        {"question": "Who is ACE Racing?", "answer": "We are the five-member STEM Racing team of Einhard-Gymnasium Aachen for the 2026/27 season.", "keywords": "team members students aachen school", "endpoint": "team"},
        {"question": "What is the team developing?", "answer": "We are developing a compact race car, including CAD design in Autodesk Fusion 360, 3D-printed prototypes, testing and optimisation.", "keywords": "car project engineering cad fusion 360 prototyping 3d print", "endpoint": "car"},
        {"question": "What is the current project status?", "answer": "The team is in the early project phase, working on research, documentation, concept ideas and its first prototype.", "keywords": "progress status prototype", "endpoint": "car"},
        {"question": "How can I support ACE Racing?", "answer": "The Sponsors page explains how companies and partners can support the STEM Racing project.", "keywords": "sponsor partner sponsorship support", "endpoint": "sponsors"},
        {"question": "How can I contact the team?", "answer": "Use the contact form or the published contact details on the Contact page.", "keywords": "email phone message contact reach", "endpoint": "contact"},
        {"question": "What does the team work on?", "answer": "Responsibilities include construction, production, IT, research and development, graphics, media and communication.", "keywords": "roles responsibilities it marketing graphics construction production", "endpoint": "team"},
        {"question": "Where is ACE Racing based?", "answer": "ACE Racing is the team of Einhard-Gymnasium in Aachen, Germany.", "keywords": "address location school einhard", "endpoint": "impressum"},
    ),
}


class _MainContentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_main = False
        self.ignored_depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "main":
            self.in_main = True
        elif self.in_main and tag in {"script", "style", "noscript"}:
            self.ignored_depth += 1

    def handle_endtag(self, tag):
        if tag == "main":
            self.in_main = False
        elif self.in_main and tag in {"script", "style", "noscript"} and self.ignored_depth:
            self.ignored_depth -= 1

    def handle_data(self, data):
        if self.in_main and not self.ignored_depth:
            self.parts.append(data)


def _main_text(rendered_page):
    parser = _MainContentParser()
    parser.feed(rendered_page)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def _search_tokens(value):
    normalized = unicodedata.normalize("NFKD", value.casefold().replace("ß", "ss"))
    plain_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return [token for token in re.findall(r"[a-z0-9]+", plain_text) if len(token) > 1 and token not in SEARCH_STOP_WORDS]


def _search_score(terms, title, text):
    title_tokens = _search_tokens(title)
    text_tokens = _search_tokens(text)
    return sum(title_tokens.count(term) * 8 + min(text_tokens.count(term), 5) for term in set(terms))


def _search_snippet(text, query):
    match = re.search(re.escape(query.strip()), text, re.IGNORECASE)
    if not match:
        for term in _search_tokens(query):
            match = re.search(re.escape(term), text, re.IGNORECASE)
            if match:
                break
    if not match:
        return text[:260] + ("…" if len(text) > 260 else "")

    start = max(0, match.start() - 90)
    end = min(len(text), start + 260)
    if start:
        start = text.find(" ", start, match.start()) + 1
    if end < len(text):
        end = text.rfind(" ", match.end(), end)
    return ("…" if start else "") + text[start:end].strip() + ("…" if end < len(text) else "")

TRANSLATIONS = {
    "de": {
        "site_name": "ACE",
        "home_aria_label": "ACE Racing am Einhard-Gymnasium Aachen, Startseite",
        "main_navigation": "Hauptnavigation",
        "language_switch": "Sprachauswahl",
        "nav_home": "Home",
        "nav_about": "Über uns",
        "nav_team": "Team",
        "nav_car": "Unser Auto",
        "nav_car_project": "Auto & Projekt",
        "nav_project": "Projekt",
        "nav_sponsors": "Sponsoren",
        "nav_contact": "Kontakt",
        "skip_to_content": "Zum Inhalt springen",
        "menu_open": "Menü öffnen",
        "menu_close": "Menü schließen",
        "home_hero_description": "Technik. Teamarbeit. Innovation. Gemeinsam entwickeln wir unseren eigenen Rennwagen.",
        "home_about": "Über uns",
        "home_car": "Unser Auto",
        "section_project": "UNSER PROJEKT",
        "project_heading": "Engineering the Future",
        "home_project_intro": "Wir sind ein neu gegründetes Team und nehmen am STEM-Racing-Projekt teil.",
        "card_team_title": "TEAM",
        "card_team_text": "Lernen Sie unser Team und unsere Aufgaben kennen.",
        "card_team_link": "Mehr erfahren",
        "card_engineering_title": "ENGINEERING",
        "card_engineering_text": "Von der Idee über CAD bis zum fertigen Rennwagen.",
        "card_engineering_link": "Unser Projekt",
        "card_racing_title": "RACING",
        "card_racing_text": "Unser Ziel: einen möglichst schnellen und gut entwickelten Rennwagen zu bauen.",
        "card_racing_link": "Unser Auto",
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
        "team_card_1_role": "Head of IT / Marketing & PR, Forschung & Entwicklung",
        "team_card_2_role": "Teamleader, Head of Construction",
        "team_card_3_role": "Head of Production / Forschung & Entwicklung",
        "team_card_4_role": "Head of Graphics/Designing & Media",
        "team_card_5_role": "Teil des Konstruktionsteams & Grafikdesign",
        "team_philosophy": "Gemeinsam statt allein.",
        "team_philosophy_text_1": "STEM Racing ist mehr als nur ein Rennwagen. Wir arbeiten gemeinsam an Konstruktion, Technik, Planung und Präsentation.",
        "team_philosophy_text_2": "Jeder von uns bringt eigene Interessen, Ideen und Fähigkeiten mit. Genau diese Kombination macht unser Team aus.",
        "team_summary_title": "ACE",
        "team_summary_1": "5 Teammitglieder",
        "team_summary_2": "STEM Racing 2026/27",
        "team_summary_3": "Einhard-Gymnasium Aachen",
        "team_summary_4": "Engineering & Racing",
        "contact_page_title": "Kontakt",
        "contact_intro": "Sie möchten mehr über unser Team oder unser STEM-Racing-Projekt erfahren? Schreiben Sie uns gerne.",
        "contact_label": "CONTACT",
        "contact_heading": "Kontaktieren Sie uns.",
        "contact_text": "Ob Fragen zu unserem Projekt, Interesse an einer Partnerschaft oder einfach Interesse an unserem Team – wir freuen uns über Ihre Nachricht.",
        "contact_person_minh": "Kontaktdaten: Minh Dao (Head of IT / Marketing & PR, Forschung & Entwicklung)",
        "contact_person_omar": "Kontaktdaten: Omar Ahmed (Teil des Konstruktionsteams & Grafikdesign)",
        "contact_person_tri": "Kontaktdaten: Tri-Dung Tran (Head of Graphics/Designing & Media)",
        "contact_person_yashmith": "Kontaktdaten: Yashmith Gettam (Teamleader, Head of Construction)",
        "contact_person_darius": "Kontaktdaten: Darius Melian Flamand (Head of Production / Forschung & Entwicklung)",
        "contact_write": "schreib",
        "contact_box_title": "ACE",
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
        "sponsors_intro": "Wir freuen uns über Unternehmen und Partner, die unser STEM-Racing-Projekt unterstützen möchten.",
        "sponsors_cta_title": "Werden Sie unser Partner.",
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
        "copyright": "© 2026 ACE Racing",
        "legal_notice": "Impressum",
        "legal_intro": "Kontakt und Anschrift unseres STEM-Racing-Teams.",
        "legal_title": "ACE Racing",
        "legal_contact": "Kontakt",
        "legal_box_title": "ACE Racing",
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
        "site_name": "ACE",
        "home_aria_label": "ACE Racing at Einhard-Gymnasium Aachen home page",
        "main_navigation": "Main navigation",
        "language_switch": "Language selection",
        "nav_home": "Home",
        "nav_about": "About us",
        "nav_team": "Team",
        "nav_car": "Our car",
        "nav_car_project": "Car & Project",
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
        "card_team_link": "Learn more",
        "card_engineering_title": "ENGINEERING",
        "card_engineering_text": "From the idea to CAD and the finished race car.",
        "card_engineering_link": "Our project",
        "card_racing_title": "RACING",
        "card_racing_text": "Our goal is to build a fast, well-developed racing car.",
        "card_racing_link": "Our car",
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
        "team_card_1_role": "Head of IT / Marketing & PR, Research & Development",
        "team_card_2_role": "Team leader, Head of Construction",
        "team_card_3_role": "Head of Production / Research & Development",
        "team_card_4_role": "Head of Graphics/Design and Media",
        "team_card_5_role": "Part of the construction & graphics team",
        "team_philosophy": "Together, not alone.",
        "team_philosophy_text_1": "STEM Racing is more than just a race car. We work together on design, technology, planning and presentation.",
        "team_philosophy_text_2": "Each of us brings different interests, ideas and skills. This combination is what makes our team special.",
        "team_summary_title": "ACE",
        "team_summary_1": "5 team members",
        "team_summary_2": "STEM Racing 2026/27",
        "team_summary_3": "Einhard-Gymnasium Aachen",
        "team_summary_4": "Engineering & Racing",
        "contact_page_title": "Contact",
        "contact_intro": "Would you like to learn more about our team or our STEM Racing project? Please feel free to get in touch.",
        "contact_label": "CONTACT",
        "contact_heading": "Get in touch.",
        "contact_text": "Whether you have questions about our project, are interested in a partnership, or simply want to learn more about our team – we are happy to hear from you.",
        "contact_person_minh": "Contact: Minh Dao (Head of IT / Marketing & PR, Research & Development)",
        "contact_person_omar": "Contact: Omar Ahmed (Part of the construction & graphics team)",
        "contact_person_tri": "Contact: Tri-Dung Tran (Head of Graphics/Design and Media)",
        "contact_person_yashmith": "Contact: Yashmith Gettam (Team leader, Head of Construction)",
        "contact_person_darius": "Contact: Darius Melian Flamand (Head of Production / Research & Development)",
        "contact_write": "write",
        "contact_box_title": "ACE",
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
        "sponsors_intro": "We welcome companies and partners who want to support our STEM Racing project.",
        "sponsors_cta_title": "Become our partner.",
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
        "copyright": "© 2026 ACE Racing",
        "legal_notice": "Legal notice",
        "legal_intro": "Contact details and address of our STEM Racing team.",
        "legal_title": "ACE Racing",
        "legal_contact": "Contact",
        "legal_box_title": "ACE Racing",
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


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()[:120]
    current_lang = request.args.get("lang") or request.cookies.get(LANGUAGE_COOKIE_NAME) or DEFAULT_LANGUAGE
    if current_lang not in LANGUAGES:
        current_lang = DEFAULT_LANGUAGE

    terms = _search_tokens(query)
    results = []

    if terms:
        for endpoint, titles in SEARCH_PAGES:
            page_response = app.make_response(app.view_functions[endpoint]())
            page_text = _main_text(page_response.get_data(as_text=True))
            title = titles[current_lang]
            score = _search_score(terms, title, page_text)
            if score:
                results.append({
                    "title": title,
                    "snippet": _search_snippet(page_text, query),
                    "url": url_for(endpoint, lang=current_lang),
                    "kind": "Seite" if current_lang == "de" else "Page",
                    "score": score,
                })

        for faq in SEARCH_FAQS[current_lang]:
            title = faq["question"]
            answer = faq["answer"]
            score = _search_score(terms, title, f"{answer} {faq['keywords']}")
            if score:
                results.append({
                    "title": title,
                    "snippet": answer,
                    "url": url_for(faq["endpoint"], lang=current_lang),
                    "kind": "Direkte Antwort" if current_lang == "de" else "Quick answer",
                    "score": score,
                })

        results.sort(key=lambda result: result["score"], reverse=True)
        results = results[:10]

    suggested_questions = [faq["question"] for faq in SEARCH_FAQS[current_lang]]
    return render_template(
        "search.html",
        search_query=query,
        search_results=results,
        suggested_questions=suggested_questions,
    )


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
    return redirect(url_for("car", _anchor="process"))


@app.route("/roadmap")
def roadmap():
    return render_template("roadmap.html")


@app.route("/legacy")
def legacy():
    return render_template("legacy.html")


def _week_label(weeks_offset, language):
    target_date = date.today() - timedelta(weeks=weeks_offset)
    iso_year, iso_week, _ = target_date.isocalendar()
    if language == "en":
        return f"Week {iso_week} / {iso_year}"
    return f"Woche {iso_week} / {iso_year}"


@app.route("/media")
def media():
    current_lang = request.args.get("lang") or request.cookies.get(LANGUAGE_COOKIE_NAME) or DEFAULT_LANGUAGE
    if current_lang not in LANGUAGES:
        current_lang = DEFAULT_LANGUAGE

    return render_template(
        "media.html",
        news_weeks={
            "01": _week_label(5, current_lang),
            "02": _week_label(2, current_lang),
            "03": _week_label(1, current_lang),
            "04": _week_label(0, current_lang),
        },
    )


@app.route("/contact")
@app.route("/contact", methods=["POST"])
def contact():
    if request.method == "GET":
        if request.args.get("sent") == "1":
            status = "success"
        elif not _contact_email_configured():
            status = "unavailable"
        else:
            status = None
        return render_template("contact.html", contact_status=status)

    if request.form.get("website"):
        language = request.args.get("lang")
        return redirect(url_for("contact", lang=language if language in LANGUAGES else DEFAULT_LANGUAGE))

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    organisation = request.form.get("organisation", "").strip()
    topic = request.form.get("topic", "")
    message_text = request.form.get("message", "").strip()
    valid_email = re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)
    if (
        not name
        or len(name) > 120
        or not valid_email
        or len(email) > 254
        or len(organisation) > 160
        or topic not in CONTACT_TOPICS
        or not message_text
        or len(message_text) > 5000
        or request.form.get("privacy_consent") != "yes"
    ):
        return render_template("contact.html", contact_status="invalid"), 400

    now = time.monotonic()
    client_ip = request.remote_addr or "unknown"
    recent = [stamp for stamp in CONTACT_SUBMISSIONS.get(client_ip, []) if now - stamp < 60]
    if len(recent) >= 3:
        CONTACT_SUBMISSIONS[client_ip] = recent
        return render_template("contact.html", contact_status="rate_limit"), 429
    recent.append(now)
    CONTACT_SUBMISSIONS[client_ip] = recent

    if not _contact_email_configured():
        return render_template("contact.html", contact_status="unavailable"), 503

    token = secrets.token_urlsafe(32)
    token_hash = _hash_contact_token(token)
    now_epoch = int(time.time())
    pending_payload = {
        "name": name,
        "email": email,
        "organisation": organisation,
        "topic": topic,
        "message": message_text,
    }
    _store_pending_contact(token_hash, pending_payload, now_epoch, now_epoch + CONTACT_CONFIRMATION_TTL_SECONDS)
    language = request.args.get("lang")
    if language not in LANGUAGES:
        language = DEFAULT_LANGUAGE
    public_base_url = os.environ.get("CONTACT_PUBLIC_URL", "https://ace-racing.de").rstrip("/")
    confirmation_url = f"{public_base_url}{url_for('confirm_contact', token=token, lang=language)}"
    try:
        _send_contact_email(
            email,
            "Confirm your message to ACE Racing",
            (
                f"Hello {name},\n\n"
                "Please confirm your email address by opening this link. "
                "Your message will only be sent to the ACE Racing team after confirmation:\n\n"
                f"{confirmation_url}\n\n"
                "This link expires in 30 minutes. If you did not submit this request, ignore this email."
            ),
        )
    except ContactDeliveryError:
        _delete_pending_contact(token_hash)
        return render_template("contact.html", contact_status="verification_failed"), 503

    return render_template("contact.html", contact_status="verification_pending"), 202


@app.route("/contact/confirm/<token>", methods=["GET", "POST"])
def confirm_contact(token):
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        return render_template("contact.html", contact_status="verification_invalid"), 400

    token_hash = _hash_contact_token(token)
    if request.method == "GET":
        pending = _get_pending_contact(token_hash, int(time.time()))
        if not pending or pending["status"] != "pending":
            return render_template("contact.html", contact_status="verification_invalid"), 400
        return render_template("contact.html", contact_status="confirm", confirmation_token=token)

    claim_status, pending_payload = _claim_pending_contact(token_hash, int(time.time()))
    if claim_status == "invalid":
        return render_template("contact.html", contact_status="verification_invalid"), 400
    if claim_status == "processing":
        return render_template("contact.html", contact_status="verification_processing"), 202

    try:
        _send_contact_email(
            os.environ.get("CONTACT_RECIPIENT", DEFAULT_CONTACT_RECIPIENT),
            f"ACE website inquiry: {pending_payload['topic']}",
            (
                f"Name: {pending_payload['name']}\n"
                f"Email: {pending_payload['email']}\n"
                f"Organisation: {pending_payload['organisation'] or '-'}\n"
                f"Topic: {pending_payload['topic']}\n\n"
                f"{pending_payload['message']}"
            ),
            reply_to=pending_payload["email"],
        )
    except ContactDeliveryError:
        _release_pending_contact(token_hash)
        return render_template("contact.html", contact_status="delivery_unavailable"), 503

    _delete_pending_contact(token_hash)
    language = request.args.get("lang")
    if language not in LANGUAGES:
        language = DEFAULT_LANGUAGE
    return redirect(url_for("contact", sent="1", lang=language))


class ContactDeliveryError(Exception):
    pass


def _contact_email_configured():
    return bool(
        os.environ.get("RESEND_API_KEY")
        and os.environ.get("CONTACT_RECIPIENT", DEFAULT_CONTACT_RECIPIENT)
    )


def _send_contact_email(recipient, subject, text, reply_to=None):
    resend_api_key = os.environ.get("RESEND_API_KEY")
    if not resend_api_key or not recipient:
        raise ContactDeliveryError("Contact email delivery is not configured.")

    email_data = {
        "from": "ACE Racing <contact@ace-racing.de>",
        "to": [recipient],
        "subject": subject,
        "text": text,
    }
    if reply_to:
        email_data["reply_to"] = reply_to

    api_request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(email_data).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ACE-Racing-Website/1.0 (+https://ace-racing.de)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(api_request, timeout=15) as response:
            response.read()
    except urllib.error.HTTPError as error:
        app.logger.error("RESEND EMAIL ERROR: HTTP %s", error.code)
        raise ContactDeliveryError("Resend rejected the email request.") from error
    except (OSError, urllib.error.URLError) as error:
        app.logger.exception("RESEND EMAIL ERROR")
        raise ContactDeliveryError("Resend could not be reached.") from error


def _contact_db_path():
    return os.environ.get(
        "CONTACT_DB_PATH",
        os.path.join(app.instance_path, "contact_submissions.sqlite3"),
    )


def _connect_contact_db():
    database_path = _contact_db_path()
    os.makedirs(os.path.dirname(os.path.abspath(database_path)), exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute(
        "CREATE TABLE IF NOT EXISTS pending_contact_messages ("
        "token_hash TEXT PRIMARY KEY, payload TEXT NOT NULL, expires_at INTEGER NOT NULL, "
        "status TEXT NOT NULL DEFAULT 'pending', processing_at INTEGER)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS pending_contact_messages_expiry "
        "ON pending_contact_messages (expires_at)"
    )
    with connection:
        connection.execute(
            "DELETE FROM pending_contact_messages WHERE expires_at <= ?",
            (int(time.time()),),
        )
    return connection


def _hash_contact_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _store_pending_contact(token_hash, payload, now, expires_at):
    connection = _connect_contact_db()
    try:
        with connection:
            connection.execute("DELETE FROM pending_contact_messages WHERE expires_at <= ?", (now,))
            connection.execute(
                "INSERT INTO pending_contact_messages (token_hash, payload, expires_at) VALUES (?, ?, ?)",
                (token_hash, json.dumps(payload), expires_at),
            )
    finally:
        connection.close()


def _get_pending_contact(token_hash, now):
    connection = _connect_contact_db()
    try:
        return connection.execute(
            "SELECT payload, status FROM pending_contact_messages WHERE token_hash = ? AND expires_at > ?",
            (token_hash, now),
        ).fetchone()
    finally:
        connection.close()


def _claim_pending_contact(token_hash, now):
    connection = _connect_contact_db()
    try:
        with connection:
            row = connection.execute(
                "SELECT payload, status, processing_at, expires_at "
                "FROM pending_contact_messages WHERE token_hash = ?",
                (token_hash,),
            ).fetchone()
            if not row or row["expires_at"] <= now:
                connection.execute("DELETE FROM pending_contact_messages WHERE token_hash = ?", (token_hash,))
                return "invalid", None
            if row["status"] == "processing" and row["processing_at"] and now - row["processing_at"] < 120:
                return "processing", None
            connection.execute(
                "UPDATE pending_contact_messages SET status = 'processing', processing_at = ? WHERE token_hash = ?",
                (now, token_hash),
            )
            return "claimed", json.loads(row["payload"])
    finally:
        connection.close()


def _release_pending_contact(token_hash):
    connection = _connect_contact_db()
    try:
        with connection:
            connection.execute(
                "UPDATE pending_contact_messages SET status = 'pending', processing_at = NULL WHERE token_hash = ?",
                (token_hash,),
            )
    finally:
        connection.close()


def _delete_pending_contact(token_hash):
    connection = _connect_contact_db()
    try:
        with connection:
            connection.execute("DELETE FROM pending_contact_messages WHERE token_hash = ?", (token_hash,))
    finally:
        connection.close()

@app.route("/impressum")
def impressum():
    return render_template("impressum.html")


@app.route("/datenschutz")
def datenschutz():
    return render_template("datenschutz.html")


@app.route("/sponsors")
def sponsors():
    return render_template("sponsors.html")


@app.route("/sitemap.xml")
def sitemap():
    pages = [
        "/",
        "/about",
        "/team",
        "/car",
        "/roadmap",
        "/legacy",
        "/media",
        "/sponsors",
        "/contact",
        "/impressum",
        "/datenschutz"
    ]

    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

    for page in pages:
        sitemap_xml += f"<url><loc>https://ace-racing.de{page}</loc></url>"

    sitemap_xml += "</urlset>"

    return sitemap_xml, 200, {"Content-Type": "application/xml"}


@app.route("/robots.txt")
def robots():
    return """User-agent: *
Allow: /

Sitemap: https://ace-racing.de/sitemap.xml
""", 200, {"Content-Type": "text/plain"}



if __name__ == "__main__":
    app.run()