---
version: alpha
name: "New Form Capital — Editorial Finance"
description: "New Form Capital uses a bold editorial design language built around massive display typography (TWK Lausanne, Editorial New, PP Mondwest) set against a near-white off-green background (#fafffa). The hero headline is typographically dominant. spanning the full viewport width at ~138px. with black-and-white photography inlined directly within the text flow. A single neon-green accent (#2bee4b) punctuates the logo and UI micro-elements. The design is flat, shadowless, and uses minimal border-radius, projecting authority and forward-looking financial confidence."
colors:
  dark-overlay: "#2e3830"
  neon-green-accent: "#2bee4b"
  off-white-background: "#fafffa"
  deep-forest: "#232924"
  near-black-text: "#121613"
  forest-green-mid: "#516254"
  muted-green-gray: "#c8d2c8"
  pure-black: "#000000"
typography:
  hero-display:
    fontFamily: "TWK Lausanne"
    fontSize: "137.779px"
    fontWeight: "550"
    lineHeight: "137.779px"
    letterSpacing: "-5.511px"
  hero-display-alt:
    fontFamily: "TWK Lausanne"
    fontSize: "85.3376px"
    fontWeight: "550"
    lineHeight: "85.3376px"
    letterSpacing: "-1.707px"
  mondwest-display-xl:
    fontFamily: "PP Mondwest"
    fontSize: "262.221px"
    fontWeight: "400"
    lineHeight: "235.999px"
    letterSpacing: "-10.489px"
  mondwest-display-l:
    fontFamily: "PP Mondwest"
    fontSize: "146.662px"
    fontWeight: "400"
    lineHeight: "131.996px"
    letterSpacing: "-5.867px"
  editorial-serif-xl:
    fontFamily: "Editorial New"
    fontSize: "213.338px"
    fontWeight: "300"
    lineHeight: "192.004px"
    letterSpacing: "-2.133px"
  editorial-serif-l:
    fontFamily: "Editorial New"
    fontSize: "124.442px"
    fontWeight: "300"
    lineHeight: "111.997px"
    letterSpacing: "-2.489px"
  editorial-serif-m:
    fontFamily: "Editorial New"
    fontSize: "53.3376px"
    fontWeight: "300"
    lineHeight: "48.004px"
    letterSpacing: "-1.067px"
  display-64:
    fontFamily: "TWK Lausanne"
    fontSize: "64px"
    fontWeight: "550"
    lineHeight: "70.4px"
    letterSpacing: "-1.28px"
  body-ui:
    fontFamily: "TWK Lausanne"
    fontSize: "16px"
    fontWeight: "200"
    lineHeight: "16px"
    letterSpacing: "-0.32px"
  ui-medium:
    fontFamily: "TWK Lausanne"
    fontSize: "16px"
    fontWeight: "550"
    lineHeight: "16px"
    letterSpacing: "-0.32px"
  caption-tag:
    fontFamily: "TWK Lausanne"
    fontSize: "12.4416px"
    fontWeight: "350"
    lineHeight: "13.686px"
    letterSpacing: "0.124px"
  micro-label:
    fontFamily: "TWK Lausanne"
    fontSize: "9.7792px"
    fontWeight: "550"
    lineHeight: "10.757px"
rounded:
  sm: "4.4px"
  md: "7.1px"
  lg: "8.9px"
  xl: "14px"
spacing:
  xs: "3.9px"
  sm: "8.9px"
  md: "13.3px"
  base: "17.8px"
  lg: "22.2px"
  xl: "26.7px"
  2xl: "35.6px"
  3xl: "44.4px"
  4xl: "48.9px"
  5xl: "62.2px"
  6xl: "88.9px"
  7xl: "106.7px"
  8xl: "115.6px"
  9xl: "120px"
  10xl: "168.9px"
components:
  hero-headline-block:
    fontFamily: "TWK Lausanne"
    fontSize: "137.779px"
    fontWeight: "550"
    lineHeight: "137.779px"
    letterSpacing: "-5.511px"
    textColor: "{colors.near-black-text}"
    backgroundColor: "transparent"
    rounded: "0px"
    padding: "88.88px 0px 53.34px"
    boxShadow: "none"
  hero-image-inset:
    rounded: "{rounded.md}"
    backgroundColor: "transparent"
    boxShadow: "none"
    overflow: "hidden"
  logo-button:
    textColor: "{colors.pure-black}"
    backgroundColor: "transparent"
    rounded: "0px"
    borderWidth: "0px"
    boxShadow: "none"
    accentColor: "{colors.neon-green-accent}"
  menu-toggle:
    textColor: "{colors.pure-black}"
    accentColor: "{colors.neon-green-accent}"
    fontFamily: "TWK Lausanne"
    fontSize: "16px"
    fontWeight: "550"
  navigation-overlay-background:
    backgroundColor: "rgba(46, 56, 48, 0.8)"
    textColor: "{colors.pure-black}"
    rounded: "0px"
    borderWidth: "0px"
    boxShadow: "none"
    padding: "0px"
---

## Overview

New Form Capital uses a bold editorial design language built around massive display typography (TWK Lausanne, Editorial New, PP Mondwest) set against a near-white off-green background (#fafffa). The hero headline is typographically dominant. spanning the full viewport width at ~138px. with black-and-white photography inlined directly within the text flow. A single neon-green accent (#2bee4b) punctuates the logo and UI micro-elements. The design is flat, shadowless, and uses minimal border-radius, projecting authority and forward-looking financial confidence.

**Signature traits:**
- Dual typeface system: Pairs TWK Lausanne and PP Mondwest across the type hierarchy.
- Layered elevation: Depth comes from 2 validated shadow tokens.

## Colors

The palette uses 8 validated color tokens across 1 theme profile. Semantic roles stay attached to observed usage so generation agents can choose accents without inventing new color meaning.

**Semantic naming:**
- **surface-background** maps to `off-white-background`: Role "background" is grounded by usage context "Primary page background — near-white with a faint green tint, used across all surfaces".
- **content-text** maps to `near-black-text`: Role "text" is grounded by usage context "Primary body and heading text color, dominant foreground across all zones".
- **action-border** maps to `pure-black`: Role "border" is grounded by usage context "Navigation text, logo wordmark, button foreground, and border elements in header/footer".
- **content-background** maps to `neon-green-accent`: Role "background" is grounded by usage context "Brand accent — used on logo underline, menu icon bars, and interactive highlights".

### Text Scale
- **Deep Forest** (#232924): Secondary text and surface tones in footer. Role: text. {authored: rgb(35, 41, 36), space: rgb}
- **Near-Black Text** (#121613): Primary body and heading text color, dominant foreground across all zones. Role: text. {authored: rgb(18, 22, 19), space: rgb}

### Interactive
- **Forest Green Mid** (#516254): Subtle border and secondary text in footer zone. Role: border. {authored: rgb(81, 98, 84), space: rgb}
- **Muted Green-Gray** (#c8d2c8): Hairline borders and dividers in footer. Role: border. {authored: rgb(200, 210, 200), space: rgb}
- **Pure Black** (#000000): Navigation text, logo wordmark, button foreground, and border elements in header/footer. Role: border. {authored: rgb(0, 0, 0), space: rgb}

### Surface & Shadows
- **Dark Overlay** (#2e3830): Semi-transparent side nav background overlay (rgba(46,56,48,0.8)). Role: background. {authored: rgba(46, 56, 48, 0.8), space: rgb, alpha: 0.8}
- **Neon Green Accent** (#2bee4b): Brand accent — used on logo underline, menu icon bars, and interactive highlights. Role: background. {authored: rgb(43, 238, 75), space: rgb}
- **Off-White Background** (#fafffa): Primary page background — near-white with a faint green tint, used across all surfaces. Role: background. {authored: rgb(250, 255, 250), space: rgb}

## Typography

Typography uses TWK Lausanne, PP Mondwest, Editorial New across extracted hierarchy roles. Keep hierarchy mapped to these token rows before adding decorative type styles.

Mixes TWK Lausanne and PP Mondwest and Editorial New for visual contrast. Weight range spans semi-bold, regular, light. Sizes range from 9.7792px to 262.221px.

### Font Roles
- **Headline Font**: TWK Lausanne
- **Body Font**: TWK Lausanne

### Type Scale Evidence
| Role | Font | Size | Weight | Line Height | Letter Spacing | Stack / Features | Notes |
|------|------|------|--------|-------------|----------------|------------------|-------|
| Primary hero headline — full-viewport-width display text | TWK Lausanne | 137.779px | 550 | 137.779px | -5.511px | TWK Lausanne | Extracted token |
| Secondary hero and section display headings | TWK Lausanne | 85.3376px | 550 | 85.3376px | -1.707px | TWK Lausanne | Extracted token |
| Decorative oversized display — likely used in scroll-driven or full-bleed sections | PP Mondwest | 262.221px | 400 | 235.999px | -10.489px | PP Mondwest | Extracted token |
| Large decorative section headings | PP Mondwest | 146.662px | 400 | 131.996px | -5.867px | PP Mondwest | Extracted token |
| Oversized serif display for editorial contrast sections | Editorial New | 213.338px | 300 | 192.004px | -2.133px | Editorial New | Extracted token |
| Large serif section headings | Editorial New | 124.442px | 300 | 111.997px | -2.489px | Editorial New | Extracted token |
| Mid-size serif subheadings | Editorial New | 53.3376px | 300 | 48.004px | -1.067px | Editorial New | Extracted token |
| Section headings and large callout text | TWK Lausanne | 64px | 550 | 70.4px | -1.28px | TWK Lausanne | Extracted token |
| Body copy, navigation labels, and UI text | TWK Lausanne | 16px | 200 | 16px | -0.32px | TWK Lausanne | Extracted token |
| Emphasized UI labels, nav items, and button text | TWK Lausanne | 16px | 550 | 16px | -0.32px | TWK Lausanne | Extracted token |
| Captions, tags, and metadata labels | TWK Lausanne | 12.4416px | 350 | 13.686px | 0.124px | TWK Lausanne | Extracted token |
| Micro labels, badges, and ticker-style text | TWK Lausanne | 9.7792px | 550 | 10.757px | normal | TWK Lausanne | Extracted token |

## Layout

Responsive system uses 3 breakpoint tier(s): mobile, desktop, wide.

This system uses a 8.9px base grid with scale values 3.9, 8.9, 13.3, 17.8, 22.2, 26.7, 35.6, 44.4, 48.9, 62.2, 88.9, 106.7, 115.6, 120, 168.9.

### Responsive Strategy
- **mobile (429-1024px)**: Constrain layout for small viewports and prioritize vertical stacking.
- **desktop (1025-1440px)**: Expand layout density and horizontal composition for wide viewports.
- **wide (>= 1441px)**: Stretch composition with generous gutters and wider layout spans.

### Spacing System
| Token | Value | Px | Notes |
|------|-------|----|-------|
| xs | 3.9px | 3.9 | Extracted spacing token |
| sm | 8.9px | 8.9 | Extracted spacing token |
| md | 13.3px | 13.3 | Extracted spacing token |
| base | 17.8px | 17.8 | Extracted spacing token |
| lg | 22.2px | 22.2 | Extracted spacing token |
| xl | 26.7px | 26.7 | Extracted spacing token |
| 2xl | 35.6px | 35.6 | Extracted spacing token |
| 3xl | 44.4px | 44.4 | Extracted spacing token |
| 4xl | 48.9px | 48.9 | Extracted spacing token |
| 5xl | 62.2px | 62.2 | Extracted spacing token |
| 6xl | 88.9px | 88.9 | Extracted spacing token |
| 7xl | 106.7px | 106.7 | Extracted spacing token |
| 8xl | 115.6px | 115.6 | Extracted spacing token |
| 9xl | 120px | 120 | Extracted spacing token |
| 10xl | 168.9px | 168.9 | Extracted spacing token |

## Elevation & Depth

Keep depth flat unless validated shadow or interaction evidence appears in the extraction payload. Do not invent shadows beyond this evidence boundary.

### Shadow Evidence
| Shadow Token | Layers | Details |
|--------------|--------|---------|
| Green Glow Strong | 1 | 1px 8px 20px 0px rgba(16, 94, 29, 0.45) |
| Green Glow Soft | 1 | 1px 8px 20px 0px rgba(18, 146, 39, 0.25) |

### Interaction Signals
| Theme | Signal | Evidence |
|-------|--------|----------|
| Light | outline-color | rgb(250, 255, 250) ; rgb(18, 22, 19) ; rgb(0, 0, 0) |
| Light | outline-width | 3px |
| Light | outline-offset | 0px |
| Light | transform | matrix(1, 0, 0, 1, 0, 0) ; matrix(1, 0, 0, 1, 0, -17.7775) ; matrix(1, 0, 0, 1, 0, 10) |

## Shapes

Shape language maps directly to rounded tokens. Keep component corners consistent with the role mapping below before introducing bespoke geometry.

### Radius Roles
| Token | Value | Px | Role Mapping |
|------|-------|----|--------------|
| sm | 4.4px | 4.4 | Subtle corner |
| md | 7.1px | 7.1 | Control corner |
| lg | 8.9px | 8.9 | Control corner |
| xl | 14px | 14 | Card corner |

### Geometry Evidence
| Radius Token | Shape | Units |
|--------------|-------|-------|
| sm | 4.4px | px |
| md | 7.1px | px |
| lg | 8.9px | px |
| xl | 14px | px |

## Components

Components should be recreated from token references first, then tuned with variant notes and probe-backed state guidance.
- **Hero Headline Block**: Full-viewport-width display headline with black-and-white photography inlined within the text flow. Images are positioned as inline elements between words, creating a typographic-image collage.
- **Hero Image Inset**: Rounded-corner image containers embedded inline within the hero headline text flow. Images are black-and-white photography of financial landmarks.
- **Side Navigation**: Full-screen overlay side navigation triggered by the Menu button. Uses a semi-transparent dark green background overlay.
- **Logo Button**: Top-left logo mark — 'New Form' wordmark with a neon-green underline accent on 'New'. Rendered as a button element.
- **Menu Toggle**: Top-right 'Menu' text label paired with a three-bar icon rendered in neon green. Triggers the side navigation overlay.

### Hero Headline Block

**Default**
- fontFamily: TWK Lausanne
- fontSize: 137.779px
- fontWeight: 550
- lineHeight: 137.779px
- letterSpacing: -5.511px
- textColor: #121613
- backgroundColor: transparent
- rounded: 0px
- padding: 88.88px 0px 53.34px
- boxShadow: none
- State guidance: Probe-confirmed: h1.sc-01-Hero__Text-sc-1igrmkj-2 at 137.779px, color rgb(18,22,19). Wrapper padding confirmed at 88.8832px 0px 53.3376px.

### Hero Image Inset

**Default**
- rounded: 7.1px
- backgroundColor: transparent
- boxShadow: none
- overflow: hidden
- State guidance: Probe-confirmed: div.sc-01-Hero__Image-sc-1igrmkj-3 borderRadius 7.1168px. Images are grayscale financial photography.

### Logo Button

**Default**
- textColor: #000000
- backgroundColor: transparent
- rounded: 0px
- borderWidth: 0px
- boxShadow: none
- accentColor: #2bee4b
- State guidance: Probe-confirmed: button.Logo__Wrapper-sc-1ajunpz-1. Neon green underline on 'New' visible in screenshot.

### Menu Toggle

**Default**
- textColor: #000000
- accentColor: #2bee4b
- fontFamily: TWK Lausanne
- fontSize: 16px
- fontWeight: 550
- State guidance: Visually confirmed in screenshot: 'Menu' text + green bar icon in top-right corner.

### Navigation

**Overlay Background**
- backgroundColor: rgba(46, 56, 48, 0.8)
- textColor: #000000
- rounded: 0px
- borderWidth: 0px
- boxShadow: none
- padding: 0px
- State guidance: Probe-confirmed: button.SideNav__BG-sc-ev7esv-1 backgroundColor rgba(46,56,48,0.8). Acts as the overlay trigger/background.

## Do's and Don'ts

Guardrails protect Dual typeface system, Layered elevation without adding unsupported visual claims.

| Do | Don't |
|----|---------|
| Do maintain consistent spacing using the base grid | Don't make unsupported claims about absent visual features |
| Do maintain WCAG AA contrast ratios (4.5:1 for normal text) | Don't mix rounded and sharp corners in the same view |
| Do use the primary color only for the single most important action per screen |  |
| Do verify evidence before writing new design-system guidance |  |

## Responsive Evidence

### Breakpoints
| Name | Width | Key Changes |
|------|-------|-------------|
| Mobile | <= 428px | screen and (max-width: 428px) |
| Mobile | 429-1024px | screen and (min-width: 429px) and (max-width: 1024px) |
| Desktop | 1025-1440px | screen and (min-width: 1025px) and (max-width: 1440px) |
| Desktop | >= 1441px | screen and (min-width: 1441px) |

## Agent Prompt Guide

### Example Component Prompts
- Create Hero Headline Block variant that preserves Full-viewport-width display headline with black-and-white photography inlined within the text flow. Images are positioned as inline elements between words, creating a typographic-image collage..
- Create Hero Image Inset variant that preserves Rounded-corner image containers embedded inline within the hero headline text flow. Images are black-and-white photography of financial landmarks..
- Create Logo Button variant that preserves Top-left logo mark — 'New Form' wordmark with a neon-green underline accent on 'New'. Rendered as a button element..

### Iteration Guide
1. Start with extracted palette and typography roles only.
2. Map spacing and radius directly from token tables before visual polish.
3. Apply component patterns one section at a time and compare against source intent.
4. Keep elevation claims tied to explicit evidence in output.
5. Iterate with smallest diffs and re-check section hierarchy after each change.
