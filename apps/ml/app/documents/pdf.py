from __future__ import annotations

import io
import re
from collections import Counter

from pypdf import PdfReader


def extract_pdf(content: bytes) -> dict:
    if not content.startswith(b'%PDF'):
        raise ValueError('El archivo no tiene una firma PDF válida')
    try:
        reader = PdfReader(io.BytesIO(content))
    except Exception as exc:
        raise ValueError('El PDF está dañado o no se puede leer') from exc
    if reader.is_encrypted:
        raise ValueError('El PDF está cifrado; sube una copia sin contraseña')
    if len(reader.pages) > 500:
        raise ValueError('El PDF supera el límite de 500 páginas')

    raw_pages = [(page.extract_text() or '').strip() for page in reader.pages]
    if sum(len(text) for text in raw_pages) < 100:
        raise ValueError('El PDF no contiene texto seleccionable; el OCR no está disponible todavía')

    repeated = _repeated_edge_lines(raw_pages)
    segments = []
    full_text = []
    idx = 0
    for page_number, raw in enumerate(raw_pages, start=1):
        cleaned = _clean_page(raw, repeated)
        if not cleaned or _is_editorial_page(cleaned):
            continue
        full_text.append(cleaned)
        for paragraph in _chunk_text(cleaned):
            segments.append({'idx': idx, 'page_start': page_number, 'page_end': page_number, 'text': paragraph})
            idx += 1
    return {'page_count': len(reader.pages), 'full_text': '\n\n'.join(full_text), 'segments': segments}


def _repeated_edge_lines(pages: list[str]) -> set[str]:
    candidates = Counter()
    for text in pages:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines[:2] + lines[-2:]:
            if 3 < len(line) < 120:
                candidates[line] += 1
    threshold = max(3, len(pages) // 3)
    return {line for line, count in candidates.items() if count >= threshold}


def _clean_page(raw: str, repeated: set[str]) -> str:
    lines = [line.strip() for line in raw.splitlines()]
    kept = [
        line for line in lines
        if line and line not in repeated and not re.fullmatch(r'\d{1,4}', line)
        and not _is_editorial_line(line)
    ]
    text = ' '.join(kept)
    text = re.sub(r'/?bracket(?:left|right)(?:\.cap)?', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'(?<=\w)-\s+(?=[a-záéíóúñ])', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+([,.;:!?])', r'\1', text)
    text = re.sub(r'\s+', ' ', text).strip()

    def normalize_word(match: re.Match) -> str:
        word = match.group(0)
        inner_upper = sum(char.isupper() for char in word[1:])
        if any(char.islower() for char in word) and inner_upper >= 2:
            return word.lower()
        return word

    return re.sub(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{4,}', normalize_word, text)


def _is_editorial_line(line: str) -> bool:
    normalized = line.casefold().strip()
    patterns = (
        r'^hecho el dep[oó]sito legal', r'^dep[oó]sito legal', r'^isbn\s*:',
        r'^issn\s*:', r'^tiraje\s*:', r'^©', r'^derechos de (la|esta)',
        r'^e-?mail\s*:', r'^(tel[eé]f?\.?|telf\.?|tel[eé]fono|fax|p[aá]g\.? web)\s*:?\s*(\d|https?|\()',
        r'^(jir[oó]n|av\.?|avenida|calle|pasaje)\s+',
        r'^(diseño|cuidado) de la (car[aá]tula|edici[oó]n)',
        r'^imprenta\s+', r'^im[aá]genes de la car[aá]tula',
        r'^este volumen corresponde al tomo', r'^ley\s+\d+', r'^\d+\s+am[eé]rica latina$',
        r'issn\s*\d', r'(institut|lnstitut).*(andines|fran)',
        r'^fran[~çc]ais d[’\'e]tudes', r'^francisco mas[ií]as\s+\d+',
        r'^(cuadro|museo|propiedad|portada de la constituci[oó]n)\s+',
        r'(museo|[oó]leo sobre lienzo|retrato de don|propiedad de).*(/|museo|[oó]leo|retrato)',
        r'(retrato de don|propiedad de|[oó]leo de|galer[ií]a pict[oó]rica|portada de la constituci[oó]n)',
        r'^con el (patrocinio|apoyo)\s+', r'^fundaci[oó]n\s+',
    )
    return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in patterns)


def _is_editorial_page(text: str) -> bool:
    lowered = text.casefold()
    if lowered.count('tomo ') >= 8:
        return True
    editorial_markers = (
        'portada', 'coordinador editorial', 'patrocinio', 'editores',
        'depósito legal', 'isbn', 'imprenta', 'carátula', 'tiraje',
    )
    if sum(marker in lowered for marker in editorial_markers) >= 2:
        return True
    if len(text.split()) < 12:
        return True
    return False


def _chunk_text(text: str, target_words: int = 180, max_words: int = 250) -> list[str]:
    sentences = re.split(r'(?<=[.!?;:])\s+', text)
    chunks = []
    current: list[str] = []
    current_words = 0
    for sentence in sentences:
        words = sentence.split()
        if current and current_words + len(words) > max_words:
            chunks.append(' '.join(current).strip())
            current = [sentence]
            current_words = len(words)
        else:
            current.append(sentence)
            current_words += len(words)
        if current_words >= target_words:
            chunks.append(' '.join(current).strip())
            current = []
            current_words = 0
    if current:
        chunks.append(' '.join(current).strip())
    return [chunk for chunk in chunks if len(chunk.split()) >= 12]
