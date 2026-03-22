---
name: amazon-product-photography
description: "Amazon product photography planning and briefing agent. Plan main images, lifestyle shots, infographics, and size comparison photos. Generate photographer briefs, shot lists, and image optimization guidelines for maximum click-through rate and conversion. Triggers: product photography, amazon photos, main image, lifestyle photo, infographic, photo brief, amazon images, product photos, amazon listing images, image optimization, photo shot list, amazon ctr, product photo guide, image strategy, amazon photo requirements"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/amazon-product-photography
---

# Amazon Product Photography Guide

Plan and brief your product photography to maximize CTR and conversion. From main image strategy to infographic design — know exactly what images you need and why.

## Commands

```
photo plan [product]            # full 7-image strategy plan
photo main [product]            # main image brief
photo lifestyle [product]       # lifestyle shot list
photo infographic [product]     # infographic content plan
photo brief                     # generate photographer brief doc
photo audit [describe images]   # score existing images
photo requirements              # Amazon technical requirements
photo mobile                    # mobile thumbnail optimization
```

## What Data to Provide

- **Product type & category** — what it is
- **Target customer** — who uses it (age, gender, lifestyle)
- **Key selling points** — top 3 features to visually communicate
- **Competitors** — describe their images so we can differentiate
- **Brand style** — clean/minimal vs. lifestyle/warm vs. technical/studio

## 7-Image Strategy Framework

### Image 1: Main Image (Most Critical)
**Purpose**: Win the click in search results
**Rules**:
- Pure white background (RGB 255,255,255) — mandatory
- Product fills 85%+ of frame
- No text, no props, no logos (except on product itself)
- Show the actual product, not packaging (usually)
- High resolution: minimum 1000px on shortest side (2000px recommended)

**CTR Optimization**:
- Show your best angle (usually 3/4 view)
- If multiple pieces, show all of them
- If color variations, show the most appealing color
- Consider: what thumbnail wins at 100px × 100px?

### Image 2: Feature Callout / Infographic
**Purpose**: Communicate 3–4 key features fast
**Format**: Product image + text overlays pointing to features
**Best for**: Technical products, multi-feature products
**Copy**: Short feature labels, not full sentences

### Image 3: Lifestyle / In-Use Shot
**Purpose**: Help customer visualize owning the product
**Elements**:
- Real person using the product (or implied use context)
- Environment matches target customer's life
- Emotion: show the feeling of using the product
- No direct eye contact with camera (feels more authentic)

### Image 4: Size Comparison
**Purpose**: Set accurate size expectations, reduce returns
**Options**:
- Product next to a common object (coin, hand, ruler)
- Dimensions overlaid on product photo
- Before/after size context (e.g., fits in a pocket)

### Image 5: Benefits / Results Shot
**Purpose**: Show the outcome, not just the product
**Examples**:
- Skincare: before/after or glowing skin close-up
- Kitchen tool: beautiful finished dish
- Fitness: person after workout looking energized
- Organization: tidy shelf vs. cluttered shelf

### Image 6: What's in the Box
**Purpose**: Eliminate "what do I get?" uncertainty
**Format**: Flat lay of all included items with numbered callouts
**Include**: All accessories, documentation, packaging

### Image 7: Social Proof / Certification
**Purpose**: Build trust and reduce purchase hesitation
**Options**:
- "X,000+ customers" with star rating graphic
- Certification logos (CE, FDA, BPA-free)
- Award badges
- Press mentions / media logos

## Infographic Design Guide

### Layout Options
| Type | Best For |
|------|----------|
| **Icon grid** | Products with 4–6 distinct features |
| **Side-by-side comparison** | Vs. competitor or vs. old way |
| **Before/after** | Products with transformative results |
| **How it works** (3-step) | Products with process/usage sequence |
| **Spec breakdown** | Technical/measurement-driven products |

### Infographic Copy Rules
- Headline: max 6 words, benefit-focused
- Feature label: max 3 words
- Supporting line: max 10 words
- Font minimum: 24pt equivalent (must be readable at thumbnail)
- High contrast: dark text on light, or light on dark — no grey-on-grey

## Photographer Brief Template

```
PROJECT: [Brand] [Product] Amazon Listing Photography
DATE: [Date]
DELIVERABLES: 7 images per colorway

IMAGE SPECS:
- Resolution: 3000 × 3000px minimum
- Format: JPEG, sRGB color profile
- Main image: pure white background (#FFFFFF)
- Secondary images: [style direction]

BRAND STYLE:
- Color palette: [hex codes]
- Mood: [clean/warm/technical/lifestyle]
- Reference images: [attach 2-3 reference photos]

SHOT LIST:
1. Main hero — [angle], [background], [props if any]
2. Feature callout — [which features to highlight]
3. Lifestyle — [scene description], [model type if any]
4. Size comparison — [comparison object]
5. Results/benefit — [what to show]
6. What's in the box — [flat lay setup]
7. Trust/certification — [which certifications to display]

MODELS/PROPS NEEDED:
- [List any models, ages, demographics]
- [List props needed]

DO NOT:
- [List brand-specific restrictions]
- Competitors' products in frame
- Logos not belonging to brand
```

## Amazon Image Technical Requirements

| Requirement | Specification |
|-------------|--------------|
| Main image background | Pure white (RGB 255,255,255) |
| Minimum resolution | 1000px on shortest side |
| Recommended resolution | 2000px+ (enables zoom) |
| File formats | JPEG, PNG, GIF, TIFF |
| Max file size | 10MB |
| Product in frame | Must fill ≥85% of image |
| Forbidden on main | Text, logos, watermarks, props |

## CTR by Image Type (Research Benchmarks)

- Main image with product only: baseline
- Main image showing all variants: +8% CTR
- Main image with lifestyle element (rule-bending): risky but +15% if approved
- A/B tested main image: +12–25% CTR improvement

## Output Format

1. **7-Image Shot List** — exact brief for each image
2. **Infographic Content Plan** — which features, what copy, what layout
3. **Photographer Brief** — complete ready-to-send document
4. **Main Image Critique** — if existing image provided, specific improvements
5. **Mobile Thumbnail Test** — does it work at 100px?

## Rules

1. Main image compliance is non-negotiable — violations get listings suppressed
2. Always plan for the mobile thumbnail first (most searches are mobile)
3. Every image must answer one customer question — no "decorative" filler images
4. Lifestyle images should show aspiration, not just product use
5. Infographic text must be readable without zooming on mobile
