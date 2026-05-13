# Additional Template Designs — Design

**Version**: 1.0
**Created**: 2026-05-12
**Author**: Orlando Bruno
**Status**: Draft
**Phase**: 2 of 3 (Design)

---

## 1. Directory Structure

```
templates/
├── classic/                        (existing — reference)
├── minimal/
│   ├── template.yaml
│   ├── cv.html
│   ├── cv.css
│   └── spec.yaml
└── modern/
    ├── template.yaml
    ├── cv.html
    ├── cv.css
    ├── spec.yaml
    └── assets/
        └── profile.jpg
```

Neither new template has a `cv.scss` file. Plain CSS is sufficient and avoids a build step dependency.

---

## 2. minimal Template Design

### 2.1 Visual Intent

Single-column, full page-width layout. No photo. No decorative colour. Section headings are uppercase labels with a 0.5pt hairline rule spanning the full content width. Typography is set in Arial at 10px body / 10px headings. White space is kept tight to maximise content density on A4.

The section heading rule is implemented via a two-cell `display: table` row: the heading text sits in a `width: 1%` cell (so it shrinks to its content), and the rule occupies the remaining width as a bottom-border on the second cell. This avoids `flexbox gap` and is WeasyPrint-safe.

### 2.2 HTML Structure — `templates/minimal/cv.html`

```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>{{ name }} - CV</title>
  </head>
  <body>

    <!-- HEADER: name, titles, contact (full width, no photo) -->
    <div class="header">
      <h1>{{ name }}</h1>
      {% if titles %}
      <p class="header__titles">{{ titles | join(' | ') }}</p>
      {% endif %}
      <p class="header__contact">
        {% if contact_info.location %}{{ contact_info.location }}{% endif %}
        {% if contact_info.phone %} | {{ contact_info.phone }}{% endif %}
        {% if contact_info.email %} | {{ contact_info.email }}{% endif %}
        {% if contact_info.website_link %} | <a href="{{ contact_info.website_link }}">{{ contact_info.website_link | base_url }}</a>{% endif %}
        {% if contact_info.github %} | <a href="{{ contact_info.github }}">github</a>{% endif %}
        {% if contact_info.linkedin %} | <a href="{{ contact_info.linkedin }}">linkedin</a>{% endif %}
      </p>
    </div>

    <!-- PROFESSIONAL PROFILE (optional) -->
    {% if profile %}
    <div class="section">
      <div class="section__heading-row">
        <h2 class="section__heading">PROFESSIONAL PROFILE</h2>
        <span class="section__rule"></span>
      </div>
      <p class="section__body">{{ profile }}</p>
    </div>
    {% endif %}

    <!-- CORE SKILLS (optional) -->
    {% if competencies_and_skills %}
    <div class="section">
      <div class="section__heading-row">
        <h2 class="section__heading">CORE SKILLS</h2>
        <span class="section__rule"></span>
      </div>
      <p class="section__body">
        {% for item in competencies_and_skills[:9] %}
        <strong>{{ item.competency }}:</strong> {{ item.skills | join(', ') }}{% if not loop.last %} &nbsp;&middot;&nbsp; {% endif %}
        {% endfor %}
      </p>
    </div>
    {% endif %}

    <!-- EDUCATION (required) -->
    <div class="section">
      <div class="section__heading-row">
        <h2 class="section__heading">EDUCATION</h2>
        <span class="section__rule"></span>
      </div>
      <table class="entry-table">
        {% for item in education %}
        <tr class="entry-table__row">
          <td class="entry-table__date">{{ item.year }}</td>
          <td class="entry-table__detail">
            <strong>{{ item.degree }}</strong><br />
            {{ item.institution }}{% if item.location %}, {{ item.location }}{% endif %}
            {% if item.grade %}<br />Grade: {{ item.grade }}{% endif %}
            {% if item.details %}<br />{{ item.details }}{% endif %}
          </td>
        </tr>
        {% endfor %}
      </table>
    </div>

    <!-- RELEVANT EXPERIENCE (required) -->
    <div class="section">
      <div class="section__heading-row">
        <h2 class="section__heading">RELEVANT EXPERIENCE</h2>
        <span class="section__rule"></span>
      </div>
      <table class="entry-table">
        {% for item in work_experience %}
        <tr class="entry-table__row">
          <td class="entry-table__date">{{ item.years }}</td>
          <td class="entry-table__detail">
            <strong>{{ item.position }}</strong> — {{ item.company }}{% if item.location %}, {{ item.location }}{% endif %}
            {% if item.roles %}
            <ul class="bullets">
              {% for role in item.roles %}
              <li>{{ role }}</li>
              {% endfor %}
            </ul>
            {% endif %}
          </td>
        </tr>
        {% endfor %}
      </table>
    </div>

    <!-- LANGUAGES (optional) -->
    {% if languages %}
    <div class="section">
      <div class="section__heading-row">
        <h2 class="section__heading">LANGUAGES</h2>
        <span class="section__rule"></span>
      </div>
      <p class="section__body">
        {% for item in languages %}
        {{ item.language }}: {{ item.level }}{% if not loop.last %} &nbsp;&middot;&nbsp; {% endif %}
        {% endfor %}
      </p>
    </div>
    {% endif %}

    <!-- CERTIFICATIONS (optional) -->
    {% if certifications %}
    <div class="section">
      <div class="section__heading-row">
        <h2 class="section__heading">CERTIFICATIONS</h2>
        <span class="section__rule"></span>
      </div>
      <ul class="cert-list">
        {% for item in certifications %}
        <li><strong>{{ item.name }}</strong> — {{ item.issuer }}, {{ item.year }}</li>
        {% endfor %}
      </ul>
    </div>
    {% endif %}

  </body>
</html>
```

### 2.3 CSS Layout Spec — `templates/minimal/cv.css`

Page size: A4. Margins: 1.5cm all sides. Font: Arial. Body 10px / line-height 1.35. Section headings 10px bold uppercase. Hairline rule 0.5pt solid `#aaaaaa`. No decorative colours.

The heading-row uses `display: table` / `display: table-cell` instead of flexbox, because WeasyPrint does not support `flexbox gap`.

```css
@page {
  size: A4;
  margin: 1.5cm;
}

*, *::before, *::after {
  box-sizing: border-box;
}

body {
  font-family: Arial, sans-serif;
  font-size: 10px;
  color: #1a1a1a;
  line-height: 1.35;
  margin: 0;
  padding: 0;
}

h1, h2, p, ul, ol, table {
  margin: 0;
  padding: 0;
}

ul {
  list-style: none;
}

a {
  color: inherit;
  text-decoration: none;
}

/* Header */

.header {
  margin-bottom: 14px;
  border-bottom: 1px solid #1a1a1a;
  padding-bottom: 10px;
}

.header h1 {
  font-size: 20px;
  font-weight: bold;
  letter-spacing: 0.5px;
}

.header__titles {
  font-size: 10px;
  color: #444444;
  margin-top: 2px;
}

.header__contact {
  font-size: 9px;
  color: #333333;
  margin-top: 4px;
}

/* Section */

.section {
  margin-bottom: 12px;
}

.section__heading-row {
  display: table;
  width: 100%;
  margin-bottom: 5px;
}

.section__heading {
  display: table-cell;
  font-size: 10px;
  font-weight: bold;
  letter-spacing: 0.8px;
  white-space: nowrap;
  padding-right: 8px;
  vertical-align: middle;
  width: 1%;
}

.section__rule {
  display: table-cell;
  border-bottom: 0.5pt solid #aaaaaa;
  vertical-align: middle;
  width: 99%;
}

.section__body {
  font-size: 10px;
  line-height: 1.4;
}

/* Entry table (education + experience) */

.entry-table {
  width: 100%;
  border-collapse: collapse;
}

.entry-table__date {
  width: 80px;
  font-size: 10px;
  font-weight: bold;
  white-space: nowrap;
  padding-right: 10px;
  padding-bottom: 7px;
  vertical-align: top;
}

.entry-table__detail {
  font-size: 10px;
  padding-bottom: 7px;
  vertical-align: top;
}

/* Bullets */

.bullets {
  list-style: disc;
  padding-left: 12px;
  margin-top: 3px;
}

.bullets li {
  padding-bottom: 2px;
}

/* Cert list */

.cert-list li {
  font-size: 10px;
  padding-bottom: 3px;
}
```

### 2.4 template.yaml — `templates/minimal/template.yaml`

```yaml
name: "Minimal"
slug: "minimal"
version: "1.0.0"
description: "Single-column, photo-free layout for text-dense professional CVs. A4 page size."
author: "Orlando Bruno"

html_file: "cv.html"
css_file: "cv.css"
spec_file: "spec.yaml"

page_size: "A4"
supports_photo: false

required_fields:
  - name
  - contact_info
  - education
  - work_experience

optional_fields:
  - titles
  - profile
  - contact_info.email
  - contact_info.phone
  - contact_info.location
  - contact_info.linkedin
  - contact_info.github
  - contact_info.website_link
  - competencies_and_skills
  - languages
  - certifications

layout_params:
  page_width_mm: 210
  page_height_mm: 297
  margin_min_mm: 10
  margin_max_mm: 15
  margin_step_mm: 1
  font_size_px: 10
  line_height: 1.35
  chars_per_line: 105
  header_fixed_lines: 4
  section_heading_lines: 1.5
  entry_header_lines: 1.5
  section_gap_lines: 0.6
  safety_margin: 0.95
  trim_rules:
    - field: work_experience
      strategy: remove_bullets_then_entries
      min_items: 1
      min_bullets: 0
    - field: education
      strategy: remove_items_from_end
      min_items: 1
    - field: certifications
      strategy: remove_items_from_end
      min_items: 0
    - field: profile
      strategy: truncate_words
      min_words: 30
```

### 2.5 spec.yaml — `templates/minimal/spec.yaml`

```yaml
template: minimal
description: >
  Minimal single-column CV. No photo. Full-width header with name, titles,
  and contact on one line. Skills rendered as inline grouped text.
  Education and experience use an 80px date column via HTML table.
  Languages and certifications are optional compact sections.

fields:

  name:
    required: true
    type: string
    description: Candidate's full name. Rendered as H1 in the header.
    constraints:
      max_chars: 55

  titles:
    required: false
    type: list[string]
    description: >
      Professional titles shown below the name, joined by " | ".
      All titles share one line.
    constraints:
      max_items: 3
      max_chars_per_item: 50

  contact_info:
    required: true
    type: object
    description: Contact details rendered inline in the header.
    fields:
      location:
        required: false
        type: string
        description: City and country.
        constraints:
          max_chars: 40
      phone:
        required: false
        type: string
        description: Phone number in any format.
        constraints:
          max_chars: 20
      email:
        required: false
        type: string
        description: Email address.
        constraints:
          max_chars: 60
      website_link:
        required: false
        type: url
        description: Personal website. Displayed as base URL only.
        constraints:
          max_chars: 80
      github:
        required: false
        type: url
        description: Full GitHub profile URL. Displayed as "github".
        constraints:
          max_chars: 80
      linkedin:
        required: false
        type: url
        description: Full LinkedIn profile URL. Displayed as "linkedin".
        constraints:
          max_chars: 80

  profile:
    required: false
    type: string
    description: >
      Short professional summary paragraph below the header.
      Tailor to the specific role and company.
    constraints:
      max_chars: 600
      recommended_chars: 380

  competencies_and_skills:
    required: false
    type: list[object]
    description: >
      Skills rendered as inline grouped text: "Competency: skill, skill · Competency: skill".
      No grid — competencies appear sequentially on contiguous lines.
    constraints:
      max_items: 9
    fields:
      competency:
        required: true
        type: string
        description: Category label shown before the skill list.
        constraints:
          max_chars: 35
      skills:
        required: true
        type: list[string]
        description: Tools or techniques under this competency.
        constraints:
          max_items: 8
          max_chars_per_item: 30

  education:
    required: true
    type: list[object]
    description: >
      Education entries in a two-column table: 80px date column, detail column.
      Most recent first.
    constraints:
      max_items: 5
    fields:
      year:
        required: true
        type: string
        description: Year or range. Fits the 80px date column.
        constraints:
          max_chars: 12
      degree:
        required: true
        type: string
        description: Degree or qualification title. Rendered bold.
        constraints:
          max_chars: 80
      institution:
        required: true
        type: string
        description: Name of the institution.
        constraints:
          max_chars: 80
      location:
        required: false
        type: string
        description: City and country.
        constraints:
          max_chars: 40
      grade:
        required: false
        type: string | null
        description: Grade or GPA. Set null to omit.
        constraints:
          max_chars: 20
      details:
        required: false
        type: string | null
        description: Specialisations, thesis, or honours. Set null to omit.
        constraints:
          max_chars: 120

  work_experience:
    required: true
    type: list[object]
    description: >
      Experience entries in a two-column table: 80px date column, detail column.
      Most recent first.
    constraints:
      max_items: 7
      recommended_items: 5
    fields:
      years:
        required: true
        type: string
        description: Year range (e.g. "2024 – Present"). Fits the 80px date column.
        constraints:
          max_chars: 14
      position:
        required: true
        type: string
        description: Job title. Rendered bold.
        constraints:
          max_chars: 60
      company:
        required: true
        type: string
        description: Employer name.
        constraints:
          max_chars: 60
      location:
        required: false
        type: string
        description: City and country (or "remote").
        constraints:
          max_chars: 40
      roles:
        required: false
        type: list[string]
        description: >
          Bullet-point responsibilities. Lead with a strong verb.
          One concise sentence per bullet.
        constraints:
          max_items: 5
          max_chars_per_item: 160

  languages:
    required: false
    type: list[object]
    description: >
      Languages rendered as an inline dot-separated list.
      Max 5 items fit cleanly on one line.
    constraints:
      max_items: 5
    fields:
      language:
        required: true
        type: string
        description: Language name.
        constraints:
          max_chars: 20
      level:
        required: true
        type: string
        description: Proficiency level (e.g. "C2 – Fluent", "Native").
        constraints:
          max_chars: 30

  certifications:
    required: false
    type: list[object]
    description: >
      Certifications rendered as a compact list.
      Most relevant or recent first.
    constraints:
      max_items: 6
    fields:
      name:
        required: true
        type: string
        description: Certification title.
        constraints:
          max_chars: 80
      issuer:
        required: true
        type: string
        description: Issuing organisation.
        constraints:
          max_chars: 60
      year:
        required: true
        type: string
        description: Year awarded.
        constraints:
          max_chars: 4

layout:
  page_size: A4
  page_margin: 1.5cm
  font: Arial
  font_size_body: 10px
  font_size_heading: 10px
  font_size_name: 20px
  date_col_width: 80px
  supports_photo: false
```

---

## 3. modern Template Design

### 3.1 Visual Intent

Two-region layout: a fixed-width left accent bar (`#1e3a5f`, 14px) and a right content pane occupying the remaining width. The accent bar is decorative and carries no text. Photo is optional; when present it renders as a 72px circle floated right inside the header. Skills are rendered as a flat dot-separated list of up to 15 individual items (competency groupings are not displayed). Section headings use a 1.5pt underline in the accent colour instead of a hairline rule.

WeasyPrint does not support `flexbox gap` or reliable CSS Grid in paged contexts. The two-region layout is implemented using an HTML `<table>` with `table-layout: fixed`: one fixed-width left cell forms the accent bar, and one fluid right cell contains all content. This is the most reliable WeasyPrint column layout strategy.

### 3.2 HTML Structure — `templates/modern/cv.html`

```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>{{ name }} - CV</title>
  </head>
  <body>

    <table class="page-layout">
      <tr>

        <!-- LEFT ACCENT BAR (decorative, no content) -->
        <td class="accent-bar"></td>

        <!-- RIGHT CONTENT PANE -->
        <td class="content-pane">

          <!-- Header -->
          <div class="header">
            {% if photo %}
            <div class="header__photo-wrap">
              <img src="{{ photo }}" alt="Profile picture" class="header__photo" />
            </div>
            {% endif %}
            <h1>{{ name }}</h1>
            {% if titles %}
            <p class="header__titles">{{ titles | join(' | ') }}</p>
            {% endif %}
            <p class="header__contact">
              {% if contact_info.location %}{{ contact_info.location }}{% endif %}
              {% if contact_info.phone %} | {{ contact_info.phone }}{% endif %}
              {% if contact_info.email %} | {{ contact_info.email }}{% endif %}
              {% if contact_info.website_link %} | <a href="{{ contact_info.website_link }}">{{ contact_info.website_link | base_url }}</a>{% endif %}
              {% if contact_info.github %} | <a href="{{ contact_info.github }}">github</a>{% endif %}
              {% if contact_info.linkedin %} | <a href="{{ contact_info.linkedin }}">linkedin</a>{% endif %}
            </p>
          </div>

          <!-- Professional Profile (optional) -->
          {% if profile %}
          <div class="section">
            <div class="section__heading-row">
              <h2 class="section__heading">PROFESSIONAL PROFILE</h2>
            </div>
            <p class="section__body">{{ profile }}</p>
          </div>
          {% endif %}

          <!-- Core Skills (optional) -->
          {% if competencies_and_skills %}
          <div class="section">
            <div class="section__heading-row">
              <h2 class="section__heading">CORE SKILLS</h2>
            </div>
            {% set ns = namespace(all_skills=[]) %}
            {% for item in competencies_and_skills %}
              {% for skill in item.skills %}
                {% set ns.all_skills = ns.all_skills + [skill] %}
              {% endfor %}
            {% endfor %}
            <p class="section__body">{{ ns.all_skills[:15] | join(' &middot; ') }}</p>
          </div>
          {% endif %}

          <!-- Education (required) -->
          <div class="section">
            <div class="section__heading-row">
              <h2 class="section__heading">EDUCATION</h2>
            </div>
            <table class="entry-table">
              {% for item in education %}
              <tr>
                <td class="entry-table__date">{{ item.year }}</td>
                <td class="entry-table__detail">
                  <strong>{{ item.degree }}</strong><br />
                  {{ item.institution }}{% if item.location %}, {{ item.location }}{% endif %}
                  {% if item.grade %}<br />Grade: {{ item.grade }}{% endif %}
                  {% if item.details %}<br />{{ item.details }}{% endif %}
                </td>
              </tr>
              {% endfor %}
            </table>
          </div>

          <!-- Relevant Experience (required) -->
          <div class="section">
            <div class="section__heading-row">
              <h2 class="section__heading">RELEVANT EXPERIENCE</h2>
            </div>
            <table class="entry-table">
              {% for item in work_experience %}
              <tr>
                <td class="entry-table__date">{{ item.years }}</td>
                <td class="entry-table__detail">
                  <strong>{{ item.position }}</strong> — {{ item.company }}{% if item.location %}, {{ item.location }}{% endif %}
                  {% if item.roles %}
                  <ul class="bullets">
                    {% for role in item.roles %}
                    <li>{{ role }}</li>
                    {% endfor %}
                  </ul>
                  {% endif %}
                </td>
              </tr>
              {% endfor %}
            </table>
          </div>

          <!-- Languages (optional) -->
          {% if languages %}
          <div class="section">
            <div class="section__heading-row">
              <h2 class="section__heading">LANGUAGES</h2>
            </div>
            <p class="section__body">
              {% for item in languages %}
              {{ item.language }}: {{ item.level }}{% if not loop.last %} &nbsp;&middot;&nbsp; {% endif %}
              {% endfor %}
            </p>
          </div>
          {% endif %}

          <!-- Certifications (optional) -->
          {% if certifications %}
          <div class="section">
            <div class="section__heading-row">
              <h2 class="section__heading">CERTIFICATIONS</h2>
            </div>
            <ul class="cert-list">
              {% for item in certifications %}
              <li><strong>{{ item.name }}</strong> — {{ item.issuer }}, {{ item.year }}</li>
              {% endfor %}
            </ul>
          </div>
          {% endif %}

        </td>
      </tr>
    </table>

  </body>
</html>
```

### 3.3 CSS Layout Spec — `templates/modern/cv.css`

Page size: Letter. Page margin: 0 (the page-layout table fills the page; internal padding is applied via `.content-pane`). Accent bar: 14px wide, background `#1e3a5f`. Section headings: 10px bold uppercase, underlined with a 1.5pt `#1e3a5f` border. Date column values rendered in `#1e3a5f`. Name rendered in `#1e3a5f`.

```css
@page {
  size: Letter;
  margin: 0;
}

*, *::before, *::after {
  box-sizing: border-box;
}

body {
  font-family: Arial, sans-serif;
  font-size: 10px;
  color: #1a1a1a;
  line-height: 1.4;
  margin: 0;
  padding: 0;
}

h1, h2, p, ul, ol, table {
  margin: 0;
  padding: 0;
}

ul {
  list-style: none;
}

a {
  color: inherit;
  text-decoration: none;
}

/* Page layout table */

.page-layout {
  width: 100%;
  height: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

/* Left accent bar */

.accent-bar {
  width: 14px;
  background-color: #1e3a5f;
  vertical-align: top;
}

/* Right content pane */

.content-pane {
  padding: 28px 20px 20px 22px;
  vertical-align: top;
}

/* Header */

.header {
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 2px solid #1e3a5f;
}

.header__photo-wrap {
  float: right;
  margin-left: 10px;
  margin-bottom: 6px;
  width: 72px;
  height: 72px;
  overflow: hidden;
  border-radius: 50%;
  border: 2px solid #1e3a5f;
}

.header__photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.header h1 {
  font-size: 22px;
  font-weight: bold;
  color: #1e3a5f;
  letter-spacing: 0.5px;
}

.header__titles {
  font-size: 10px;
  color: #555555;
  margin-top: 2px;
}

.header__contact {
  font-size: 9px;
  color: #444444;
  margin-top: 5px;
}

/* Section */

.section {
  margin-bottom: 12px;
}

.section__heading-row {
  margin-bottom: 5px;
  border-bottom: 1.5pt solid #1e3a5f;
  padding-bottom: 2px;
}

.section__heading {
  font-size: 10px;
  font-weight: bold;
  color: #1e3a5f;
  letter-spacing: 0.8px;
}

.section__body {
  font-size: 10px;
  line-height: 1.4;
}

/* Entry table (education + experience) */

.entry-table {
  width: 100%;
  border-collapse: collapse;
}

.entry-table__date {
  width: 84px;
  font-size: 10px;
  font-weight: bold;
  white-space: nowrap;
  padding-right: 10px;
  padding-bottom: 8px;
  vertical-align: top;
  color: #1e3a5f;
}

.entry-table__detail {
  font-size: 10px;
  padding-bottom: 8px;
  vertical-align: top;
}

/* Bullets */

.bullets {
  list-style: disc;
  padding-left: 12px;
  margin-top: 3px;
}

.bullets li {
  padding-bottom: 2px;
}

/* Cert list */

.cert-list li {
  font-size: 10px;
  padding-bottom: 3px;
}
```

### 3.4 template.yaml — `templates/modern/template.yaml`

```yaml
name: "Modern"
slug: "modern"
version: "1.0.0"
description: "Two-region layout with left slate-blue accent bar, optional photo, compact inline skills. US Letter."
author: "Orlando Bruno"

html_file: "cv.html"
css_file: "cv.css"
spec_file: "spec.yaml"

page_size: "Letter"
supports_photo: true

required_fields:
  - name
  - contact_info
  - education
  - work_experience

optional_fields:
  - titles
  - profile
  - photo
  - contact_info.email
  - contact_info.phone
  - contact_info.location
  - contact_info.linkedin
  - contact_info.github
  - contact_info.website_link
  - competencies_and_skills
  - languages
  - certifications

layout_params:
  page_width_mm: 215.9
  page_height_mm: 279.4
  margin_min_mm: 10
  margin_max_mm: 20
  margin_step_mm: 1
  font_size_px: 10
  line_height: 1.4
  chars_per_line: 98
  header_fixed_lines: 5
  section_heading_lines: 2
  entry_header_lines: 1.5
  section_gap_lines: 0.75
  safety_margin: 0.95
  trim_rules:
    - field: work_experience
      strategy: remove_bullets_then_entries
      min_items: 1
      min_bullets: 0
    - field: education
      strategy: remove_items_from_end
      min_items: 1
    - field: certifications
      strategy: remove_items_from_end
      min_items: 0
    - field: profile
      strategy: truncate_words
      min_words: 30
```

### 3.5 spec.yaml — `templates/modern/spec.yaml`

```yaml
template: modern
description: >
  Modern two-region CV. Left accent bar (14px, #1e3a5f) is purely decorative.
  Right content pane: optional circular photo (72px) floated right in the header,
  name in slate-blue H1, section headings underlined in slate-blue.
  Skills are rendered as a flat inline dot-separated list (max 15 items pooled
  across all competency groups). Date columns appear in the accent colour.

fields:

  name:
    required: true
    type: string
    description: Candidate's full name. Rendered as H1 in slate-blue.
    constraints:
      max_chars: 55

  titles:
    required: false
    type: list[string]
    description: >
      Professional titles shown below the name, joined by " | ".
      All titles share one line.
    constraints:
      max_items: 3
      max_chars_per_item: 50

  contact_info:
    required: true
    type: object
    description: Contact details rendered inline below titles.
    fields:
      location:
        required: false
        type: string
        description: City and country.
        constraints:
          max_chars: 40
      phone:
        required: false
        type: string
        description: Phone number.
        constraints:
          max_chars: 20
      email:
        required: false
        type: string
        description: Email address.
        constraints:
          max_chars: 60
      website_link:
        required: false
        type: url
        description: Personal website. Displayed as base URL only.
        constraints:
          max_chars: 80
      github:
        required: false
        type: url
        description: Full GitHub profile URL. Displayed as "github".
        constraints:
          max_chars: 80
      linkedin:
        required: false
        type: url
        description: Full LinkedIn profile URL. Displayed as "linkedin".
        constraints:
          max_chars: 80

  profile:
    required: false
    type: string
    description: >
      Short professional summary below the header.
      Tailor to the specific role and company.
    constraints:
      max_chars: 550
      recommended_chars: 380

  photo:
    required: false
    type: string
    description: >
      File path or URL to a profile photo. Falls back to assets/profile.jpg when omitted.
      JPEG or PNG. Square crop recommended — rendered as a 72px circle.
    constraints:
      note: Image rendered at 72x72px as a circle. Square crop required.

  competencies_and_skills:
    required: false
    type: list[object]
    description: >
      Skills section. All individual skills from all competency groups are pooled
      and rendered as a single flat dot-separated line (max 15 items).
      Competency labels are not displayed.
    constraints:
      max_items: 9
      max_toolkit_items: 15
    fields:
      competency:
        required: true
        type: string
        description: Category label (used for logical grouping; not rendered).
        constraints:
          max_chars: 35
      skills:
        required: true
        type: list[string]
        description: Tools or techniques under this competency.
        constraints:
          max_items: 8
          max_chars_per_item: 30

  education:
    required: true
    type: list[object]
    description: >
      Education entries in a two-column table: 84px date column in slate-blue, detail column.
      Most recent first.
    constraints:
      max_items: 5
    fields:
      year:
        required: true
        type: string
        description: Year or range. Fits the 84px date column.
        constraints:
          max_chars: 12
      degree:
        required: true
        type: string
        description: Degree or qualification title. Rendered bold.
        constraints:
          max_chars: 80
      institution:
        required: true
        type: string
        description: Name of the institution.
        constraints:
          max_chars: 80
      location:
        required: false
        type: string
        description: City and country.
        constraints:
          max_chars: 40
      grade:
        required: false
        type: string | null
        description: Grade or GPA. Set null to omit.
        constraints:
          max_chars: 20
      details:
        required: false
        type: string | null
        description: Specialisations, thesis, or honours. Set null to omit.
        constraints:
          max_chars: 120

  work_experience:
    required: true
    type: list[object]
    description: >
      Experience entries in a two-column table: 84px date column in slate-blue, detail column.
      Most recent first.
    constraints:
      max_items: 7
      recommended_items: 5
    fields:
      years:
        required: true
        type: string
        description: Year range (e.g. "2024 – Present"). Fits the 84px date column.
        constraints:
          max_chars: 14
      position:
        required: true
        type: string
        description: Job title. Rendered bold.
        constraints:
          max_chars: 60
      company:
        required: true
        type: string
        description: Employer name.
        constraints:
          max_chars: 60
      location:
        required: false
        type: string
        description: City and country (or "remote").
        constraints:
          max_chars: 40
      roles:
        required: false
        type: list[string]
        description: >
          Bullet-point responsibilities. Lead with a strong verb.
          One concise sentence per bullet.
        constraints:
          max_items: 5
          max_chars_per_item: 160

  languages:
    required: false
    type: list[object]
    description: >
      Languages rendered as an inline dot-separated list.
      Max 4 items fit cleanly on one line.
    constraints:
      max_items: 4
    fields:
      language:
        required: true
        type: string
        description: Language name.
        constraints:
          max_chars: 20
      level:
        required: true
        type: string
        description: Proficiency level (e.g. "C2 – Fluent", "Native").
        constraints:
          max_chars: 30

  certifications:
    required: false
    type: list[object]
    description: >
      Certifications rendered as a compact list.
      Most relevant or recent first.
    constraints:
      max_items: 6
    fields:
      name:
        required: true
        type: string
        description: Certification title.
        constraints:
          max_chars: 80
      issuer:
        required: true
        type: string
        description: Issuing organisation.
        constraints:
          max_chars: 60
      year:
        required: true
        type: string
        description: Year awarded.
        constraints:
          max_chars: 4

layout:
  page_size: Letter
  page_margin: 0
  content_pane_padding: "28px 20px 20px 22px"
  accent_bar_width: 14px
  accent_colour: "#1e3a5f"
  font: Arial
  font_size_body: 10px
  font_size_heading: 10px
  font_size_name: 22px
  photo_size: 72px
  date_col_width: 84px
  supports_photo: true
```

---

## 4. LayoutParams Values

The table below captures the key `layout_params` values for both new templates alongside `classic` for reference.

| Parameter | classic | minimal | modern |
|---|---|---|---|
| `page_width_mm` | 215.9 | 210 | 215.9 |
| `page_height_mm` | 279.4 | 297 | 279.4 |
| `margin_min_mm` | (not set) | 10 | 10 |
| `margin_max_mm` | (not set) | 15 | 20 |
| `margin_step_mm` | (not set) | 1 | 1 |
| `font_size_px` | 10 | 10 | 10 |
| `line_height` | 1.35 | 1.35 | 1.4 |
| `chars_per_line` | 95 | 105 | 98 |
| `header_fixed_lines` | 5 | 4 | 5 |
| `section_heading_lines` | 2 | 1.5 | 2 |
| `entry_header_lines` | 2 | 1.5 | 1.5 |
| `section_gap_lines` | 0.75 | 0.6 | 0.75 |
| `safety_margin` | 0.95 | 0.95 | 0.95 |

**`chars_per_line` rationale:**

- `minimal` (A4, 210mm wide, 1.5cm margins): printable width = 180mm. At Arial 10px, approximately 105 chars per line.
- `modern` (Letter, 215.9mm wide, ~20mm content-side margin, 14px accent bar ≈ 5mm removed from left): effective content width ≈ 176mm. At Arial 10px, approximately 98 chars per line.

**Trim rules (both templates):**

- `work_experience` — `remove_bullets_then_entries`: remove role bullets first, then whole entries, preserving minimum 1 entry.
- `education` — `remove_items_from_end`: drop trailing entries, preserving minimum 1 entry.
- `certifications` — `remove_items_from_end`: drop trailing entries, minimum 0 (section is optional).
- `profile` — `truncate_words`: trim from end, preserving minimum 30 words.

---

## 5. Cross-Template Compatibility

A profile YAML valid for `classic` is also valid for `minimal` and `modern` with the differences documented below.

### 5.1 Field Rendering Differences

| Field | classic | minimal | modern |
|---|---|---|---|
| `photo` | Rendered (90px circle) | Ignored entirely; no photo element in HTML | Optional; falls back to `assets/profile.jpg` if absent |
| `competencies_and_skills` | 3-column grid (max 9) + Toolkit line | Inline grouped text with competency labels | Flat dot-separated skill list (max 15 skills, labels not shown) |
| `languages` layout | Centred grid with separators | Inline dot-separated | Inline dot-separated |
| `languages` max_items | 4 | 5 | 4 |

### 5.2 Required Fields

All three templates share the same required fields: `name`, `contact_info`, `education`, `work_experience`. A profile satisfying `classic` will not fail required-field validation for `minimal` or `modern`.

### 5.3 Constraint Differences

| Field | classic max | minimal max | modern max |
|---|---|---|---|
| `name` max_chars | 60 | 55 | 55 |
| `profile` max_chars | 600 | 600 | 550 |
| `languages` max_items | 4 | 5 | 4 |

A profile built to `classic` constraints satisfies all `minimal` constraints. For `modern`, a `name` exceeding 55 chars or a `profile` exceeding 550 chars will render but may produce slight density overflow. No hard rendering failure occurs.

### 5.4 Template-Switch Procedure

To switch a `classic`-validated profile to either new template, only the `-t` flag changes:

```
uv run paperwork generate -p profile.yaml -t minimal -o cv-minimal.pdf
uv run paperwork generate -p profile.yaml -t modern  -o cv-modern.pdf
```

No profile YAML edits are required unless the `name` exceeds 55 chars or the `profile` text exceeds 550 chars (modern only).

---

**Last Updated**: 2026-05-12 by Orlando Bruno
**Next**: Phase 3 — Tasks (`03_tasks.md`)
