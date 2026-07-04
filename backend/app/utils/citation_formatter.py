"""
# mypy: disable-error-code="no-untyped-def"
引用格式化工具 — 支持 GB/T 7714 / APA 7th / MLA / Chicago / Vancouver / BibTeX。

输入：paper_meta dict（含 title / authors / journal / year / volume / issue / pages / doi）
输出：格式化后的引用字符串。
"""

from app.schemas.knowledge import CitationFormat


def _format_authors(authors: list, fmt: CitationFormat, all_caps: bool = False) -> str:
    """格式化作者列表。"""
    if not authors:
        return ""

    if fmt == CitationFormat.gbt7714:
        return ", ".join(authors) + "."

    elif fmt in (CitationFormat.apa, CitationFormat.chicago):
        # 输入为 "LastName FirstName" 格式
        formatted = []
        for a in authors:
            parts = a.split()
            if len(parts) >= 2:
                last = parts[0]  # 姓氏
                initials = "".join(f"{p[0]}." for p in parts[1:])
                formatted.append(f"{last}, {initials}")
            else:
                formatted.append(a)

        max_authors = 20 if fmt == CitationFormat.apa else 10
        if len(formatted) > max_authors:
            formatted = formatted[:max_authors - 1] + ["..."] + [formatted[-1]]

        if len(formatted) == 1:
            return formatted[0]
        elif len(formatted) == 2:
            return f"{formatted[0]}, & {formatted[1]}"
        else:
            return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"

    elif fmt == CitationFormat.vancouver:
        # 输入为 "LastName FirstName" 格式
        formatted = []
        for a in authors:
            parts = a.split()
            if len(parts) >= 2:
                last = parts[0]  # 姓氏
                initials = "".join(p[0] for p in parts[1:])
                formatted.append(f"{last} {initials}")
            else:
                formatted.append(a)
        if len(formatted) > 6:
            formatted = formatted[:6] + ["et al."]
        return ", ".join(formatted)

    elif fmt == CitationFormat.mla:
        if len(authors) == 1:
            return authors[0]  # type: ignore[no-any-return]
        elif len(authors) == 2:
            return f"{authors[0]}, and {authors[1]}"
        else:
            return f"{authors[0]}, et al."

    elif fmt == CitationFormat.bibtex:
        return " and ".join(authors)

    return ", ".join(authors)


def _format_bibtex_key(authors: list, year, title: str) -> str:
    """生成 BibTeX 引用键。"""
    first_author = authors[0].split()[0] if authors else "unknown"
    yr = str(year) if year else "0000"
    first_word = title.split()[0].lower() if title else "untitled"
    first_word = "".join(c for c in first_word if c.isalpha())
    return f"{first_author}{yr}{first_word}"


def format_citation(paper: dict, fmt: CitationFormat, index: int = 1) -> str:
    """格式化单篇文献引用。"""
    title = paper.get("title", "")
    authors_raw = paper.get("authors", [])
    if authors_raw and isinstance(authors_raw[0], dict):
        authors = [a.get("name", str(a)) for a in authors_raw]
    else:
        authors = authors_raw

    journal = paper.get("journal", "")
    year = paper.get("year", "")
    volume = paper.get("volume", "")
    issue = paper.get("issue", "")
    pages = paper.get("pages", "")
    doi = paper.get("doi", "")

    if fmt == CitationFormat.gbt7714:
        parts = []
        parts.append(f"[{index}]")
        if authors:
            parts.append(_format_authors(authors, fmt))
        parts.append(title + "[J].")
        if journal:
            parts.append(journal + ",")
        if year:
            parts.append(str(year) + ".")
        if volume:
            vol_str = f"{volume}"
            if issue:
                vol_str += f"({issue})"
            parts.append(vol_str + ":")
            if pages:
                parts.append(pages + ".")
        return " ".join(parts)

    elif fmt == CitationFormat.apa:
        parts = []
        author_str = _format_authors(authors, fmt)
        if author_str:
            parts.append(author_str)
        if year:
            parts.append(f"({year}).")
        parts.append(title + ".")
        journal_vol = journal
        if volume:
            journal_vol += f", {volume}"
            if issue:
                journal_vol += f"({issue})"
        if journal_vol:
            parts.append(journal_vol + ".")
        if pages:
            last_part = parts[-1] if parts else ""
            if last_part.endswith("."):
                parts[-1] = last_part[:-1] + f", {pages}."
            else:
                parts.append(f"{pages}.")
        if doi:
            parts.append(f"https://doi.org/{doi}")
        return " ".join(parts)

    elif fmt == CitationFormat.mla:
        parts = []
        if authors:
            parts.append(_format_authors(authors, fmt) + ".")
        parts.append(f'"{title}."')
        if journal:
            parts.append(journal + ",")
        if volume:
            parts.append(f"vol. {volume},")
        if issue:
            parts.append(f"no. {issue},")
        if year:
            parts.append(str(year) + ",")
        if pages:
            parts.append(f"pp. {pages}.")
        return " ".join(parts)

    elif fmt == CitationFormat.chicago:
        parts = []
        author_str = _format_authors(authors, fmt)
        if author_str:
            parts.append(author_str)
        if year:
            parts.append(f"{year}.")
        parts.append(f'"{title}."')
        journal_vol = journal
        if volume:
            journal_vol += f" {volume}"
            if issue:
                journal_vol += f" ({issue})"
        if journal_vol:
            parts.append(f"{journal_vol},")
        if journal_vol and pages:
            parts.append(f"{pages}.")
        if doi:
            parts.append(f"https://doi.org/{doi}")
        return " ".join(parts)

    elif fmt == CitationFormat.vancouver:
        parts = []
        author_str = _format_authors(authors, fmt)
        if author_str:
            parts.append(author_str + ".")
        parts.append(f"{title}.")
        if journal:
            parts.append(f"{journal}.")
        if year:
            yr_str = f"{year}"
            if volume:
                yr_str += f";{volume}"
                if issue:
                    yr_str += f"({issue})"
            yr_str += "."
            if pages:
                yr_str += f":{pages}."
            parts.append(yr_str)
        if doi:
            parts.append(f"doi:{doi}")
        return " ".join(parts)

    elif fmt == CitationFormat.bibtex:
        key = _format_bibtex_key(authors, year, title)
        lines = [f"@article{{{key},"]
        if authors:
            lines.append(f"  author = {{{_format_authors(authors, fmt)}}},")
        if title:
            lines.append(f"  title = {{{title}}},")
        if journal:
            lines.append(f"  journal = {{{journal}}},")
        if year:
            lines.append(f"  year = {{{year}}},")
        if volume:
            lines.append(f"  volume = {{{volume}}},")
        if issue:
            lines.append(f"  number = {{{issue}}},")
        if pages:
            lines.append(f"  pages = {{{pages}}},")
        if doi:
            lines.append(f"  doi = {{{doi}}},")
            lines.append(f"  url = {{https://doi.org/{doi}}},")
        abstract = paper.get("abstract", "")
        if abstract:
            lines.append(f"  abstract = {{{abstract}}},")
        lines.append("}")
        return "\n".join(lines)

    return ""
