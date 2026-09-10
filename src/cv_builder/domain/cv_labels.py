"""Static section headings printed inside the CV itself.

These are the only words in an exported document that CV Builder writes: every
other line comes from what the user typed. They belong to the document, not to
the interface, so they follow the CV's own locale (`domain.locales`) and not
the language the application window happens to be in.

Latin and Cyrillic section headings are stored already upper-cased because that
is the typographic convention of the document. Experience list subheads stay
in title case so they read as labels rather than another section heading.
"""
from __future__ import annotations


LABELS: dict[str, dict[str, str]] = {
    "en": {
        "contact": "CONTACT",
        "portfolio": "PORTFOLIO",
        "core_skills": "CORE SKILLS",
        "languages": "LANGUAGES",
        "summary": "SUMMARY",
        "experience": "EXPERIENCE",
        "key_responsibilities": "Key responsibilities",
        "results": "Results",
        "education": "EDUCATION",
        "present": "Present",
    },
    "ru": {
        "contact": "КОНТАКТЫ",
        "portfolio": "ПОРТФОЛИО",
        "core_skills": "КЛЮЧЕВЫЕ НАВЫКИ",
        "languages": "ЯЗЫКИ",
        "summary": "О СЕБЕ",
        "experience": "ОПЫТ РАБОТЫ",
        "key_responsibilities": "Обязанности",
        "results": "Результаты",
        "education": "ОБРАЗОВАНИЕ",
        "present": "настоящее время",
    },
    "de": {
        "contact": "KONTAKT",
        "portfolio": "PORTFOLIO",
        "core_skills": "KERNKOMPETENZEN",
        "languages": "SPRACHEN",
        "summary": "PROFIL",
        "experience": "BERUFSERFAHRUNG",
        "key_responsibilities": "Hauptaufgaben",
        "results": "Erfolge",
        "education": "AUSBILDUNG",
        "present": "heute",
    },
    "es": {
        "contact": "CONTACTO",
        "portfolio": "PORTFOLIO",
        "core_skills": "COMPETENCIAS CLAVE",
        "languages": "IDIOMAS",
        "summary": "PERFIL",
        "experience": "EXPERIENCIA",
        "key_responsibilities": "Responsabilidades",
        "results": "Logros",
        "education": "FORMACIÓN",
        "present": "actualidad",
    },
    "fr": {
        "contact": "CONTACT",
        "portfolio": "PORTFOLIO",
        "core_skills": "COMPÉTENCES CLÉS",
        "languages": "LANGUES",
        "summary": "PROFIL",
        "experience": "EXPÉRIENCE",
        "key_responsibilities": "Responsabilités",
        "results": "Réalisations",
        "education": "FORMATION",
        "present": "aujourd'hui",
    },
    "ja": {
        "contact": "連絡先",
        "portfolio": "ポートフォリオ",
        "core_skills": "スキル",
        "languages": "語学",
        "summary": "概要",
        "experience": "職務経歴",
        "key_responsibilities": "主な業務",
        "results": "実績",
        "education": "学歴",
        "present": "現在",
    },
    "ko": {
        "contact": "연락처",
        "portfolio": "포트폴리오",
        "core_skills": "핵심 역량",
        "languages": "언어",
        "summary": "소개",
        "experience": "경력",
        "key_responsibilities": "주요 업무",
        "results": "성과",
        "education": "학력",
        "present": "현재",
    },
    "zh-Hant": {
        "contact": "聯絡方式",
        "portfolio": "作品集",
        "core_skills": "核心技能",
        "languages": "語言能力",
        "summary": "個人簡介",
        "experience": "工作經歷",
        "key_responsibilities": "主要職責",
        "results": "工作成果",
        "education": "教育背景",
        "present": "至今",
    },
    "zh-Hans": {
        "contact": "联系方式",
        "portfolio": "作品集",
        "core_skills": "核心技能",
        "languages": "语言能力",
        "summary": "个人简介",
        "experience": "工作经历",
        "key_responsibilities": "主要职责",
        "results": "工作成果",
        "education": "教育背景",
        "present": "至今",
    },
}


def labels(code: str | None) -> dict[str, str]:
    """Return the CV headings for a locale, falling back to English."""
    return LABELS.get(code or "", LABELS["en"])
