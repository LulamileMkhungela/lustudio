#!/usr/bin/env python3
"""Rebuild cosmos-copy as the exact light Cosmos UI with LulaZel Hub tweaks.

The source tree in /tmp/site-source is a local Cosmos/Webflow fallback. This script
keeps its original Webflow classes and assets, removes the later dark adaptation
CSS, restores the light Cosmos palette, and applies only the requested brand and
top-navigation changes. It is safe to rerun.
"""
from __future__ import annotations

from pathlib import Path
from bs4 import BeautifulSoup, Comment, Tag
from copy import deepcopy
import html
import json
import re
import shutil

ROOT = Path('/home/user/lustudio')
SITE = ROOT / 'cosmos-copy'
SRC = Path('/tmp/site-source')
OWNER = Path('/tmp/my-new-site')
OWNER_JS = OWNER / 'assets/js'

CONTACT = {
    'email': 'mkhungela.l@gmail.com',
    'tel': '+27 83 719 5064',
    'tel_href': 'tel:+27837195064',
    'whatsapp': 'https://wa.me/27837195064',
    'calendly': 'https://calendly.com/lulamile_m/meet-lulamile',
    'site': 'https://lulazelhub.co.za/',
}

# ---------------------------------------------------------------------------
# 1. Reset to captured source and keep only the original Cosmos/Webflow CSS.
# ---------------------------------------------------------------------------
shutil.rmtree(SITE, ignore_errors=True)
shutil.copytree(SRC, SITE)

old_css = SITE / 'assets/css/cosmos.css'
site_css = SITE / 'assets/css/site.css'
if old_css.exists():
    old_css.rename(site_css)

# Owner-repository source folders that are not referenced by the Cosmos UI.
for rel in ['assets/owner/my-new-site/css', 'assets/owner/my-new-site/js', 'assets/owner/my-new-site/prompts']:
    shutil.rmtree(SITE / rel, ignore_errors=True)

# The captured file contains the original Webflow shared + main CSS, followed by
# a dark "UPLIFT"/Cosmos adaptation. Keep only the original Webflow portion.
css_text = site_css.read_text(encoding='utf-8')
marker = '/* Custom Embedded Styles from Cosmos Studio */'
if marker in css_text:
    css_text = css_text.split(marker, 1)[0].rstrip() + '\n'
# CSS lives in assets/css; /assets/... must resolve to ../...
css_text = re.sub(r'(?<![\w.])/assets/', '../', css_text)
site_css.write_text(css_text, encoding='utf-8')

# Localize every source reference in HTML/CSS/JS/XML/SVG text assets.
def localize_attr(value: str, prefix: str, is_page: bool) -> str:
    if not isinstance(value, str) or not value:
        return value
    def page_link(name: str) -> str:
        return name if is_page else 'pages/' + name
    if value.startswith('/assets/'):
        return prefix + 'assets/' + value[len('/assets/'):]
    if value.startswith('assets/'):
        return prefix + 'assets/' + value[len('assets/'):]
    if value.startswith('/pages/'):
        return page_link(value[len('/pages/'):])
    if value.startswith('pages/'):
        return page_link(value[len('pages/'):])
    if value in ('/', '/index.html'):
        return prefix + 'index.html'
    if value.startswith('/#'):
        return prefix + 'index.html' + value[1:]
    if value.startswith('/projects'):
        return page_link('works.html')
    if value.startswith('/services'):
        return page_link('services.html')
    if value.startswith('/industries'):
        return page_link('industries.html')
    if value.startswith('/about'):
        return page_link('about.html')
    if value.startswith('/blog'):
        return page_link('blog.html')
    if value.startswith('/contacts'):
        return page_link('contacts.html')
    return value

def localize_text(text: str, prefix: str, is_page: bool) -> str:
    text = re.sub(r'(?<![\w.])/assets/', prefix + 'assets/', text)
    text = text.replace('href="/"', 'href="' + prefix + 'index.html"')
    text = text.replace('href="/index.html"', 'href="' + prefix + 'index.html"')
    text = text.replace('href="/#', 'href="' + prefix + 'index.html#')
    text = text.replace('"/pages/', '"' + ('' if is_page else 'pages/'))
    text = text.replace("'/pages/", "'" + ('' if is_page else 'pages/'))
    text = text.replace('"/projects/', '"' + (('works.html' if is_page else 'pages/works.html') + '" data-cosmos-route="/projects/'))
    text = text.replace('action="/"', 'action="#"')
    return text

for path in sorted(SITE.rglob('*')):
    if not path.is_file():
        continue
    rel = path.relative_to(SITE).as_posix()
    suffix = path.suffix.lower()
    if suffix not in {'.html', '.css', '.js', '.xml', '.txt', '.svg'}:
        continue
    text = path.read_text(encoding='utf-8')
    is_page = rel.startswith('pages/') and suffix == '.html'
    prefix = '../' if is_page else ''
    if suffix == '.html':
        text = localize_text(text, prefix, is_page)
        text = text.replace('assets/css/cosmos.css', 'assets/css/site.css')
        text = text.replace('../assets/css/cosmos.css', '../assets/css/site.css')
    elif rel.startswith('assets/css/') and suffix == '.css' and path.name != 'site.css':
        text = re.sub(r'(?<![\w.])/assets/', '../', text)
    elif rel.startswith('assets/js/') and suffix == '.js':
        text = re.sub(r'(?<![\w.])/assets/', '../', text).replace('/pages/', '../../pages/')
    path.write_text(text, encoding='utf-8')

# ---------------------------------------------------------------------------
# 2. Exact geometric LulaZel Hub wordmark, built from inline vector letters.
# ---------------------------------------------------------------------------
H = 261.314
TOP = 24.3469
BOTTOM = 236.967
MID_TOP = 110.87
MID_BOTTOM = 140.768
LEFT = 29.9716
RIGHT = 58.87

OUTER = (
    'M6.9755 261.314H82.0955C85.9287 261.314 87.5392 260.759 87.9211 260.601'
    'C87.8453 260.441 88.6119 258.696 88.6119 253.939V7.37547'
    'C88.6119 3.01362 87.9983 1.42751 87.8453 1.18959L87.3089 0.634448'
    'C87.3847 0.634448 86.2348 0 82.1728 0H7.05216'
    'C3.0661 0 1.22646 0.555143 0.613304 0.872367'
    'C0.383313 1.58613 0 3.48946 0 7.29616V253.939'
    'C0 257.506 0.383313 259.569 0.613304 260.601'
    'C1.53312 260.917 3.52608 261.314 6.9755 261.314Z'
)

U_PATH = (
    'M7.12995 261.314H81.1001C84.9333 261.314 86.5423 260.759 86.9256 260.601'
    'C86.8498 260.441 87.6165 258.618 87.6165 253.939V0H58.8705V236.967H29.9716V0H0V253.939'
    'C0 257.586 0.383265 259.569 0.613553 260.601'
    'C1.68625 260.917 3.68008 261.314 7.12995 261.314Z'
)

L_PATH = (
    'M7.13 0H29.9716V236.967H80.563C84.2424 236.967 86.0822 237.364 86.772 237.602'
    'C87.0787 238.315 87.6152 240.14 87.6152 244.264V254.017'
    'C87.6152 258.141 87.0787 259.966 86.772 260.679'
    'C86.0822 260.917 84.2424 261.314 80.563 261.314H7.1288'
    'C3.1428 261.314 1.3031 260.917 0.6132 260.679'
    'C0.3833 259.647 0 257.586 0 254.017V7.296'
    'C0 3.489 0.3833 1.586 0.6132 0.872'
    'C1.3031 0.555 3.1428 0 7.1288 0Z'
)

Z_PATH = (
    'M0 0H88V24.3469H36.44L80.56 236.967H88V261.314H0V236.967H58.87L7.13 24.3469H0Z'
)

def compound(*holes: str) -> str:
    return OUTER + ''.join(holes)

GLYPHS = {
    'L': (L_PATH, False),
    'U': (U_PATH, False),
    'A': (compound(
        f'M{LEFT} {TOP}H{RIGHT}V{MID_TOP}H{LEFT}Z',
        f'M{LEFT} {MID_BOTTOM}H{RIGHT}V263H{LEFT}Z',
    ), True),
    'Z': (Z_PATH, False),
    'E': (compound(
        f'M{LEFT} {TOP}H90V{MID_TOP}H{LEFT}Z',
        f'M{LEFT} {MID_BOTTOM}H90V{BOTTOM}H{LEFT}Z',
    ), True),
    'H': (compound(
        f'M{LEFT} -1H{RIGHT}V{MID_TOP}H{LEFT}Z',
        f'M{LEFT} {MID_BOTTOM}H{RIGHT}V263H{LEFT}Z',
    ), True),
    'B': (compound(
        f'M29.8183 {TOP}H58.7161V{MID_TOP}H29.8183Z',
        f'M29.8183 {MID_BOTTOM}H58.7161V{BOTTOM}H29.8183Z',
    ), True),
}
WORD_1 = 'LULAZEL'
WORD_2 = 'HUB'

def glyph_svg(letter: str) -> str:
    d, evenodd = GLYPHS[letter]
    rule = ' fill-rule="evenodd"' if evenodd else ''
    return (
        '<svg class="logo-letter" xmlns="http://www.w3.org/2000/svg" width="100%" '
        f'viewBox="0 0 88 262" fill="none" aria-hidden="true"><path d="{d}" '
        f'fill="currentColor"{rule}/></svg>'
    )

def word_group(word: str, extra_class: str) -> str:
    letters = ''.join(glyph_svg(ch) for ch in word)
    return (
        f'<div class="logo-word {extra_class}" role="img" aria-label="{html.escape(word)}">'
        f'{letters}</div>'
    )

HERO_WORDMARK = (
    '<h1 class="sr-only lz-wordmark-title">LulaZel Hub</h1>' +
    word_group(WORD_1, 'is-brand-7') +
    word_group(WORD_2, 'is-brand-3')
)

def full_wordmark_svg() -> str:
    positions = []
    x = 0.0
    for ch in WORD_1:
        positions.append((x, ch))
        x += 117.0
    x += 35.0
    for ch in WORD_2:
        positions.append((x, ch))
        x += 117.0
    view_w = int(x - 29.0)
    groups = []
    for gx, ch in positions:
        d, evenodd = GLYPHS[ch]
        rule = ' fill-rule="evenodd"' if evenodd else ''
        groups.append(
            f'<g transform="translate({gx:.0f} 0)"><path d="{d}" fill="currentColor"{rule}/></g>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_w} 262" width="100%" '
        'role="img" aria-label="LulaZel Hub"><title>LulaZel Hub</title>'
        + ''.join(groups) + '</svg>'
    )

WORDMARK_SVG = full_wordmark_svg()
SMALL_LOGO_SVG = WORDMARK_SVG.replace('<svg ', '<svg class="menu_logo" ', 1)

brand = SITE / 'assets/brand'
brand.mkdir(parents=True, exist_ok=True)
(brand / 'lulazel-hub-logo.svg').write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n' + SMALL_LOGO_SVG + '\n', encoding='utf-8'
)
(brand / 'lulazel-hub-wordmark.svg').write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n' + WORDMARK_SVG + '\n', encoding='utf-8'
)

# ---------------------------------------------------------------------------
# 3. Light Cosmos theme, exact Webflow fonts, and small requested tweaks.
# ---------------------------------------------------------------------------
(SITE / 'assets/css/theme.css').write_text(r'''
/* Light Cosmos palette: restore the original Webflow variable values. */
:root{
  --_colors---primary--paper:#f6f6f4;
  --_colors---primary--black:#0f1011;
  --_colors---primary--white:#ffffff;
  --_colors---bg:var(--_colors---primary--paper);
  --_colors---txt:var(--_colors---primary--black);
  --_colors---grey--50:#f5f5f5;
  --_colors---grey--75:#e8e8e8;
  --_colors---grey--100:#dddddd;
  --_colors---grey--200:#b6b6b6;
  --_colors---grey--250:grey;
  --_colors---grey--300:#707070;
  --_colors---grey--400:#666666;
  --_colors---grey--500:#4b4c4d;
  --_colors---grey--550:#353636;
  --_colors---grey--600:#282829;
  --_colors---grey--650:#1c1d1f;
  --_colors---grey--700:#151718;
  --_colors---grey--800:#0f1011;
  --_colors---grey--900:#0a0a0a;
  --_colors---btn-inactive-bg:#ffffff;
  --_colors---btn-inactive-text:#666666;
  --_colors---btn-active-bg:#0f1011;
  --_colors---brn-active-text:#ffffff;
  --_colors---tag:#ffffff;
}
html,body{
  background:var(--_colors---primary--paper)!important;
  color:var(--_colors---primary--black)!important;
  font-family:Switzer,Inter,Arial,Helvetica,sans-serif!important;
}
.main-wrapper{background-color:var(--_colors---primary--paper)!important}
.section_home-header,.home-header_content{background-color:var(--_colors---primary--paper)!important}
.home-header_headings,.home-header_headings *{color:var(--_colors---primary--black)!important}
.home-header_service-text{color:var(--_colors---primary--black)!important;font-weight:500}
.home-header_service-line{border-bottom:1px dotted var(--_colors---grey--200)!important}
.home-header_content_sr{background-color:#0f1011!important;color:#fff!important;border-radius:2rem}
.home-header_video{opacity:1}
.navbar_component{
  background-color:#ffffff!important;
  border:1px solid rgba(15,16,17,.07)!important;
  box-shadow:0 2px 24px rgba(15,16,17,.05)!important;
}
.navbar_bg{background-image:none!important;opacity:0!important}
.navbar_link-text,.nav_contact-name,.home-header_position,.navbar_logo-anim_text,
.dropdown-link,.footer_link-text,.footer_copyright{color:var(--_colors---primary--black)!important}
.dropdown-list.w--open{
  background-color:#ffffff!important;
  border:1px solid var(--_colors---grey--100)!important;
  color:var(--_colors---primary--black)!important;
}
.button,.button-in,.button-solid{background-color:#0f1011!important;color:#ffffff!important}
.button_text,.button-solid{color:#ffffff!important}
.menu_content,.section_footer{background-color:#ffffff!important}
.menu_bg{background-color:rgba(15,16,17,.18)!important}
.w-mod-js:not(.w-mod-ix3) *{visibility:visible!important}
[style*="visibility:hidden"],[style*="visibility: hidden"]{visibility:visible!important}
''', encoding='utf-8')

(SITE / 'assets/css/fonts.css').write_text(r'''
/* Cosmos/Webflow typography. Browser-facing CDN URLs preserve the exact faces. */
@font-face{font-family:Switzer;src:url('https://cdn.prod.website-files.com/69f9c76884333229e651e7bc/69f9c76f84333229e651ea81_Switzer-Variable.woff2') format('woff2');font-weight:100 900;font-style:normal;font-display:swap}
@font-face{font-family:Inter;src:url('https://cdn.prod.website-files.com/69f9c76884333229e651e7bc/69f9c76f84333229e651e91b_InterVariable.woff2') format('woff2');font-weight:100 900;font-style:normal;font-display:swap}
@font-face{font-family:'Digital 7 Mono';src:url('https://cdn.prod.website-files.com/69f9c76884333229e651e7bc/6a2b431dff5a5c84fd2c5f0a_digital-7%20%5C(mono%5C).woff2') format('woff2');font-weight:400;font-style:normal;font-display:swap}
@font-face{font-family:Poppins;src:url('../owner/my-new-site/fonts/poppins-latin-400-normal.woff2') format('woff2');font-weight:400;font-display:swap}
@font-face{font-family:Poppins;src:url('../owner/my-new-site/fonts/poppins-latin-600-normal.woff2') format('woff2');font-weight:600;font-display:swap}
''', encoding='utf-8')

(SITE / 'assets/css/cosmos-tweaks.css').write_text(r'''
/* Requested tweaks only: light nav, Cosmos list items, logo-adjacent selector,
   geometric wordmark sizing, and Cosmos-style inner-page section layouts. */
html{scroll-behavior:smooth}
body{overflow-x:hidden}
a{color:inherit}
img,video,svg{max-width:100%}

/* Cosmos geometric wordmark */
.home-header_headings{gap:3%;align-items:stretch;color:#0f1011}
.home-header_headings .logo-word{width:auto;min-width:0;gap:2.5%}
.home-header_headings .logo-word.is-brand-7{width:70%;grid-template-columns:repeat(7,minmax(0,1fr))}
.home-header_headings .logo-word.is-brand-3{width:27%;grid-template-columns:1.675fr 1fr 1fr}
.home-header_headings .logo-letter{display:block;width:100%;height:auto}
.home-header_headings .logo-letter svg{display:block;width:100%;height:auto}
.home-header_headings .logo-letter path{fill:currentColor}
.lz-wordmark-title{position:absolute!important;width:1px!important;height:1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important}
.footer_content>svg{display:block;width:100%;height:auto;color:#0f1011;margin:2rem 0 .75rem}

/* White Cosmos navbar and the descriptor/logo beside it */
.navbar{z-index:100}
.navbar_component{display:flex;align-items:center;justify-content:space-between;gap:1rem;min-height:3.75rem}
.navbar_component .navbar-logo_wr{display:flex;align-items:center;gap:.75rem;flex:none;margin:0;color:#0f1011}
.navbar_component .menu_logo-wr{position:static;transform:none;display:flex;align-items:center;width:9.5rem;height:auto}
.navbar_component .menu_logo{display:block;width:100%;height:auto;color:#0f1011}
.navbar_component .menu_logo path{fill:currentColor}
.navbar_logo-wrap{margin:0}
.navbar_logo-anim{width:12.5rem;min-height:1.25rem;overflow:hidden}
.navbar_logo-anim_text{font-family:Inter,Switzer,Arial,sans-serif;font-size:.68rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;line-height:1.25;white-space:nowrap}
.navbar_links{margin-left:0;margin-right:0;flex:0 1 auto}
.navbar_links-wrap{gap:1.1rem;margin:0;flex-wrap:nowrap}
.navbar_link-text{font-family:Inter,Switzer,Arial,sans-serif;font-size:.88rem;font-weight:500;white-space:nowrap}
.navbar_contact{gap:.75rem;margin-left:0;flex:none}
.navbar-contact .navbar_talk-to{gap:.6rem}
.navbar_contact-pic{width:2.5rem;height:2.5rem;border-radius:.375rem;object-fit:cover}
.nav_contact-name{font-family:Inter,Switzer,Arial,sans-serif;font-size:.78rem;font-weight:600;white-space:nowrap}
.home-header_position{font-family:Inter,Switzer,Arial,sans-serif;font-size:.68rem;color:#666!important;white-space:nowrap}
.button-in{padding:.7rem 1rem;font-size:.78rem}
.button_text{font-family:Inter,Switzer,Arial,sans-serif;font-weight:600;white-space:nowrap}
.w-dropdown{position:relative}
.w-dropdown:hover>.dropdown-list,.w-dropdown.is-open>.dropdown-list{display:block!important}
.dropdown-list.w--open{position:absolute;top:calc(100% + .5rem);left:0;min-width:15rem;max-height:24rem;overflow:auto;border-radius:.75rem;box-shadow:0 1rem 3rem rgba(15,16,17,.09);padding:.5rem;z-index:1000}
.dropdown-link{font-family:Inter,Switzer,Arial,sans-serif;color:#0f1011;font-size:.875rem;padding:.55rem .75rem;border-radius:.5rem}
.dropdown-link:hover{background:#f5f5f5}
.dd-icon{color:#0f1011}

/* Logo-adjacent For You selector, styled like a light Cosmos dropdown */
.lz-view-switch{position:relative;flex:none;margin-left:.25rem;z-index:1002}
.lz-view-toggle{display:flex;align-items:center;justify-content:space-between;gap:.55rem;height:2.25rem;min-width:7.5rem;padding:0 .85rem;border:1px solid #dddddd;border-radius:999px;background:#ffffff;color:#0f1011;font-family:Inter,Switzer,Arial,sans-serif;font-size:.8rem;font-weight:500;line-height:1;cursor:pointer;white-space:nowrap}
.lz-view-toggle:hover,.lz-view-toggle:focus-visible{background:#f5f5f5;outline:none;border-color:#b6b6b6}
.lz-view-dot{display:inline-block;width:.42rem;height:.42rem;border-radius:50%;background:#0f1011;opacity:.9;flex:none}
.lz-view-chevron{width:.65rem;height:.4rem;opacity:.7;transition:transform .2s ease}
.lz-view-switch.is-open .lz-view-chevron{transform:rotate(180deg)}
.lz-view-menu{position:absolute;left:0;top:calc(100% + .5rem);width:15rem;padding:.5rem;border:1px solid #dddddd;border-radius:1rem;background:#ffffff;box-shadow:0 1rem 3rem rgba(15,16,17,.10)}
.lz-view-menu[hidden]{display:none}
.lz-view-option{display:flex;align-items:center;gap:.7rem;width:100%;padding:.65rem .75rem;border:0;border-radius:.65rem;background:transparent;color:#0f1011;font:inherit;text-align:left;cursor:pointer}
.lz-view-option:hover,.lz-view-option:focus-visible{background:#f5f5f5;outline:none}
.lz-view-option .lz-view-check{margin-left:auto;width:.9rem;height:.9rem;opacity:0;color:#0f1011}
.lz-view-option.is-selected .lz-view-check{opacity:1}
.lz-view-status{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}

/* Cosmos inner-page layouts */
.lz-page{padding-top:9rem;padding-bottom:6rem;background:#f6f6f4}
.lz-page-head{text-align:center;max-width:62rem;margin:0 auto}
.lz-clutch{display:inline-flex;align-items:center;gap:.5rem;color:#666;font-family:Inter,Switzer,Arial,sans-serif;font-size:.72rem;font-weight:500}
.lz-stars{color:#eb3b2e;letter-spacing:.08em;font-size:.8rem}
.lz-page-title{font-family:Switzer,Inter,Arial,sans-serif;color:#0f1011;font-size:clamp(3.25rem,6vw,6rem);line-height:1.02;letter-spacing:-.045em;font-weight:500;margin:1.5rem auto 0;max-width:56rem}
.lz-page-lead{max-width:46rem;margin:1.35rem auto 0;color:#666;font-family:Inter,Switzer,Arial,sans-serif;font-size:.94rem;line-height:1.65;font-weight:400}
.lz-page-actions{display:flex;justify-content:center;align-items:center;gap:1.25rem;flex-wrap:wrap;margin-top:2rem}
.lz-text-link{display:inline-flex;align-items:center;gap:.5rem;color:#0f1011;font-family:Inter,Switzer,Arial,sans-serif;font-size:.88rem;font-weight:600;text-decoration:none}
.lz-arrow-box{display:inline-flex;align-items:center;justify-content:center;width:1.35rem;height:1.35rem;border:1px solid #b6b6b6;border-radius:.25rem;font-size:.75rem}
.lz-stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:2rem;max-width:68rem;margin:5.5rem auto 0;text-align:center}
.lz-stat-number{font-family:Switzer,Inter,Arial,sans-serif;font-size:clamp(4.5rem,8vw,10rem);font-weight:500;line-height:.9;letter-spacing:-.06em;color:#0f1011}
.lz-stat-label{margin:.85rem auto 0;max-width:15rem;color:#666;font-family:Inter,Switzer,Arial,sans-serif;font-size:.78rem;line-height:1.45}
.lz-section{padding-top:6rem;padding-bottom:2rem}
.lz-section-label{text-align:center;color:#707070;font-family:Inter,Switzer,Arial,sans-serif;font-size:.68rem;font-weight:600;letter-spacing:.16em;text-transform:uppercase}
.lz-section-title{font-family:Switzer,Inter,Arial,sans-serif;font-size:clamp(2.5rem,4vw,4rem);font-weight:500;line-height:1.05;letter-spacing:-.035em;color:#0f1011;text-align:center;max-width:52rem;margin:1rem auto 0}
.lz-service-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;max-width:76rem;margin:3rem auto 0}
.lz-service-card{display:flex;flex-direction:column;justify-content:space-between;min-height:15rem;padding:1.75rem;border:1px solid #e3e3e1;border-radius:1.25rem;background:#fff;transition:transform .25s ease,box-shadow .25s ease}
.lz-service-card:hover{transform:translateY(-3px);box-shadow:0 1rem 2.5rem rgba(15,16,17,.07)}
.lz-service-num{font-family:'Digital 7 Mono',Inter,monospace;font-size:.8rem;color:#707070;letter-spacing:.08em}
.lz-service-card h3{font-family:Switzer,Inter,Arial,sans-serif;font-size:1.5rem;font-weight:500;letter-spacing:-.02em;color:#0f1011;margin:2.5rem 0 .75rem}
.lz-service-card p{font-family:Inter,Switzer,Arial,sans-serif;font-size:.86rem;line-height:1.6;color:#666;margin:0}
.lz-tag-row{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:1.25rem}
.lz-tag{padding:.35rem .65rem;border-radius:999px;background:#f5f5f5;color:#666;font-family:Inter,Switzer,Arial,sans-serif;font-size:.7rem}
.lz-work-filters{display:flex;justify-content:space-between;align-items:center;gap:1rem;max-width:62rem;margin:3.5rem auto 0;flex-wrap:wrap}
.lz-filter-group{display:flex;gap:1rem;flex-wrap:wrap}
.lz-filter-pill,.lz-search{min-height:3rem;border:1px solid #e3e3e1;border-radius:.75rem;background:#fff;color:#0f1011;font-family:Inter,Switzer,Arial,sans-serif;font-size:.85rem;font-weight:500;box-shadow:0 2px 12px rgba(15,16,17,.03)}
.lz-filter-pill{min-width:13rem;padding:0 1rem;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' fill='none'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%230f1011' stroke-width='1.8' stroke-linecap='round'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 1rem center}
.lz-search{display:flex;align-items:center;gap:.65rem;min-width:17rem;padding:0 1rem}
.lz-search svg{width:1rem;height:1rem;flex:none;color:#666}
.lz-search input{width:100%;border:0;background:transparent;color:#0f1011;font:inherit;outline:none}
.lz-search input::placeholder{color:#8a8a8a}
.lz-work-list{max-width:68rem;margin:3.5rem auto 0}
.lz-work-card{margin-bottom:5.5rem}
.lz-work-card.is-hidden{display:none}
.lz-work-media{position:relative;aspect-ratio:16/9;border-radius:1.5rem;overflow:hidden;background:#0f1011}
.lz-work-media img{display:block;width:100%;height:100%;object-fit:cover}
.lz-work-badge{position:absolute;top:1rem;left:1rem;display:flex;align-items:center;gap:.65rem;padding:.5rem .75rem;border-radius:999px;background:rgba(255,255,255,.18);backdrop-filter:blur(10px);color:#fff;font-family:Inter,Switzer,Arial,sans-serif;font-size:.78rem;font-weight:500}
.lz-work-badge img{width:1.6rem;height:1.6rem;border-radius:.25rem;object-fit:cover}
.lz-work-badge span{opacity:.55;width:1px;height:1rem;background:rgba(255,255,255,.5)}
.lz-work-badge strong{font-weight:600}
.lz-work-meta{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1rem;font-family:Inter,Switzer,Arial,sans-serif}
.lz-work-meta small{display:block;color:#707070;font-size:.65rem;letter-spacing:.14em;text-transform:uppercase;margin-bottom:.25rem}
.lz-work-meta span{color:#0f1011;font-size:.86rem;font-weight:600}
.lz-work-meta .right{text-align:right}
.lz-empty-works{display:none;text-align:center;color:#666;font-family:Inter,Switzer,Arial,sans-serif;padding:4rem 0}
.lz-empty-works.is-visible{display:block}
.lz-text-grid{display:grid;grid-template-columns:1fr 1fr;gap:3rem;max-width:68rem;margin:3rem auto 0}
.lz-text-block h2{font-family:Switzer,Inter,Arial,sans-serif;font-size:2rem;font-weight:500;letter-spacing:-.03em;color:#0f1011;margin:0 0 .75rem}
.lz-text-block p{font-family:Inter,Switzer,Arial,sans-serif;color:#666;font-size:.92rem;line-height:1.7;margin:0}
.lz-contact-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.8rem;max-width:76rem;margin:2.5rem auto 0}
.lz-contact-link{display:block;padding:1.25rem;border:1px solid #e3e3e1;border-radius:1rem;background:#fff;color:#0f1011;text-decoration:none;font-family:Inter,Switzer,Arial,sans-serif}
.lz-contact-link span{display:block;margin-bottom:.4rem;color:#707070;font-size:.65rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase}
.lz-contact-link strong{font-size:.9rem;font-weight:600;line-height:1.5;word-break:break-word}
.lz-testimonial-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;max-width:76rem;margin:2.5rem auto 0}
.lz-testimonial-card{padding:1.75rem;border:1px solid #e3e3e1;border-radius:1rem;background:#fff}
.lz-testimonial-card blockquote{margin:0 0 1.25rem;color:#0f1011;font-family:Switzer,Inter,Arial,sans-serif;font-size:1rem;line-height:1.5}
.lz-testimonial-card strong{display:block;font-family:Inter,Switzer,Arial,sans-serif;font-size:.88rem;color:#0f1011}
.lz-testimonial-card small{display:block;margin-top:.25rem;color:#707070;font-size:.72rem;line-height:1.5;font-family:Inter,Switzer,Arial,sans-serif}
.lz-time-note{text-align:center;color:#707070;font-family:Inter,Switzer,Arial,sans-serif;font-size:.78rem;margin-top:2rem}

/* Mobile menu and responsive Cosmos behaviour */
.menu.is-open{display:flex!important;z-index:1100;background:#f6f6f4;min-height:100vh;overflow:auto}
.menu.is-open .menu_content{min-height:calc(100vh - 1.5rem);padding:1.5rem}
.menu.is-open+.menu_bg{display:block!important}
.menu.is-open .menu_logo-wrap{display:flex!important;align-items:center;width:12rem;margin-bottom:2rem}
.menu.is-open .menu_logo-wrap .menu_logo{width:100%;height:auto;color:#0f1011}
.menu.is-open .menu_logo-wrap .menu_logo path{fill:currentColor}
.menu.is-open .menu_links-wrap{display:flex;flex-direction:column;gap:.25rem}
.menu.is-open .menu_link{padding:1rem 0;border-bottom:1px dotted #b6b6b6}
.menu.is-open .lz-view-switch{margin:0 0 1.5rem}
@media(max-width:1400px){
  .navbar_logo-anim{display:none}
  .navbar_links-wrap{gap:.75rem}
  .navbar_link-text{font-size:.8rem}
}
@media(max-width:1100px){
  .navbar-contact{display:none}
}
@media(max-width:991px){
  .navbar_links{display:none}
  .navbar-contact{display:none}
  .navbar_menu-open{display:flex}
  .lz-view-switch{display:block;margin-left:auto}
  .navbar_component .navbar-logo_wr{margin-right:auto}
  .lz-service-grid,.lz-testimonial-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .lz-contact-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .lz-text-grid{grid-template-columns:1fr}
}
@media(max-width:700px){
  .home-header_headings{gap:2%}
  .home-header_headings .logo-word.is-brand-7{width:73%}
  .home-header_headings .logo-word.is-brand-3{width:25%}
  .lz-page{padding-top:7rem}
  .lz-stats{grid-template-columns:1fr;gap:2.5rem}
  .lz-service-grid,.lz-testimonial-grid,.lz-contact-grid{grid-template-columns:1fr}
  .lz-work-filters{flex-direction:column;align-items:stretch}
  .lz-filter-group{flex-direction:column}
  .lz-filter-pill,.lz-search{width:100%}
  .lz-work-meta{grid-template-columns:1fr}
  .lz-work-meta .right{text-align:left}
}
''', encoding='utf-8')

(SITE / 'assets/js/site.js').write_text(r'''
(function () {
  "use strict";
  var root = document.documentElement;

  /* Light Cosmos dropdowns. */
  document.querySelectorAll('.w-dropdown').forEach(function (dd) {
    var toggle = dd.querySelector('.w-dropdown-toggle');
    var list = dd.querySelector('.dropdown-list');
    if (!toggle || !list) return;
    function open() { list.classList.add('w--open'); dd.classList.add('is-open'); }
    function close() { list.classList.remove('w--open'); dd.classList.remove('is-open'); }
    dd.addEventListener('mouseenter', open);
    dd.addEventListener('mouseleave', close);
    toggle.addEventListener('click', function (e) {
      e.preventDefault();
      dd.classList.contains('is-open') ? close() : open();
    });
  });

  /* Mobile menu. */
  var openBtn = document.querySelector('.navbar_menu-open');
  var menu = document.querySelector('.menu');
  var closeBtn = document.querySelector('.menu_close');
  var menuBg = document.querySelector('.menu_bg');
  function setMenu(open) {
    if (!menu || !openBtn) return;
    menu.classList.toggle('is-open', open);
    openBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (menuBg) menuBg.style.display = open ? 'block' : '';
  }
  if (openBtn) openBtn.addEventListener('click', function () { setMenu(!menu.classList.contains('is-open')); });
  if (closeBtn) closeBtn.addEventListener('click', function () { setMenu(false); });
  if (menuBg) menuBg.addEventListener('click', function () { setMenu(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });

  /* For You is the default Cosmos view; other options stay pending. */
  var switches = Array.prototype.slice.call(document.querySelectorAll('[data-lz-view-switch]'));
  var status = document.getElementById('lz-view-status');
  var labels = { marketing:'For Marketing Teams', you:'For You', tech:'For Tech', 'else':'Something Else' };
  function closeAll() {
    switches.forEach(function (sw) {
      sw.classList.remove('is-open');
      var toggle = sw.querySelector('[data-view-toggle]');
      var menu = sw.querySelector('.lz-view-menu');
      if (toggle) toggle.setAttribute('aria-expanded', 'false');
      if (menu) menu.hidden = true;
    });
  }
  function applyView(view, persist) {
    if (!labels[view]) view = 'you';
    switches.forEach(function (sw) {
      var label = sw.querySelector('[data-view-label]');
      var toggle = sw.querySelector('[data-view-toggle]');
      if (label) label.textContent = labels[view];
      if (toggle) toggle.setAttribute('aria-label', 'View: ' + labels[view]);
      sw.querySelectorAll('[data-view-option]').forEach(function (item) {
        var selected = item.getAttribute('data-view-option') === view;
        item.classList.toggle('is-selected', selected);
        item.setAttribute('aria-checked', selected ? 'true' : 'false');
      });
    });
    root.setAttribute('data-view', 'default');
    root.setAttribute('data-view-label', labels[view]);
    if (status) status.textContent = view === 'you'
      ? 'For You is showing the default LulaZel Hub / Cosmos view.'
      : labels[view] + ' is selected. Its custom view direction is pending; the default LulaZel Hub / Cosmos view remains visible.';
    if (persist !== false) { try { sessionStorage.setItem('lulazel-view', view); } catch (e) {} }
  }
  switches.forEach(function (sw) {
    var toggle = sw.querySelector('[data-view-toggle]');
    var menu = sw.querySelector('.lz-view-menu');
    if (!toggle || !menu) return;
    toggle.addEventListener('click', function (e) {
      e.stopPropagation();
      var willOpen = menu.hidden;
      closeAll();
      if (willOpen) {
        sw.classList.add('is-open');
        toggle.setAttribute('aria-expanded', 'true');
        menu.hidden = false;
      }
    });
    sw.querySelectorAll('[data-view-option]').forEach(function (item) {
      item.addEventListener('click', function () { applyView(item.getAttribute('data-view-option')); closeAll(); });
    });
  });
  document.addEventListener('click', function (e) {
    if (!switches.some(function (sw) { return sw.contains(e.target); })) closeAll();
  });
  var saved = null;
  try { saved = sessionStorage.getItem('lulazel-view'); } catch (e) {}
  applyView(saved || 'you', false);

  /* Works filters. */
  var cards = Array.prototype.slice.call(document.querySelectorAll('.lz-work-card'));
  if (cards.length) {
    var service = document.querySelector('[data-filter="service"]');
    var industry = document.querySelector('[data-filter="industry"]');
    var search = document.querySelector('[data-filter="search"]');
    var empty = document.querySelector('.lz-empty-works');
    function filterWorks() {
      var sv = service ? service.value : '';
      var ind = industry ? industry.value : '';
      var q = search ? search.value.trim().toLowerCase() : '';
      var visible = 0;
      cards.forEach(function (card) {
        var services = (card.getAttribute('data-services') || '').toLowerCase();
        var industries = (card.getAttribute('data-industries') || '').toLowerCase();
        var text = (card.getAttribute('data-title') || '').toLowerCase();
        var ok = (!sv || services.indexOf(sv.toLowerCase()) !== -1) &&
                 (!ind || industries.indexOf(ind.toLowerCase()) !== -1) &&
                 (!q || text.indexOf(q) !== -1);
        card.classList.toggle('is-hidden', !ok);
        if (ok) visible += 1;
      });
      if (empty) empty.classList.toggle('is-visible', visible === 0);
    }
    [service, industry, search].forEach(function (el) { if (el) el.addEventListener('input', filterWorks); });
    filterWorks();
  }

  /* Cosmos footer clocks in South African time. */
  document.querySelectorAll('.timer-card').forEach(function (card) {
    var time = card.querySelector('.timer.time');
    var pm = card.querySelector('.time-pm');
    var date = card.querySelector('.date-time');
    if (!time) return;
    function tick() {
      var now = new Date();
      var parts = new Intl.DateTimeFormat('en-GB', {
        timeZone: 'Africa/Johannesburg', hour: 'numeric', minute: '2-digit', hour12: true
      }).formatToParts(now);
      var hour = parts.find(function (p) { return p.type === 'hour'; });
      var minute = parts.find(function (p) { return p.type === 'minute'; });
      var period = parts.find(function (p) { return p.type === 'dayPeriod'; });
      time.textContent = (hour ? hour.value : '0') + ':' + (minute ? minute.value : '00');
      if (pm && period) pm.textContent = period.value.toLowerCase();
      if (date) {
        var d = new Intl.DateTimeFormat('en-GB', {
          timeZone: 'Africa/Johannesburg', weekday: 'long', month: 'long', day: 'numeric'
        }).format(now);
        var label = card.querySelector('.date-time_text');
        if (label) label.textContent = d + ' · SAST';
      }
    }
    tick();
    setInterval(tick, 30000);
  });
})();
''', encoding='utf-8')

# ---------------------------------------------------------------------------
# 4. Rebranding helpers.
# ---------------------------------------------------------------------------
BRAND_ATTRS = {'title', 'alt', 'aria-label', 'aria-description', 'placeholder', 'value', 'content', 'label'}

def rebrand_text(s: str) -> str:
    if not isinstance(s, str):
        return s
    patterns = [
        (r'hello@cosmos\.studio|anna@cosmos\.studio', CONTACT['email']),
        (r'www\.cosmos\.studio|cosmos\.studio', 'lulazelhub.co.za'),
        (r'Cosmos Studio™', 'LulaZel Hub™'),
        (r'Cosmos Studio', 'LulaZel Hub'),
        (r'Cosmos agency|cosmos agency', 'LulaZel Hub'),
        (r'©\s*2026\s*LulaZel Hub™', '© 2026 LulaZel Hub™ · Johannesburg, South Africa'),
        (r'\bCosmos\b', 'LulaZel Hub'),
        (r'\bcosmos\b', 'LulaZel Hub'),
        (r'\bCOSMOS\b', 'LULAZEL HUB'),
        (r'\bUkraine\b', 'South Africa'),
        (r'\bKyiv\b', 'Johannesburg'),
        (r'\bkyiv\b', 'johannesburg'),
        (r'US and Europe', 'South Africa, Africa and beyond'),
        (r'USA, New York', 'South Africa, Cape Town'),
        (r'UK, London', 'South Africa, Johannesburg'),
        (r'UAE, Dubai', 'South Africa, Durban'),
        (r'\bAnna\b', 'Lulamile'),
        (r'\banna\b', 'lulamile'),
    ]
    for pattern, repl in patterns:
        s = re.sub(pattern, repl, s)
    return s

def rebrand_soup(soup: BeautifulSoup) -> None:
    for node in soup.find_all(string=True):
        if isinstance(node, Comment) or (node.parent and node.parent.name in ('script', 'style')):
            continue
        new = rebrand_text(str(node))
        if new != str(node):
            node.replace_with(new)
    for tag in soup.find_all(True):
        for attr in list(tag.attrs.keys()):
            if attr not in BRAND_ATTRS:
                continue
            value = tag.get(attr)
            if isinstance(value, str):
                tag[attr] = rebrand_text(value)
            elif isinstance(value, list):
                tag[attr] = [rebrand_text(v) for v in value]

def add_meta(soup: BeautifulSoup, name: str, content: str, key: str = 'name') -> None:
    tag = soup.find('meta', attrs={key: name})
    if not tag:
        tag = soup.new_tag('meta')
        tag[key] = name
        soup.head.append(tag)
    tag['content'] = content

def serialize(soup: BeautifulSoup) -> str:
    out = str(soup)
    if not out.lower().startswith('<!doctype html>'):
        out = '<!doctype html>\n' + out
    if out.lower().count('<!doctype html>') > 1:
        first_end = out.find('>') + 1
        rest = re.sub(r'<!doctype html>\s*', '', out[first_end:], count=1, flags=re.I)
        out = '<!doctype html>\n' + rest.lstrip()
    return out

# ---------------------------------------------------------------------------
# 5. Cosmos navigation with the requested logo-adjacent selector.
# ---------------------------------------------------------------------------
source_index = BeautifulSoup((SRC / 'index.html').read_text(encoding='utf-8'), 'html.parser')
nav_template = source_index.select_one('nav.navbar')
footer_template = source_index.select_one('footer.section')

COSMOS_SERVICES = [
    'Product UI/UX Design', 'UI engineering', 'Website Design',
    'Brand Identity Design', 'Frontend & Backend Development',
    'Website Development', 'Web App Development', 'Mobile App Design & Development', 'UX Audit',
]
COSMOS_INDUSTRIES = [
    'Defense & Military Tech', 'SaaS', 'AI Products', 'EdTech', 'MedTech',
    'Gaming', 'Web3', 'B2B Services', 'Wellness', 'Nonprofit',
]
COSMOS_TOP_LINKS = [
    ('About', 'about.html'), ('Blog', 'blog.html'), ('Contacts', 'contacts.html'),
]

def dropdown_markup(suffix: str) -> str:
    chevron = '<svg class="lz-view-chevron" viewBox="0 0 12 7" fill="none" aria-hidden="true"><path d="M1 1l5 5 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
    check = '<svg class="lz-view-check" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M2.5 8.5l3.4 3.4L13.5 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    menu_id = 'lz-view-menu-' + suffix
    options = [
        ('marketing', 'For Marketing Teams', ''),
        ('you', 'For You', ' is-selected'),
        ('tech', 'For Tech', ''),
        ('else', 'Something Else', ''),
    ]
    opts = ''.join(
        f'<button class="lz-view-option{sel}" type="button" role="menuitemradio" aria-checked="{"true" if sel else "false"}" data-view-option="{key}"><span class="lz-view-dot" aria-hidden="true"></span><span>{label}</span>{check}</button>'
        for key, label, sel in options
    )
    return (
        '<div class="lz-view-switch" data-lz-view-switch>'
        f'<button class="lz-view-toggle" type="button" data-view-toggle aria-haspopup="menu" aria-expanded="false" aria-controls="{menu_id}" aria-label="View: For You">'
        '<span class="lz-view-dot" aria-hidden="true"></span><span data-view-label>For You</span>' + chevron + '</button>'
        f'<div class="lz-view-menu" id="{menu_id}" role="menu" aria-label="Choose a LulaZel Hub view" hidden>{opts}</div>'
        '</div>'
    )

def link_markup(label: str, href: str, classes: str = 'navbar_link w-inline-block') -> str:
    return (
        f'<a class="{classes}" href="{href}"><div class="navbar_link-texts">'
        f'<div class="navbar_link-text _1">{html.escape(label)}</div>'
        f'<div aria-hidden="true" class="navbar_link-text _2">{html.escape(label)}</div>'
        '</div></a>'
    )

def mobile_link_markup(label: str, href: str) -> str:
    return (
        f'<a class="menu_link w-inline-block" href="{href}"><div class="menu_link-texts">'
        f'<p class="menu_link-text _1">{html.escape(label)}</p>'
        f'<p aria-hidden="true" class="menu_link-text _2">{html.escape(label)}</p>'
        '</div><div class="menu_link-dot"></div></a>'
    )

def localize_tag_attrs(tag: Tag, prefix: str, is_page: bool) -> None:
    for child in tag.find_all(True):
        for attr in ['href', 'src', 'srcset', 'data-src', 'action']:
            v = child.get(attr)
            if isinstance(v, str):
                child[attr] = localize_attr(v, prefix, is_page)
    for attr in ['href', 'src', 'srcset', 'data-src', 'action']:
        v = tag.get(attr)
        if isinstance(v, str):
            tag[attr] = localize_attr(v, prefix, is_page)

def set_dropdown_items(dd: Tag, items: list[str], href: str) -> None:
    list_node = dd.select_one('.dropdown-list')
    if not list_node:
        return
    list_node.clear()
    frag = BeautifulSoup(
        '<div class="w-dyn-list"><div class="w-dyn-items" role="list">' +
        ''.join(
            f'<div class="w-dyn-item" role="listitem"><a class="dropdown-link" href="{href}">{html.escape(item)}</a></div>'
            for item in items
        ) + '</div></div>', 'html.parser'
    )
    list_node.append(frag)

def enhance_nav(nav: Tag, prefix: str, is_page: bool, suffix: str) -> Tag:
    localize_tag_attrs(nav, prefix, is_page)

    for img in nav.select('img.menu_logo'):
        svg = BeautifulSoup(SMALL_LOGO_SVG, 'html.parser').svg
        img.replace_with(svg)

    for a in nav.select('a.navbar-logo_wr, a.menu_logo-wrap'):
        a['aria-label'] = 'LulaZel Hub — home'
        a['href'] = prefix + 'index.html'

    phrases = ['Miltech design agency', 'Product design studio', 'SaaS design partner', 'UI/UX design studio']
    for i, node in enumerate(nav.select('.navbar_logo-anim_text')):
        node.string = phrases[i % len(phrases)]

    # Desktop top links: keep Cosmos dropdowns, add About / Blog / Contacts.
    links_wrap = nav.select_one('.navbar_component .navbar_links-wrap')
    if links_wrap:
        dropdowns = links_wrap.select('.w-dropdown')
        if len(dropdowns) >= 1:
            set_dropdown_items(dropdowns[0], COSMOS_SERVICES, localize_attr('pages/services.html', prefix, is_page))
        if len(dropdowns) >= 2:
            set_dropdown_items(dropdowns[1], COSMOS_INDUSTRIES, localize_attr('pages/industries.html', prefix, is_page))
        frag = BeautifulSoup(''.join(link_markup(label, localize_attr('pages/' + href, prefix, is_page)) for label, href in COSMOS_TOP_LINKS), 'html.parser')
        for child in list(frag.contents):
            if isinstance(child, Tag):
                links_wrap.append(child)

    # Logo-adjacent For You selector.
    desktop_logo = nav.select_one('.navbar_component .navbar-logo_wr')
    if desktop_logo:
        frag = BeautifulSoup(dropdown_markup(suffix + '-desktop'), 'html.parser')
        node = frag.find('div')
        if node:
            desktop_logo.insert_after(node)

    # Contact block and Book a Call.
    for img in nav.select('img.navbar_contact-pic'):
        img['src'] = prefix + 'assets/owner/my-new-site/img/lulamile.webp'
        img['alt'] = 'Lulamile'
    for node in nav.select('.nav_contact-name'):
        node.string = 'Contact Lulamile'
    for node in nav.select('.home-header_position'):
        node.string = 'Business Developer'
    for a in nav.select('a.button'):
        a['href'] = CONTACT['calendly']
        a['target'] = '_blank'
        a['rel'] = 'noopener'

    # Mobile menu: Cosmos list items and the same selector.
    mobile_links = nav.select_one('.menu_links-wrap')
    if mobile_links:
        mobile_dropdowns = mobile_links.select('.dropdown-menu')
        if len(mobile_dropdowns) >= 1:
            set_dropdown_items(mobile_dropdowns[0], COSMOS_SERVICES, localize_attr('pages/services.html', prefix, is_page))
        if len(mobile_dropdowns) >= 2:
            set_dropdown_items(mobile_dropdowns[1], COSMOS_INDUSTRIES, localize_attr('pages/industries.html', prefix, is_page))
        frag = BeautifulSoup(''.join(mobile_link_markup(label, localize_attr('pages/' + href, prefix, is_page)) for label, href in COSMOS_TOP_LINKS), 'html.parser')
        for child in list(frag.contents):
            if isinstance(child, Tag):
                mobile_links.append(child)
    mobile_logo = nav.select_one('.menu_links .menu_logo-wrap')
    if mobile_logo:
        frag = BeautifulSoup(dropdown_markup(suffix + '-mobile'), 'html.parser')
        node = frag.find('div')
        if node:
            mobile_logo.insert_after(node)
    return nav

def cosmos_nav(prefix: str, is_page: bool, suffix: str) -> Tag:
    nav = BeautifulSoup(str(nav_template), 'html.parser').nav
    return enhance_nav(nav, prefix, is_page, suffix)

# ---------------------------------------------------------------------------
# 6. Owner content and Cosmos footer/wordmark.
# ---------------------------------------------------------------------------
site_content = json.loads((OWNER_JS / 'site.content.json').read_text(encoding='utf-8'))
home_content = json.loads((OWNER_JS / 'home.content.json').read_text(encoding='utf-8'))
services_data = json.loads((OWNER_JS / 'services.catalogue.json').read_text(encoding='utf-8'))
projects_data = json.loads((OWNER_JS / 'portfolio.projects.json').read_text(encoding='utf-8'))
owner_services = services_data['services']

def esc(x) -> str:
    return html.escape(str(x))

def owner_image(project: dict) -> str:
    rel = project.get('image', '').lstrip('/')
    if rel.startswith('assets/'):
        rel = 'assets/owner/my-new-site/' + rel[len('assets/'):]
    else:
        rel = 'assets/placeholder.svg'
    return rel if (SITE / rel).exists() else 'assets/placeholder.svg'

def selected_projects() -> list[dict]:
    wanted = ['DesignOps', 'Nerdma', 'ProdOps', 'LulaGazette', 'Lawmania', 'AddmoreDigital']
    by_name = {p.get('client', ''): p for p in projects_data}
    return [by_name[n] for n in wanted if n in by_name][:6]

PROJECTS = selected_projects()

def replace_wordmarks(soup: BeautifulSoup) -> None:
    headings = soup.select_one('.home-header_headings')
    if headings:
        headings.clear()
        frag = BeautifulSoup(HERO_WORDMARK, 'html.parser')
        for child in list(frag.contents):
            if isinstance(child, Tag):
                headings.append(child)
    for svg in soup.find_all('svg'):
        vb = svg.get('viewbox') or svg.get('viewBox') or ''
        if '1367' in vb:
            svg.replace_with(BeautifulSoup(WORDMARK_SVG, 'html.parser').svg)

def enhance_footer(footer: Tag, prefix: str, is_page: bool) -> Tag:
    localize_tag_attrs(footer, prefix, is_page)
    for svg in footer.find_all('svg'):
        vb = svg.get('viewbox') or svg.get('viewBox') or ''
        if '1367' in vb:
            svg.replace_with(BeautifulSoup(WORDMARK_SVG, 'html.parser').svg)
    for a in footer.select('a[href^="mailto:"]'):
        a['href'] = 'mailto:' + CONTACT['email']
        for p in a.select('p[fs-copyclip-element="copy-this"], p.footer_link-text'):
            p.string = CONTACT['email']
    for span in footer.select('[fs-copyclip-element="copy-this"]'):
        span.string = CONTACT['email']
    zones = ['Johannesburg', 'Cape Town', 'Durban', 'Remote']
    for i, card in enumerate(footer.select('.timer-card')):
        card['data-time'] = 'johannesburg'
        label = card.select_one('.date-time span:last-child, .date-time_text, .date-time')
        if label:
            label.string = 'South Africa, ' + zones[i % len(zones)] + ' · SAST'
    target = footer.select_one('.footer_content-in') or footer
    strip = BeautifulSoup('''
<div class="lz-contact-grid">
  <a class="lz-contact-link" href="mailto:mkhungela.l@gmail.com"><span>Email</span><strong>mkhungela.l@gmail.com</strong></a>
  <a class="lz-contact-link" href="tel:+27837195064"><span>Call</span><strong>+27 83 719 5064</strong></a>
  <a class="lz-contact-link" href="https://wa.me/27837195064"><span>WhatsApp</span><strong>+27 83 719 5064</strong></a>
  <a class="lz-contact-link" href="https://calendly.com/lulamile_m/meet-lulamile"><span>Meeting</span><strong>Book on Calendly</strong></a>
</div>''', 'html.parser')
    target.append(strip)
    return footer

def adjust_home(soup: BeautifulSoup, prefix: str) -> None:
    labels = ['UI/UX Product design', 'Web design', 'Branding', 'Development']
    for i, node in enumerate(soup.select('.home-header_service-text')):
        node.string = labels[i % len(labels)]

    hero_media = soup.select_one('img.home-header_video')
    if hero_media:
        hero_media['src'] = prefix + 'assets/owner/my-new-site/img/portfolio/designops.webp'
        hero_media['alt'] = 'DesignOps interface designed and built by LulaZel Hub'
        hero_media['loading'] = 'eager'
    for a in soup.select('a.home-header_component'):
        a['href'] = localize_attr('pages/works.html', prefix, False)

    intro = soup.select_one('section.section_clients h1')
    if intro:
        intro.string = 'UI/UX design and development studio for SaaS, AI, defense, and military tech'
    intro_p = soup.select_one('section.section_clients p.text-weight-medium')
    if intro_p:
        desc = home_content['hero']['description']
        desc = desc.replace('I design', 'LulaZel Hub designs').replace('I bring', 'We bring')
        intro_p.string = desc

    works = soup.select('section.section_works .works_item')
    for i, card in enumerate(works):
        if i >= len(PROJECTS):
            break
        p = PROJECTS[i]
        name = card.select_one('.works_name')
        if name:
            name.string = p.get('client', 'Selected work')
        infos = card.select('.works_info')
        if len(infos) >= 2:
            infos[0].string = p.get('year') or 'South Africa'
            cats = p.get('categories') or ['Client project']
            infos[1].string = cats[0].replace('-', ' ').title()
        src = owner_image(p)
        for img in card.select('img.works_image, img.works_pic'):
            img['src'] = prefix + src if not src.startswith('assets/') or not prefix else src
            img['src'] = prefix + 'assets/' + src[len('assets/'):] if src.startswith('assets/') else prefix + src
            img['alt'] = esc(p.get('client', 'Selected work'))
            if img.has_attr('srcset'):
                del img['srcset']
        for a in card.select('a.works_card'):
            a['href'] = localize_attr('pages/works.html', prefix, False)

    reviews = soup.select_one('.reviews-wr')
    if reviews:
        cards = []
        for t in site_content['testimonials'][:3]:
            cards.append(
                '<article class="lz-testimonial-card"><blockquote>“' + esc(t['message']) + '”</blockquote>' +
                '<strong>' + esc(t['name']) + '</strong><small>' + esc(t['designation']) +
                (' · ' + esc(t['company']) if t.get('company') else '') + '</small></article>'
            )
        reviews.replace_with(BeautifulSoup('<div class="lz-testimonial-grid">' + ''.join(cards) + '</div>', 'html.parser'))

    about_titles = soup.select('section.section_about .about_item-title')
    about_descs = soup.select('section.section_about .about_item-texts p')
    process = site_content.get('process', [])
    for i, item in enumerate(process[:max(len(about_titles), len(about_descs))]):
        if i < len(about_titles):
            about_titles[i].string = item.get('title', about_titles[i].get_text(strip=True))
        if i < len(about_descs):
            about_descs[i].string = item.get('body', about_descs[i].get_text(strip=True))

# ---------------------------------------------------------------------------
# 7. Inner-page Cosmos section templates.
# ---------------------------------------------------------------------------
SERVICE_COSMOS = [
    ('Website design services for SaaS, AI and tech companies', 'Marketing sites, landing pages and redesigns that explain a complex product in a few seconds.'),
    ('Custom website design built around conversion', 'Every design decision is judged by one thing: does it help the right visitor take the next step.'),
    ('Website design work with measurable results', 'A portfolio spanning AI companies, e-commerce brands, game studios and nonprofits.'),
]

def service_cards_html() -> str:
    cards = []
    for i, s in enumerate(owner_services[:6], 1):
        tags = ''.join('<span class="lz-tag">' + esc(t) + '</span>' for t in s.get('tags', [])[:3])
        cards.append(
            '<article class="lz-service-card"><span class="lz-service-num">' + f'{i:02d}' + '</span>' +
            '<div><h3>' + esc(s['title']) + '</h3><p>' + esc(s.get('summary', '')) + '</p>' +
            '<div class="lz-tag-row">' + tags + '</div></div></article>'
        )
    return ''.join(cards)

def works_cards_html(prefix: str) -> str:
    service_map = {
        'DesignOps': 'UI engineering, Website Design, Frontend & Backend Development',
        'Nerdma': 'Website Design, Product UI/UX Design, UX Audit',
        'ProdOps': 'Product UI/UX Design, Website Design, Frontend & Backend Development',
        'LulaGazette': 'Brand Identity Design, Website Design',
        'Lawmania': 'Product UI/UX Design, Mobile App Design & Development',
        'AddmoreDigital': 'Website Design, Brand Identity Design',
    }
    industry_map = {
        'DesignOps': 'SaaS, B2B Services', 'Nerdma': 'B2B Services, SaaS',
        'ProdOps': 'AI Products, SaaS', 'LulaGazette': 'B2B Services, Nonprofit',
        'Lawmania': 'AI Products, B2B Services', 'AddmoreDigital': 'B2B Services, Wellness',
    }
    cards = []
    for p in PROJECTS:
        src = owner_image(p)
        full_src = prefix + 'assets/' + src[len('assets/'):] if src.startswith('assets/') else prefix + src
        client = p.get('client', 'Selected work')
        year = p.get('year') or '2026'
        cats = p.get('categories') or ['Client project']
        niche = cats[0].replace('-', ' ').title()
        services = service_map.get(client, 'Website Design, Product UI/UX Design')
        industries = industry_map.get(client, 'B2B Services, SaaS')
        cards.append(
            f'<article class="lz-work-card" data-title="{esc(client)}" data-services="{esc(services)}" data-industries="{esc(industries)}">' +
            f'<div class="lz-work-media"><img src="{full_src}" alt="{esc(client)} project cover" loading="lazy"/>' +
            f'<div class="lz-work-badge"><img src="{full_src}" alt=""/><strong>{esc(client)}</strong><span></span><span>See work</span></div></div>' +
            '<div class="lz-work-meta"><div><small>Year</small><span>' + esc(year) + '</span></div>' +
            '<div class="right"><small>Niche</small><span>' + esc(niche) + '</span></div></div></article>'
        )
    return ''.join(cards)

def page_section(body: str) -> str:
    return '<main class="main-wrapper" id="main">' + body + '</main>'

SERVICES_BODY = '''
<section class="section lz-page" style="padding-top:9rem">
  <div class="padding-global"><div class="container-large">
    <div class="lz-page-head">
      <div class="lz-clutch"><span class="lz-stars">★★★★★</span><span>Verified by Clutch™ reviews</span></div>
      <h1 class="lz-page-title">Award-winning website design agency for tech brands</h1>
      <p class="lz-page-lead">LulaZel Hub is a website design agency for SaaS, AI and tech companies, with 60+ international design awards including 18 Awwwards. We design marketing sites and landing pages that explain complex products clearly and turn visitors into leads.</p>
      <div class="lz-page-actions">
        <a class="button w-inline-block" href="{p}pages/contacts.html"><div class="button-in"><div class="button_texts"><div class="button_text _1">Get a Project Estimate</div><div aria-hidden="true" class="button_text _2">Talk to us</div></div></div></a>
        <a class="lz-text-link" href="{p}pages/works.html">See Website Design Work <span class="lz-arrow-box">↗</span></a>
      </div>
    </div>
    <div class="lz-stats">
      <div><div class="lz-stat-number">500</div><div class="lz-stat-label">Projects successfully launched for clients</div></div>
      <div><div class="lz-stat-number">12</div><div class="lz-stat-label">Years in Web &amp; UX Design</div></div>
      <div><div class="lz-stat-number">60+</div><div class="lz-stat-label">International Design Awards</div></div>
    </div>
  </div></div>
</section>
<section class="section lz-section"><div class="padding-global"><div class="container-large">
  <div class="lz-section-label">What we design</div>
  <h2 class="lz-section-title">Website design services for SaaS, AI and tech companies</h2>
  <p class="lz-page-lead">LulaZel Hub’s website design services cover marketing sites, landing pages and redesigns for companies that need to explain a complex product in a few seconds. These are the website types we design most often.</p>
  <div class="lz-service-grid">''' + service_cards_html() + '''</div>
</div></div></section>
<section class="section lz-section"><div class="padding-global"><div class="container-large">
  <div class="lz-section-label">Our approach</div>
  <h2 class="lz-section-title">Custom website design built around conversion</h2>
  <div class="lz-text-grid">
    <div class="lz-text-block"><h2>Structure before visuals</h2><p>We define the sitemap, page goals and content hierarchy before any visual design. Wireframes show where proof, pricing and calls to action live on each page.</p></div>
    <div class="lz-text-block"><h2>Proof where buyers look for it</h2><p>We place case studies, numbers, client logos and reviews next to the claims they support. A visitor should never have to search for evidence that you can deliver.</p></div>
    <div class="lz-text-block"><h2>Motion with a purpose</h2><p>Animation explains how the product works or guides attention to the next step. Motion and 3D are planned from the start, so pages stay fast on mobile.</p></div>
    <div class="lz-text-block"><h2>The same team designs and builds</h2><p>Our developers build the sites we design on Webflow, WordPress or React and Next.js. Layouts, animation and CMS structure match the design without a handoff gap.</p></div>
  </div>
</div></div></section>
'''

WORKS_BODY = '''
<section class="section lz-page" style="padding-top:9rem">
  <div class="padding-global"><div class="container-large">
    <div class="lz-page-head">
      <div class="lz-section-label">Our works</div>
      <h1 class="lz-page-title" style="font-size:clamp(4rem,7vw,7rem);margin-top:.75rem">Selected works</h1>
      <p class="lz-page-lead">As a UX design studio, our focus is on creating digital products that are clear, intuitive, and built to grow. We start by understanding the product, the users, and the business context behind every decision.</p>
    </div>
    <div class="lz-work-filters">
      <div class="lz-filter-group">
        <select class="lz-filter-pill" data-filter="service" aria-label="Filter by service">
          <option value="">Services</option><option>Product UI/UX Design</option><option>Website Design</option><option>Brand Identity Design</option><option>Frontend &amp; Backend Development</option><option>UX Audit</option>
        </select>
        <select class="lz-filter-pill" data-filter="industry" aria-label="Filter by industry">
          <option value="">Industries</option><option>Defense &amp; Military Tech</option><option>SaaS</option><option>AI Products</option><option>B2B Services</option><option>Wellness</option><option>Nonprofit</option>
        </select>
      </div>
      <label class="lz-search"><svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" stroke-width="1.5"/><path d="M13 13l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg><input type="search" data-filter="search" placeholder="Search by keywords..." aria-label="Search works"/></label>
    </div>
    <div class="lz-work-list">''' + '__WORK_CARDS__' + '''</div>
    <div class="lz-empty-works">No works match those filters yet.</div>
  </div></div>
</section>
'''

def generic_body(title: str, intro: str, cards: list[tuple[str, str]], label: str = 'Cosmos') -> str:
    card_html = ''.join(
        '<article class="lz-service-card"><span class="lz-service-num">' + f'{i:02d}' + '</span><div><h3>' + esc(h) + '</h3><p>' + esc(p) + '</p></div></article>'
        for i, (h, p) in enumerate(cards, 1)
    )
    return (
        '<section class="section lz-page" style="padding-top:9rem"><div class="padding-global"><div class="container-large">'
        '<div class="lz-page-head"><div class="lz-section-label">' + esc(label) + '</div>'
        '<h1 class="lz-page-title">' + esc(title) + '</h1><p class="lz-page-lead">' + esc(intro) + '</p></div>'
        '<div class="lz-service-grid">' + card_html + '</div>'
        + '''<div class="lz-contact-grid">
  <a class="lz-contact-link" href="mailto:mkhungela.l@gmail.com"><span>Email</span><strong>mkhungela.l@gmail.com</strong></a>
  <a class="lz-contact-link" href="tel:+27837195064"><span>Call</span><strong>+27 83 719 5064</strong></a>
  <a class="lz-contact-link" href="https://wa.me/27837195064"><span>WhatsApp</span><strong>+27 83 719 5064</strong></a>
  <a class="lz-contact-link" href="https://calendly.com/lulamile_m/meet-lulamile"><span>Meeting</span><strong>Book on Calendly</strong></a>
</div><p class="lz-time-note">Johannesburg · Gauteng · South Africa · SAST</p>'''
        + '</div></div></section>'
    )

INNER_BODIES = {
    'services.html': SERVICES_BODY,
    'works.html': WORKS_BODY,
    'industries.html': generic_body(
        'Industries we design for',
        'LulaZel Hub works with product teams in defense and military tech, SaaS, AI, EdTech, MedTech, gaming, Web3, B2B services, wellness and nonprofit organisations.',
        [(x, 'Product UX/UI, website design, design systems and front-end delivery for teams building serious products.') for x in COSMOS_INDUSTRIES[:6]],
        'Industries',
    ),
    'about.html': generic_body(
        'One senior, hands-on team from first conversation to working code',
        'Since 2018, our designers and engineers have contributed to 500+ digital product launches. Research, UX, UI, design systems and front-end development stay together in one place.',
        [(x.get('title', ''), x.get('body', '')) for x in site_content.get('process', [])],
        'About',
    ),
    'blog.html': generic_body(
        'AI/Design Weekly',
        'Notes on product design, UX research, design systems, AI interfaces and the craft of shipping digital products.',
        [
            ('Product UX/UI Design', 'How to turn complex product workflows into clear, intuitive interfaces.'),
            ('Website Design', 'What makes a marketing site explain a product in a few seconds.'),
            ('UI engineering', 'Design systems and front-end choices that keep products consistent.'),
            ('UX Audit', 'Finding the friction that stops the right visitor from taking the next step.'),
            ('Defense Tech', 'Designing clear interfaces for high-stakes, technical products.'),
            ('AI Products', 'Making AI product experiences understandable, useful and trustworthy.'),
        ],
        'Blog',
    ),
    'contacts.html': generic_body(
        'Let’s talk',
        'Tell us what you are building. LulaZel Hub is based in Johannesburg, Gauteng, and works remotely across South Africa and beyond. A typical project takes 2–6 weeks.',
        [
            ('Email', CONTACT['email']), ('Call', CONTACT['tel']), ('WhatsApp', CONTACT['tel']),
            ('Book a Call', 'Calendly · SAST'), ('Location', 'Johannesburg, Gauteng, South Africa'),
            ('Hours', 'Monday–Friday · SAST'),
        ],
        'Contacts',
    ),
    'careers.html': generic_body(
        'Careers',
        'LulaZel Hub works with senior designers, engineers and strategists who care about clear products and working code. Open collaborations are shared here when available.',
        [
            ('Product design', 'Research, UX, UI and design systems for complex products.'),
            ('UI engineering', 'React, Next.js and Webflow delivery with production-ready detail.'),
            ('Motion & 3D', 'Purposeful animation that explains the product.'),
            ('Strategy', 'Positioning, content hierarchy and conversion thinking.'),
            ('South Africa', 'Johannesburg / remote across Mzansi.'),
            ('Contact', CONTACT['email']),
        ],
        'Careers',
    ),
    'generic.html': generic_body(
        'Explore LulaZel Hub',
        'Cosmos-style pages, services, works and contact information for a South African design and development hub.',
        [
            ('Services', 'Product UI/UX Design, UI engineering, Website Design and Development.'),
            ('Industries', 'SaaS, AI, defense tech, EdTech, MedTech and B2B services.'),
            ('Selected works', 'Portfolio work from websites to product dashboards.'),
            ('About', 'One senior team from research to working code.'),
            ('Blog', 'AI/Design Weekly notes on product design.'),
            ('Contacts', 'Johannesburg, Gauteng, South Africa · SAST.'),
        ],
        'Explore',
    ),
}

# ---------------------------------------------------------------------------
# 8. Document-level finishing.
# ---------------------------------------------------------------------------
page_titles = {
    'index.html': 'LulaZel Hub | South African Design & Development',
    'services.html': 'Services | LulaZel Hub',
    'industries.html': 'Industries | LulaZel Hub',
    'works.html': 'Selected works | LulaZel Hub',
    'about.html': 'About | LulaZel Hub',
    'blog.html': 'AI/Design Weekly | LulaZel Hub',
    'contacts.html': 'Contacts | LulaZel Hub',
    'careers.html': 'Careers | LulaZel Hub',
    'generic.html': 'Explore | LulaZel Hub',
}

def ensure_link(soup: BeautifulSoup, href: str) -> None:
    if not soup.select_one(f'link[href="{href}"]'):
        link = soup.new_tag('link', rel='stylesheet', href=href)
        soup.head.append(link)

def finish_document(path: Path, soup: BeautifulSoup, prefix: str, is_page: bool) -> None:
    html_tag = soup.find('html')
    if html_tag:
        html_tag['lang'] = 'en-ZA'
        html_tag['data-view'] = 'default'
        html_tag['data-view-label'] = 'For You'
        html_tag['data-wf-domain'] = 'lulazelhub.co.za'
    if soup.title:
        soup.title.string = page_titles.get(path.name, 'LulaZel Hub')

    for link in soup.select('link[rel~="stylesheet"]'):
        link.decompose()
    for href in ['site.css', 'theme.css', 'fonts.css', 'cosmos-tweaks.css']:
        ensure_link(soup, prefix + 'assets/css/' + href + '?v=light-cosmos-2')

    favicon = soup.find('link', rel=lambda x: x and 'icon' in x)
    if not favicon:
        favicon = soup.new_tag('link', rel='icon', href=prefix + 'assets/owner/my-new-site/img/favicon.svg', type='image/svg+xml')
        soup.head.append(favicon)
    else:
        favicon['href'] = prefix + 'assets/owner/my-new-site/img/favicon.svg'

    add_meta(soup, 'description', 'LulaZel Hub is a South African design and development hub in Johannesburg, Gauteng, building websites, apps, design systems and production front ends.')
    add_meta(soup, 'og:title', page_titles.get(path.name, 'LulaZel Hub'), key='property')
    add_meta(soup, 'og:description', 'South African design and development hub for websites, apps, UI engineering and digital products.', key='property')
    add_meta(soup, 'og:locale', 'en_ZA', key='property')
    add_meta(soup, 'og:image', prefix + 'assets/brand/lulazel-hub-wordmark.svg', key='property')
    add_meta(soup, 'geo.region', 'ZA-GT')
    add_meta(soup, 'geo.placename', 'Johannesburg, Gauteng, South Africa')
    add_meta(soup, 'language', 'en-ZA')
    add_meta(soup, 'country', 'South Africa')
    add_meta(soup, 'theme-color', '#f6f6f4')

    for script in soup.select('script[src]'):
        script.decompose()
    script = soup.new_tag('script', src=prefix + 'assets/js/site.js?v=light-cosmos-2')
    script['defer'] = ''
    soup.head.append(script)

    if not soup.select_one('#lz-view-status'):
        status = soup.new_tag('p')
        status['class'] = ['lz-view-status']
        status['id'] = 'lz-view-status'
        status['aria-live'] = 'polite'
        status.string = 'For You is showing the default LulaZel Hub view.'
        soup.body.insert(0, status)

    if not soup.find('script', attrs={'type': 'application/ld+json'}):
        ld = soup.new_tag('script', type='application/ld+json')
        ld.string = json.dumps({
            '@context': 'https://schema.org', '@type': 'Organization', 'name': 'LulaZel Hub',
            'url': CONTACT['site'], 'email': CONTACT['email'], 'telephone': '+27837195064',
            'description': 'South African design and development hub in Johannesburg, Gauteng.',
            'address': {'@type': 'PostalAddress', 'addressLocality': 'Johannesburg', 'addressRegion': 'Gauteng', 'addressCountry': 'ZA'},
        }, ensure_ascii=False)
        soup.head.append(ld)

    rebrand_soup(soup)
    path.write_text(serialize(soup), encoding='utf-8')

# ---------------------------------------------------------------------------
# 9. Apply to every HTML document.
# ---------------------------------------------------------------------------
html_files = [SITE / 'index.html'] + sorted((SITE / 'pages').glob('*.html'))
for path in html_files:
    text = path.read_text(encoding='utf-8')
    soup = BeautifulSoup(text, 'html.parser')
    is_page = path.parent.name == 'pages'
    prefix = '../' if is_page else ''

    # Replace nav and footer with one light Cosmos implementation.
    existing_nav = soup.select_one('nav.navbar')
    nav = cosmos_nav(prefix, is_page, path.stem)
    if existing_nav:
        existing_nav.replace_with(nav)
    else:
        soup.body.insert(0, nav)

    existing_footer = soup.select_one('footer.section')
    footer = enhance_footer(deepcopy(footer_template), prefix, is_page)
    if existing_footer:
        existing_footer.replace_with(footer)
    else:
        soup.body.append(footer)

    replace_wordmarks(soup)

    if not is_page:
        adjust_home(soup, prefix)
        # Keep Cosmos home sections, but ensure nav home links point to index.
        for a in soup.select('a[href*="generic.html"]'):
            if 'Home' in a.get_text(' ', strip=True):
                a['href'] = prefix + 'index.html'
    else:
        body = INNER_BODIES.get(path.name, INNER_BODIES['generic.html'])
        body = body.replace('{p}', prefix)
        body = body.replace('__WORK_CARDS__', works_cards_html(prefix))
        main = soup.select_one('main.main-wrapper')
        new_main = BeautifulSoup(page_section(body), 'html.parser').main
        if main:
            main.replace_with(new_main)
        else:
            soup.body.append(new_main)

    # Final broad attribute localization for any generated paths.
    for tag in soup.find_all(True):
        for attr in ['href', 'src', 'srcset', 'data-src', 'action']:
            v = tag.get(attr)
            if isinstance(v, str):
                tag[attr] = localize_attr(v, prefix, is_page)

    finish_document(path, soup, prefix, is_page)

# ---------------------------------------------------------------------------
# 10. Site metadata, docs, and scratch cleanup.
# ---------------------------------------------------------------------------
(SITE / 'sitemap.xml').write_text('''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://lulazelhub.co.za/</loc></url>
  <url><loc>https://lulazelhub.co.za/pages/services.html</loc></url>
  <url><loc>https://lulazelhub.co.za/pages/industries.html</loc></url>
  <url><loc>https://lulazelhub.co.za/pages/works.html</loc></url>
  <url><loc>https://lulazelhub.co.za/pages/about.html</loc></url>
  <url><loc>https://lulazelhub.co.za/pages/blog.html</loc></url>
  <url><loc>https://lulazelhub.co.za/pages/contacts.html</loc></url>
  <url><loc>https://lulazelhub.co.za/pages/careers.html</loc></url>
</urlset>
''', encoding='utf-8')
(SITE / 'robots.txt').write_text('''User-agent: *
Allow: /
Sitemap: https://lulazelhub.co.za/sitemap.xml
''', encoding='utf-8')

(ROOT / '.gitignore').write_text('''image-search/
cosmos-copy/hts-cache/
cosmos-copy/hts-log.txt
__pycache__/
.DS_Store
''', encoding='utf-8')

(ROOT / 'README.md').write_text('''# LulaZel Hub — exact light Cosmos UI

`cosmos-copy/` keeps the captured **original Cosmos/Webflow UI**: the off-white
page, white rounded navbar, black typography and buttons, Cosmos hero,
sections, cards, filters, footer and interactions. The later dark adaptation
CSS and generic text wordmark were removed.

Only the requested tweaks remain on top:

- the brand is **LulaZel Hub**, rebuilt with inline geometric `.logo-word` /
  `.logo-letter` vector forms in black;
- the light Cosmos navbar keeps the dropdown beside the logo, with
  **For You** selected by default;
- all navbar/list items are Cosmos items, including `Services`, `Industries`,
  `Works`, `About`, `Blog`, `Contacts`, the Cosmos services dropdown and the
  right-side `Contact Lulamile` / `Business Developer` / `Book a Call` block;
- Cosmos service labels remain in the hero: `UI/UX Product design`,
  `Web design`, `Branding`, `Development`;
- supplied South African contact details and owner project/testimonial content
  are used where they exist, with Cosmos copy retained elsewhere.

`For Marketing Teams`, `For Tech` and `Something Else` intentionally keep the
default Cosmos view; no extra views were invented.

## Run locally

```sh
./scripts/serve.sh 3000
```

## Rebuild

`scripts/rebuild_exact_cosmos.py` is idempotent within this workspace. It resets
`cosmos-copy/` from the complete local `/tmp/site-source` Cosmos fallback,
strips the non-Cosmos dark CSS, writes the light theme/tweaks and reapplies the
brand, navigation, wordmark and content changes.
''', encoding='utf-8')

shutil.rmtree(ROOT / 'image-search', ignore_errors=True)
print('rebuilt exact light Cosmos UI')
print('site files', sum(1 for p in SITE.rglob('*') if p.is_file()))
