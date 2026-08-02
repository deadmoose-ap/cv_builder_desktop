"""Static section headings printed inside the CV itself.

These are the only words in an exported document that CV Builder writes: every
other line comes from what the user typed. They belong to the document, not to
the interface, so they follow the CV's own locale (`domain.locales`) and not
the language the application window happens to be in.

Latin and Cyrillic headings are stored already upper-cased because that is the
typographic convention the layout was designed around; CJK scripts have no
case, so their headings are stored as they should be read. `list_suffix` is the
punctuation that separates a bullet-list heading from its first item — CJK
convention is the fullwidth colon.
"""
from __future__ import annotations


LABELS: dict[str, dict[str, str]] = {
    "en": {
        "contact": "CONTACT",
        "core_skills": "CORE SKILLS",
        "summary": "SUMMARY",
        "experience": "EXPERIENCE",
        "key_responsibilities": "KEY RESPONSIBILITIES",
        "results": "RESULTS",
        "education": "EDUCATION",
        "page": "Page {number}",
        "list_suffix": ":",
    },
    "ru": {
        "contact": "КОНТАКТЫ",
        "core_skills": "КЛЮЧЕВЫЕ НАВЫКИ",
        "summary": "О СЕБЕ",
        "experience": "ОПЫТ РАБОТЫ",
        "key_responsibilities": "ОБЯЗАННОСТИ",
        "results": "РЕЗУЛЬТАТЫ",
        "education": "ОБРАЗОВАНИЕ",
        "page": "Стр. {number}",
        "list_suffix": ":",
    },
    "de": {
        "contact": "KONTAKT",
        "core_skills": "KERNKOMPETENZEN",
        "summary": "PROFIL",
        "experience": "BERUFSERFAHRUNG",
        "key_responsibilities": "HAUPTAUFGABEN",
        "results": "ERFOLGE",
        "education": "AUSBILDUNG",
        "page": "Seite {number}",
        "list_suffix": ":",
    },
    "es": {
        "contact": "CONTACTO",
        "core_skills": "COMPETENCIAS CLAVE",
        "summary": "PERFIL",
        "experience": "EXPERIENCIA",
        "key_responsibilities": "RESPONSABILIDADES",
        "results": "LOGROS",
        "education": "FORMACIÓN",
        "page": "Página {number}",
        "list_suffix": ":",
    },
    "fr": {
        "contact": "CONTACT",
        "core_skills": "COMPÉTENCES CLÉS",
        "summary": "PROFIL",
        "experience": "EXPÉRIENCE",
        "key_responsibilities": "RESPONSABILITÉS",
        "results": "RÉALISATIONS",
        "education": "FORMATION",
        "page": "Page {number}",
        "list_suffix": ":",
    },
    "ja": {
        "contact": "連絡先",
        "core_skills": "スキル",
        "summary": "概要",
        "experience": "職務経歴",
        "key_responsibilities": "主な業務",
        "results": "実績",
        "education": "学歴",
        "page": "{number} ページ",
        "list_suffix": "：",
    },
    "ko": {
        "contact": "연락처",
        "core_skills": "핵심 역량",
        "summary": "소개",
        "experience": "경력",
        "key_responsibilities": "주요 업무",
        "results": "성과",
        "education": "학력",
        "page": "{number} 페이지",
        "list_suffix": ":",
    },
    "zh-Hant": {
        "contact": "聯絡方式",
        "core_skills": "核心技能",
        "summary": "個人簡介",
        "experience": "工作經歷",
        "key_responsibilities": "主要職責",
        "results": "工作成果",
        "education": "教育背景",
        "page": "第 {number} 頁",
        "list_suffix": "：",
    },
    "zh-Hans": {
        "contact": "联系方式",
        "core_skills": "核心技能",
        "summary": "个人简介",
        "experience": "工作经历",
        "key_responsibilities": "主要职责",
        "results": "工作成果",
        "education": "教育背景",
        "page": "第 {number} 页",
        "list_suffix": "：",
    },
}


def labels(code: str | None) -> dict[str, str]:
    """Return the CV headings for a locale, falling back to English."""
    return LABELS.get(code or "", LABELS["en"])


def page_label(code: str | None, number: int) -> str:
    return labels(code)["page"].format(number=number)
