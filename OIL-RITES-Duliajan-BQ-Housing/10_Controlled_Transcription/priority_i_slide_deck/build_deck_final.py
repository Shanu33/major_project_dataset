import sys
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_final_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Professional Academic Civil Engineering Palette
    NAVY = RGBColor(15, 44, 89)         # #0F2C59 - Primary Accent / Headers
    STEEL = RGBColor(43, 108, 176)      # #2B6CB0 - Secondary Accent / Subtitles
    CHARCOAL = RGBColor(51, 65, 85)     # #334155 - Body Text
    LIGHT_BG = RGBColor(248, 250, 252)  # #F8FAFC - Card Background
    BORDER_COLOR = RGBColor(203, 213, 225) # #CBD5E1 - Card Borders
    WHITE = RGBColor(255, 255, 255)
    ALERT_RED = RGBColor(185, 28, 28)   # #B91C1C - Blocked / Firewalled
    MUTED_GREEN = RGBColor(22, 101, 52) # #166534 - Reconciliation / Verified
    HEADER_FILL = RGBColor(30, 58, 138) # #1E3A8A - Table Header Navy

    def add_header(slide, title_text, category="CIVIL ENGINEERING MAJOR PROJECT REVIEW"):
        # Header top decorative line
        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.38), Inches(11.733), Inches(0.04))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = STEEL
        top_bar.line.fill.background()

        # Category text
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.46), Inches(11.733), Inches(0.32))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_top = tf_cat.margin_right = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = STEEL

        # Title text
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.78), Inches(11.733), Inches(0.68))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(21)
        p_title.font.bold = True
        p_title.font.color.rgb = NAVY

    def add_bullet_card(slide, left, top, width, height, bullets, title=None, border_color=BORDER_COLOR, bg_color=LIGHT_BG):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.2)

        tx_box = slide.shapes.add_textbox(left + Inches(0.25), top + Inches(0.2), width - Inches(0.5), height - Inches(0.4))
        tf = tx_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p_first = tf.paragraphs[0]
        if title:
            p_first.text = title
            p_first.font.size = Pt(13.5)
            p_first.font.bold = True
            p_first.font.color.rgb = NAVY
            p_first.space_after = Pt(10)
        
        for idx, bullet in enumerate(bullets):
            p = tf.add_paragraph() if (title or idx > 0) else p_first
            p.text = "•  " + bullet[0]
            p.font.size = Pt(11.5)
            p.font.bold = True
            p.font.color.rgb = NAVY
            p.space_after = Pt(2)

            if len(bullet) > 1 and bullet[1]:
                p_sub = tf.add_paragraph()
                p_sub.text = "    " + bullet[1]
                p_sub.font.size = Pt(10.5)
                p_sub.font.color.rgb = CHARCOAL
                p_sub.space_after = Pt(8)

    def set_notes(slide, notes_text):
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = notes_text

    # =========================================================================
    # SLIDE 1: Title & Project Objective (Simplified & Clean)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    bg_card1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.8), Inches(11.733), Inches(5.9))
    bg_card1.fill.solid()
    bg_card1.fill.fore_color.rgb = LIGHT_BG
    bg_card1.line.color.rgb = BORDER_COLOR
    bg_card1.line.width = Pt(1.5)

    t_bar1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.8), Inches(11.733), Inches(0.12))
    t_bar1.fill.solid()
    t_bar1.fill.fore_color.rgb = NAVY
    t_bar1.line.fill.background()

    tb1 = s1.shapes.add_textbox(Inches(1.4), Inches(1.35), Inches(10.5), Inches(4.8))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p1 = tf1.paragraphs[0]
    p1.text = "DEPARTMENT OF CIVIL ENGINEERING | MAJOR PROJECT REVIEW"
    p1.font.size = Pt(12)
    p1.font.bold = True
    p1.font.color.rgb = STEEL
    p1.space_after = Pt(16)

    p2 = tf1.add_paragraph()
    p2.text = "Evidence-Controlled Civil Quantity Intelligence"
    p2.font.size = Pt(28)
    p2.font.bold = True
    p2.font.color.rgb = NAVY

    p3 = tf1.add_paragraph()
    p3.text = "Multi-Document Benchmark & Architecture on OIL India BQ Housing"
    p3.font.size = Pt(16)
    p3.font.color.rgb = STEEL
    p3.space_after = Pt(26)

    p4 = tf1.add_paragraph()
    p4.text = "Project Scope & Research Objective:"
    p4.font.size = Pt(13)
    p4.font.bold = True
    p4.font.color.rgb = NAVY
    p4.space_after = Pt(10)

    bullets_s1 = [
        ("Benchmark Scope", "Typical Stilt+6 Residential Housing Block (24 Units, Seismic Zone V)."),
        ("Project Authority", "Client: Oil India Limited | Project Management Consultant: RITES Limited."),
        ("Core Objective", "Establish auditable multi-document data extraction linking drawings with IS 1200 rules while enforcing refusal guardrails against AI hallucination.")
    ]
    for b in bullets_s1:
        p = tf1.add_paragraph()
        p.text = "•  " + b[0] + ": " + b[1]
        p.font.size = Pt(11.5)
        p.font.color.rgb = CHARCOAL
        p.space_after = Pt(6)

    set_notes(s1, "Respected members of the review panel, our major project addresses a fundamental bottleneck in digital construction: the lack of auditable, evidence-controlled data pipelines for quantity estimation. Instead of treating quantity surveying as an ungrounded generative AI task, we developed a rigorous multi-document architecture for the OIL India Duliajan BQ Housing Complex. Our system transcribes architectural and structural drawings, reconciles inter-trade discrepancies, and enforces an engineered refusal guardrail that halts takeoff when drawings lack prerequisite engineering details.")

    # =========================================================================
    # SLIDE 2: Problem in Construction Quantity Estimation
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "The Core Problem: AI Hallucination, Prompt Leakage, and Lost Provenance")

    bullets_s2_left = [
        ("The Black-Box Generation Trap", "Standard Vision-Language Models predict bulk quantities without any traceable geometric audit trail back to drawing gridlines or schedule callouts."),
        ("Prompt Poisoning & Data Leakage", "Feeding tender BOQs directly into AI prompts leads to circular reasoning; the AI recites the BOQ rather than truly parsing and understanding drawing geometry.")
    ]
    bullets_s2_right = [
        ("Synthetic Rules-of-Thumb", "Existing estimation tools rely heavily on ungrounded percentages (e.g. blanket 23% window deductions and 10% door deductions) that introduce compounding errors."),
        ("Contractual & Engineering Realities", "In public works contracts, ungrounded estimates trigger formal disputes, contractor claims, and budget overruns; IS 1200 demands verifiable geometric dimensions.")
    ]
    add_bullet_card(s2, Inches(0.8), Inches(1.75), Inches(5.6), Inches(4.9), bullets_s2_left, "Current Limitations in AI Estimation")
    add_bullet_card(s2, Inches(6.9), Inches(1.75), Inches(5.6), Inches(4.9), bullets_s2_right, "Contractual & Civil Engineering Realities")

    set_notes(s2, "Most current AI research in construction estimation suffers from prompt poisoning. Researchers frequently provide both drawings and the final BOQ to the model, claiming high benchmark agreement. In reality, the model simply memorized or copied the BOQ text. Furthermore, when tender drawings omit bar bending schedules or pile depths, generic models hallucinate numbers instead of admitting data is missing. Under IS 1200 and standard Indian public works contracts, an estimate without verifiable provenance is legally and commercially unusable.")

    # =========================================================================
    # SLIDE 3: Why Project-Level Document Matching Matters
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Why Project-Level Document Matching Matters")

    bullets_s3_left = [
        ("Inter-Document Dependencies in Civil Engineering", "A quantity surveyor never calculates from one drawing alone. Every single element requires cross-referencing across multiple specialized disciplines."),
        ("The Cross-Referencing Chain", "Measuring an RCC beam requires architectural sections (clear floor height), structural plans (framing spans), rebar schedules (bar marks), and DBR (concrete grade).")
    ]
    bullets_s3_right = [
        ("Why Disconnected Document Scraping Fails", "Scraping disconnected drawings from random internet sources creates geometric incoherence; training AI on mismatched pairs teaches noise rather than structural logic."),
        ("Closed-Loop Tender Ecosystem", "This pilot captures the complete, authentic tender package: 55 drawings, Design Basis Report, Geotechnical Report, Tender Notices, and CPWD Specifications.")
    ]
    add_bullet_card(s3, Inches(0.8), Inches(1.75), Inches(5.6), Inches(4.9), bullets_s3_left, "Inter-Document Interdependence")
    add_bullet_card(s3, Inches(6.9), Inches(1.75), Inches(5.6), Inches(4.9), bullets_s3_right, "Authentic Tender Packaging")

    set_notes(s3, "In civil engineering practice, an architectural plan only shows walls and room uses; the structural drawing shows column sizes and reinforcement, and the specifications define concrete mixes. If an AI system is trained on random floor plans scraped from the internet, it cannot learn real-world civil engineering. Our pilot captures a complete, closed-loop tender package from RITES and Oil India Limited, preserving all inter-document dependencies exactly as encountered on a live construction project.")

    # =========================================================================
    # SLIDE 4: Selected Pilot Project and Dataset Corpus
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "Pilot Benchmark: OIL India Workmen Housing Complex, Duliajan")

    bullets_s4_1 = [
        ("Tender Identity & Authority", "Client: Oil India Limited | PMC: RITES Limited | Tender ID: RITES/NERPO/OIL/BQ-HOUSING/25 | Award Value: Rs 128.14 Cr (Dec 2025 status record)."),
        ("Seismic & Geotechnical Context", "Located in Duliajan, Upper Assam (Seismic Zone V, Zone Factor Z=0.36). Requires heavy ductile detailing per IS 13920:2016 and deep bored pile foundations.")
    ]
    bullets_s4_2 = [
        ("Selected Benchmark Unit", "One typical Stilt+6 BQ Residential Housing Tower (Footprint: 30.08m x 16.08m = 483.60 m2, Total Height: 24.00m, 24 residential units)."),
        ("Corpus Under Audit (55 Sheets)", "26 Architectural sheets (AR/001-026), 23 Structural sheets (STR/100-150), 18 Building Services sheets (MEP/001-018), plus DBR, Geotech, and CPWD Specifications.")
    ]
    add_bullet_card(s4, Inches(0.8), Inches(1.75), Inches(5.6), Inches(4.9), bullets_s4_1, "Contractual & Structural Context")
    add_bullet_card(s4, Inches(6.9), Inches(1.75), Inches(5.6), Inches(4.9), bullets_s4_2, "Physical Scope & Drawing Corpus")

    set_notes(s4, "Our benchmark project is an authentic, high-seismic public sector housing development in Assam. We isolated one typical Stilt+6 BQ residential tower as our benchmark unit. It features 207 bored cast-in-situ piles, 49 vertical load-bearing columns and shear walls, 34 framing beams per floor, and 24 identical flats across 6 upper storeys. The drawing corpus comprises 55 audited tender drawing sheets across architecture, structure, and MEP.")

    # =========================================================================
    # SLIDE 5: AI Input vs Ground-Truth Concept (WITH DIAGRAM)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Ontological Separation: Predictive Inputs vs Ground-Truth Targets")

    # Left Box: Predictive AI Inputs
    box_ai = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.75), Inches(5.5), Inches(3.65))
    box_ai.fill.solid()
    box_ai.fill.fore_color.rgb = RGBColor(238, 242, 255)
    box_ai.line.color.rgb = STEEL
    box_ai.line.width = Pt(1.5)

    tb_ai = s5.shapes.add_textbox(Inches(1.0), Inches(1.9), Inches(5.1), Inches(3.3))
    tf_ai = tb_ai.text_frame
    tf_ai.word_wrap = True
    p_ai_t = tf_ai.paragraphs[0]
    p_ai_t.text = "PREDICTIVE AI INPUT DOMAIN (VISIBLE)"
    p_ai_t.font.size = Pt(12)
    p_ai_t.font.bold = True
    p_ai_t.font.color.rgb = NAVY
    p_ai_t.space_after = Pt(10)

    ai_items = [
        "Architectural Drawings (AR/TD/001 - 026): Floor plans, elevations, sections, door/window schedules.",
        "Structural Drawings (STR/TD/100 - 110): Pile layouts, column/wall schedules, beam framing, slab details.",
        "Engineering Specifications: Design Basis Report (DBR), CPWD Specifications 2019, IS 1200 measurement rules.",
        "Zero Leakage Guarantee: Zero BOQ items, priced rates, or cost figures are placed in extraction prompts."
    ]
    for it in ai_items:
        p = tf_ai.add_paragraph()
        p.text = "•  " + it
        p.font.size = Pt(10.5)
        p.font.color.rgb = CHARCOAL
        p.space_after = Pt(6)

    # Right Box: Blind Ground Truth Domain
    box_gt = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.0), Inches(1.75), Inches(5.5), Inches(3.65))
    box_gt.fill.solid()
    box_gt.fill.fore_color.rgb = RGBColor(254, 242, 242)
    box_gt.line.color.rgb = ALERT_RED
    box_gt.line.width = Pt(1.5)

    tb_gt = s5.shapes.add_textbox(Inches(7.2), Inches(1.9), Inches(5.1), Inches(3.3))
    tf_gt = tb_gt.text_frame
    tf_gt.word_wrap = True
    p_gt_t = tf_gt.paragraphs[0]
    p_gt_t.text = "BLIND GROUND-TRUTH DOMAIN (FIREWALLED)"
    p_gt_t.font.size = Pt(12)
    p_gt_t.font.bold = True
    p_gt_t.font.color.rgb = ALERT_RED
    p_gt_t.space_after = Pt(10)

    gt_items = [
        "Official Tender BOQ: Schedule of Quantities used strictly for post-takeoff validation comparison.",
        "Priced Schedule of Rates (SOR): Item rate analysis and contractor financial bids.",
        "Approved CPM Schedule: Contractor project bar chart and baseline duration milestones.",
        "Single-Tower BOQ Note: Because RITES only issued an aggregate 8-tower BOQ, cost accuracy is not calculated."
    ]
    for it in gt_items:
        p = tf_gt.add_paragraph()
        p.text = "•  " + it
        p.font.size = Pt(10.5)
        p.font.color.rgb = CHARCOAL
        p.space_after = Pt(6)

    # Bottom Banner: The Firewall Principle
    fw_bar = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(5.6), Inches(11.7), Inches(1.05))
    fw_bar.fill.solid()
    fw_bar.fill.fore_color.rgb = LIGHT_BG
    fw_bar.line.color.rgb = BORDER_COLOR
    fw_bar.line.width = Pt(1)

    tb_fw = s5.shapes.add_textbox(Inches(1.0), Inches(5.68), Inches(11.3), Inches(0.9))
    tf_fw = tb_fw.text_frame
    tf_fw.word_wrap = True
    p_fw = tf_fw.paragraphs[0]
    p_fw.text = "THE METHODOLOGICAL FIREWALL: PREVENTING DATA CONTAMINATION"
    p_fw.font.size = Pt(11)
    p_fw.font.bold = True
    p_fw.font.color.rgb = NAVY
    p_fw_sub = tf_fw.add_paragraph()
    p_fw_sub.text = "To guarantee scientific rigor, predictive inputs are strictly separated from ground-truth validation targets. BOQ validation was not performed, and cost accuracy is not calculated because the official contract tender only provides an aggregate multi-building Schedule of Quantities."
    p_fw_sub.font.size = Pt(10)
    p_fw_sub.font.color.rgb = CHARCOAL

    set_notes(s5, "Slide 5 illustrates our core methodological safeguard: the ontological firewall. We strictly separate predictive AI inputs from blind evaluation targets. The AI model only receives design drawings and specifications. The tender BOQ and contract costs remain strictly behind a blind evaluation firewall. Furthermore, because RITES issued an aggregate 8-tower BOQ without an official single-tower breakdown, BOQ validation was not performed and cost accuracy is not calculated to preserve academic integrity.")

    # =========================================================================
    # SLIDE 6: Evidence-Control Methodology
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Evidence-Control Methodology: The 9-Tier Provenance Hierarchy")

    bullets_s6_left = [
        ("The 9-Tier Provenance Ladder", "Every parameter carries an immutable evidence tag:\n  • Tier 1: DIRECT_SHEET_OBSERVATION (Printed text/callouts)\n  • Tier 2: DERIVED_FROM_ARCHITECTURAL_SECTION (Heights)\n  • Tier 3: DERIVED_BY_BASIC_GEOMETRY (L x B, perimeters)\n  • Tier 4: IS_CODE_DERIVED (45.3d rebar lap, cover)\n  • Tier 5: ENGINEERING_ASSUMPTION_STANDARDIZED (Medium)"),
        ("Eradicating Over-Confident Assumptions", "Under our project governance rules, zero assumptions are permitted to claim high confidence. All assumptions are capped at MEDIUM or ESTIMATED.")
    ]
    bullets_s6_right = [
        ("Purging Synthetic Heuristics", "Legacy estimation rules-of-thumb—such as deducting a flat 23% for windows and 10% for doors—were audited, revoked, and replaced with exact scheduled opening marks."),
        ("Auditability Over Guesswork", "If a dimension cannot be traced to a specific drawing callout or verified section, it cannot enter the formula calculation stream.")
    ]
    add_bullet_card(s6, Inches(0.8), Inches(1.75), Inches(5.6), Inches(4.9), bullets_s6_left, "Evidence Hierarchy & Tagging")
    add_bullet_card(s6, Inches(6.9), Inches(1.75), Inches(5.6), Inches(4.9), bullets_s6_right, "Governance & Heuristic Purging")

    set_notes(s6, "In quantity surveying, not all numbers have the same authority. We established a 9-tier provenance hierarchy. When an engineer reads a column schedule, that is direct sheet observation. When room bounds are multiplied, that is derived geometry. Crucially, we enforced a strict rule: no assumption may be tagged with high confidence. We also completely eliminated legacy ungrounded heuristics—such as blanket 23% and 10% wall deductions—insisting that every deduction map to scheduled opening marks.")

    # =========================================================================
    # SLIDE 7: System Architecture (Pipeline Diagram)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "System Architecture: 11-Stage Pipeline from Ingestion to Refusal")

    stages = [
        ("Phases 0-2", "INGESTION & AUDIT", "Tender PDFs, Registers & Sheet Legibility Audits"),
        ("Phases 3-5", "CONTROLLED TRANSCRIPTION", "Priority A (Foundation), B (Frame), C (Architecture)"),
        ("Phase 6", "CIVIL RECONCILIATION", "Priority D: Multi-discipline level & boundary matrix"),
        ("Phase 7", "FORMULA MAPPING", "Priority E: IS 1200 formulas linked to input dependencies"),
        ("Phase 8", "REFUSAL GUARDRAIL", "Priority F: Sample takeoff executed; unsafe takeoff blocked")
    ]

    left_start = Inches(0.8)
    box_w = Inches(2.15)
    box_gap = Inches(0.24)
    top_pos = Inches(1.75)
    box_h = Inches(3.5)

    for i, st in enumerate(stages):
        cur_left = left_start + i * (box_w + box_gap)
        box = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cur_left, top_pos, box_w, box_h)
        box.fill.solid()
        box.fill.fore_color.rgb = LIGHT_BG if i < 4 else RGBColor(254, 242, 242)
        box.line.color.rgb = STEEL if i < 4 else ALERT_RED
        box.line.width = Pt(1.5)

        tb = s7.shapes.add_textbox(cur_left + Inches(0.12), top_pos + Inches(0.15), box_w - Inches(0.24), box_h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p1 = tf.paragraphs[0]
        p1.text = st[0]
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = STEEL if i < 4 else ALERT_RED
        p1.space_after = Pt(6)

        p2 = tf.add_paragraph()
        p2.text = st[1]
        p2.font.size = Pt(11)
        p2.font.bold = True
        p2.font.color.rgb = NAVY
        p2.space_after = Pt(10)

        p3 = tf.add_paragraph()
        p3.text = st[2]
        p3.font.size = Pt(10)
        p3.font.color.rgb = CHARCOAL

    # Bottom summary card
    b_card = s7.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(5.5), Inches(11.7), Inches(1.15))
    b_card.fill.solid()
    b_card.fill.fore_color.rgb = LIGHT_BG
    b_card.line.color.rgb = BORDER_COLOR
    b_card.line.width = Pt(1)

    tb_bc = s7.shapes.add_textbox(Inches(1.0), Inches(5.6), Inches(11.3), Inches(0.95))
    tf_bc = tb_bc.text_frame
    tf_bc.word_wrap = True
    p_bc_t = tf_bc.paragraphs[0]
    p_bc_t.text = "CORE PIPELINE PRINCIPLE: MODULAR DECOUPLING OF TRANSCRIPTION AND FORMULAS"
    p_bc_t.font.size = Pt(11)
    p_bc_t.font.bold = True
    p_bc_t.font.color.rgb = NAVY
    p_bc_sub = tf_bc.add_paragraph()
    p_bc_sub.text = "The pipeline decouples raw drawing extraction from mathematical evaluation. Ingestion transcribes entities into relational registers; reconciliation resolves inter-trade clashes; formula dependency checks halt execution if inputs are missing. Full takeoff remains blocked where evidence is missing."
    p_bc_sub.font.size = Pt(10)
    p_bc_sub.font.color.rgb = CHARCOAL

    set_notes(s7, "Here is our 11-stage system architecture. Rather than an ungrounded black-box script, we structure quantity takeoff into discrete, verifiable phases. Phases 3 through 5 extract Foundation, Structural Frame, and Architecture into separate registers. Phase 6 performs cross-register reconciliation. Phase 7 maps IS 1200 measurement rules to input dependencies. Phase 8 executes sample calculations while intercepting and blocking unsafe takeoff.")

    # =========================================================================
    # SLIDE 8: Controlled Transcription & Reconciliation Workflow
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Controlled Transcription & Civil Cross-Register Reconciliation")

    # Box 1: Architecture
    b_ar = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.75), Inches(3.6), Inches(4.9))
    b_ar.fill.solid()
    b_ar.fill.fore_color.rgb = LIGHT_BG
    b_ar.line.color.rgb = STEEL
    b_ar.line.width = Pt(1.5)
    tb_ar = s8.shapes.add_textbox(Inches(1.0), Inches(1.9), Inches(3.2), Inches(4.6))
    tf_ar = tb_ar.text_frame
    tf_ar.word_wrap = True
    p = tf_ar.paragraphs[0]
    p.text = "ARCHITECTURAL REGISTERS"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p.space_after = Pt(8)
    ar_points = [
        ("controlled_opening_register.csv", "10 scheduled door/window types (D1-D3, W1-W4, DW1, V1-V2, SD1-SD4) with width and height callouts."),
        ("controlled_room_register.csv", "5 room archetypes across 4 flats per typical floor with clear length and width dimensions."),
        ("controlled_finish_register.csv", "Flooring, skirting, internal 12mm plaster, and external 18mm waterproof plaster specs."),
        ("controlled_masonry_deduction_register.csv", "Deductions mapped to scheduled opening marks.")
    ]
    for pt in ar_points:
        p = tf_ar.add_paragraph()
        p.text = "•  " + pt[0]
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = STEEL
        p_s = tf_ar.add_paragraph()
        p_s.text = "    " + pt[1]
        p_s.font.size = Pt(9.5)
        p_s.font.color.rgb = CHARCOAL
        p_s.space_after = Pt(4)

    # Box 2: Structural Frame
    b_str = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.8), Inches(1.75), Inches(3.6), Inches(4.9))
    b_str.fill.solid()
    b_str.fill.fore_color.rgb = LIGHT_BG
    b_str.line.color.rgb = STEEL
    b_str.line.width = Pt(1.5)
    tb_str = s8.shapes.add_textbox(Inches(5.0), Inches(1.9), Inches(3.2), Inches(4.6))
    tf_str = tb_str.text_frame
    tf_str.word_wrap = True
    p = tf_str.paragraphs[0]
    p.text = "STRUCTURAL REGISTERS"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p.space_after = Pt(8)
    str_points = [
        ("controlled_foundation_register.csv", "207 bored cast-in-situ piles (600mm dia) and 84 scheduled pile caps with grid locations."),
        ("controlled_column_wall_register.csv", "49 vertical members (16 columns C1-C3, 33 shear walls SW1-SW10) with main bar marks."),
        ("controlled_beam_register.csv", "34 framing beams per floor (PB1-PB34, B1-B34) with longitudinal and shear reinforcement."),
        ("controlled_slab_stair_register.csv", "125mm suspended slabs S1-S2, 150mm stair waist slab.")
    ]
    for pt in str_points:
        p = tf_str.add_paragraph()
        p.text = "•  " + pt[0]
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = STEEL
        p_s = tf_str.add_paragraph()
        p_s.text = "    " + pt[1]
        p_s.font.size = Pt(9.5)
        p_s.font.color.rgb = CHARCOAL
        p_s.space_after = Pt(4)

    # Box 3: Reconciliation Engine
    b_rec = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.8), Inches(1.75), Inches(3.7), Inches(4.9))
    b_rec.fill.solid()
    b_rec.fill.fore_color.rgb = RGBColor(240, 253, 244)
    b_rec.line.color.rgb = MUTED_GREEN
    b_rec.line.width = Pt(1.5)
    tb_rec = s8.shapes.add_textbox(Inches(9.0), Inches(1.9), Inches(3.3), Inches(4.6))
    tf_rec = tb_rec.text_frame
    tf_rec.word_wrap = True
    p = tf_rec.paragraphs[0]
    p.text = "CIVIL RECONCILIATION LAYER"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = MUTED_GREEN
    p.space_after = Pt(8)
    rec_points = [
        ("floor_scope_reconciliation.csv", "Reconciled 9 vertical building datums from Stilt (+0.00m) to Mumty (+24.00m)."),
        ("Height Derivation Resolution", "Proved column heights derive from Architectural Section A-A (3050mm), not structural schedules."),
        ("wall_takeoff_reconciliation_matrix.csv", "Resolves masonry deduction boundaries: masonry spans deduct framing columns and beam soffits."),
        ("structural_architecture_conflict_log.csv", "Flags 54 vs 84 pile cap conflict and unsegregated wall centerlines.")
    ]
    for pt in rec_points:
        p = tf_rec.add_paragraph()
        p.text = "•  " + pt[0]
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = MUTED_GREEN
        p_s = tf_rec.add_paragraph()
        p_s.text = "    " + pt[1]
        p_s.font.size = Pt(9.5)
        p_s.font.color.rgb = CHARCOAL
        p_s.space_after = Pt(4)

    set_notes(s8, "Slide 8 shows our reconciliation layer in action. In real projects, architectural and structural drawings frequently exhibit drafting misalignments. We constructed a floor scope reconciliation matrix reconciling all 9 building levels. For example, Sheet 104 does not print column heights; our reconciliation layer proved that the 3050mm floor height derives from Architectural Section A-A. This proves why isolated drawing extraction fails without cross-register reconciliation.")

    # =========================================================================
    # SLIDE 9: Formula Setup & Refusal Logic (Safe Blocking on Missing Evidence)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Formula Setup & Engineered Refusal: Safe Blocking on Missing Evidence")

    fl_steps = [
        ("IS 1200 FORMULA DEFINITION", "14 standardized civil formulas mapped for concrete, rebar, masonry, and finishes."),
        ("INPUT DEPENDENCY CHECK", "Verify if L, B, H, deduction boundaries, and schedules are 100% complete."),
        ("GUARDRAIL INTERCEPTION", "If any prerequisite input is missing or conflicting, execution is blocked immediately."),
        ("AUDITABLE REFUSAL LOG", "Generates formal Request for Information (RFI) rather than fabricating numbers.")
    ]
    f_w = Inches(2.65)
    f_gap = Inches(0.35)
    f_top = Inches(1.75)
    for idx, f in enumerate(fl_steps):
        c_left = Inches(0.8) + idx * (f_w + f_gap)
        box = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, c_left, f_top, f_w, Inches(2.25))
        box.fill.solid()
        box.fill.fore_color.rgb = LIGHT_BG if idx < 2 else RGBColor(254, 242, 242)
        box.line.color.rgb = STEEL if idx < 2 else ALERT_RED
        box.line.width = Pt(1.5)

        tb = s9.shapes.add_textbox(c_left + Inches(0.15), f_top + Inches(0.15), f_w - Inches(0.3), Inches(1.95))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"STEP {idx+1}: {f[0]}"
        p1.font.size = Pt(10)
        p1.font.bold = True
        p1.font.color.rgb = NAVY if idx < 2 else ALERT_RED
        p1.space_after = Pt(6)
        p2 = tf.add_paragraph()
        p2.text = f[1]
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = CHARCOAL

    add_bullet_card(s9, Inches(0.8), Inches(4.3), Inches(5.6), Inches(2.35), [
        ("Deterministic Dependency Mapping", "Formulas mapped in priority_e_formula_setup link operands directly to registered drawing fields."),
        ("Strict Execution Lock", "All bulk quantity formulas are set to INPUTS_BLOCKED until drawing schedules are complete.")
    ], "Formula Architecture Conforming to IS 1200")

    add_bullet_card(s9, Inches(6.9), Inches(4.3), Inches(5.6), Inches(2.35), [
        ("Safe Blocking on Missing Evidence", "In civil engineering contracts, halting execution when data is omitted protects against litigation and claims."),
        ("Actionable RFI Generation", "The refusal engine outputs structured queries for structural consultants rather than guesses.")
    ], "Engineering Rationale: Refusal as a Safety Feature")

    set_notes(s9, "Slide 9 highlights our refusal engine. In computer science, when a program halts, it is often viewed as an exception. But in civil engineering quantity surveying, halting when drawings lack critical data is the hallmark of professional competence. We mapped 14 standardized IS 1200 formulas into a dependency engine. When the engine attempts to evaluate pile concrete, it discovers that pile lengths are omitted from Sheet 100. Instead of guessing 18 meters, it safely blocks execution due to missing evidence and logs an explicit refusal record.")

    # =========================================================================
    # SLIDE 10: Traceable Sample Quantity Results (NO "ACCURACY" WORDING)
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Traceable Sample Quantity Results: Proof-of-Method")

    sub_bar = s10.shapes.add_textbox(Inches(0.8), Inches(1.48), Inches(11.733), Inches(0.38))
    tf_sub = sub_bar.text_frame
    tf_sub.word_wrap = True
    p_sb = tf_sub.paragraphs[0]
    p_sb.text = "Traceable sample calculations formula-recomputed from controlled dimensions on Sheet AR/TD/005 | Full takeoff remains blocked where evidence is missing."
    p_sb.font.size = Pt(11)
    p_sb.font.bold = True
    p_sb.font.color.rgb = STEEL

    rows = 7
    cols = 6
    t_left = Inches(0.8)
    t_top = Inches(1.92)
    t_width = Inches(11.733)
    t_height = Inches(3.25)
    tbl_shape = s10.shapes.add_table(rows, cols, t_left, t_top, t_width, t_height)
    tbl = tbl_shape.table

    tbl.columns[0].width = Inches(1.8)
    tbl.columns[1].width = Inches(2.3)
    tbl.columns[2].width = Inches(2.0)
    tbl.columns[3].width = Inches(2.2)
    tbl.columns[4].width = Inches(1.8)
    tbl.columns[5].width = Inches(1.633)

    headers = ["Element Tag", "Description", "Observed Dimensions", "Calculation Formula", "Calculated Output", "Provenance"]
    for j, h in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = HEADER_FILL
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    table_data = [
        ["D1", "Toilet Door", "0.800 m x 2.100 m", "width_m x height_m", "1.680 m2", "DERIVED_GEOMETRY"],
        ["W1", "Bedroom Window", "1.200 m x 1.200 m", "width_m x height_m", "1.440 m2", "DERIVED_GEOMETRY"],
        ["DW1", "Door-Window Combo", "2.000 m x 2.100 m", "width_m x height_m", "4.200 m2", "DERIVED_GEOMETRY"],
        ["Living / Dining", "Carpet Area", "5.520 m x 3.970 m", "clear_L x clear_W", "21.914 m2", "DERIVED_GEOMETRY"],
        ["Master Bedroom", "Carpet Area", "3.845 m x 3.220 m", "clear_L x clear_W", "12.381 m2", "DERIVED_GEOMETRY"],
        ["Kitchen", "Carpet Area", "2.580 m x 2.440 m", "clear_L x clear_W", "6.295 m2", "DERIVED_GEOMETRY"]
    ]

    for i, r_data in enumerate(table_data):
        for j, val in enumerate(r_data):
            cell = tbl.cell(i+1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if i % 2 == 0 else LIGHT_BG
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(9.5)
            p.font.color.rgb = CHARCOAL
            if j in [0, 4, 5]:
                p.alignment = PP_ALIGN.CENTER
                p.font.bold = True
                if j == 4:
                    p.font.color.rgb = NAVY

    n_card = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(5.38), Inches(11.733), Inches(1.22))
    n_card.fill.solid()
    n_card.fill.fore_color.rgb = LIGHT_BG
    n_card.line.color.rgb = BORDER_COLOR
    n_card.line.width = Pt(1)

    tb_nc = s10.shapes.add_textbox(Inches(1.0), Inches(5.45), Inches(11.333), Inches(1.05))
    tf_nc = tb_nc.text_frame
    tf_nc.word_wrap = True
    p_nc1 = tf_nc.paragraphs[0]
    p_nc1.text = "METHODOLOGICAL BOUNDARY CERTIFICATION"
    p_nc1.font.size = Pt(10.5)
    p_nc1.font.bold = True
    p_nc1.font.color.rgb = NAVY
    bullets_nc = [
        "Single-Element Verification: Calculations are executed strictly on single isolated units directly observed from Sheet AR/TD/005.",
        "Zero Multiplier Application: Results are intentionally not multiplied by 4 flats/floor or 24 flats/tower to preserve geometric truth.",
        "Full Takeoff Blocked: Bulk quantities (tower concrete, steel tonnage, total brickwork) remain blocked until missing schedules are resolved."
    ]
    for b in bullets_nc:
        p = tf_nc.add_paragraph()
        p.text = "•  " + b
        p.font.size = Pt(9.5)
        p.font.color.rgb = CHARCOAL

    set_notes(s10, "On Slide 10, we present our traceable sample quantity results. Where drawings provide verified geometric dimensions, our formula engine executes deterministic geometry with complete fidelity. For Toilet Door D1, 0.800m by 2.100m gives exactly 1.680 square meters. For Window W1, 1.200m by 1.200m yields 1.440 square meters. For the Living/Dining room, 5.520m by 3.970m yields 21.914 square meters. Notice that we deliberately did not multiply these by 24 flats—because typical flats have shaft and plumbing variations that require floor-wise verification.")

    # =========================================================================
    # SLIDE 11: Limitations & Blocked Scopes (Controlled Evidence Discipline)
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "Project Limitations & Explicitly Blocked Scopes")

    sub11 = s11.shapes.add_textbox(Inches(0.8), Inches(1.48), Inches(11.733), Inches(0.38))
    tf_s11 = sub11.text_frame
    tf_s11.word_wrap = True
    p_s11 = tf_s11.paragraphs[0]
    p_s11.text = "Full takeoff remains blocked across 14 major civil packages due to missing tender schedules."
    p_s11.font.size = Pt(11)
    p_s11.font.bold = True
    p_s11.font.color.rgb = ALERT_RED

    t11_shape = s11.shapes.add_table(6, 4, Inches(0.8), Inches(1.92), Inches(11.733), Inches(3.35))
    t11 = t11_shape.table
    t11.columns[0].width = Inches(2.2)
    t11.columns[1].width = Inches(3.6)
    t11.columns[2].width = Inches(3.4)
    t11.columns[3].width = Inches(2.533)

    h11 = ["Work Package", "Specific Missing Input on Drawings", "Risk of Estimation", "Required Unblocking Action"]
    for j, h in enumerate(h11):
        cell = t11.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = ALERT_RED
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER

    b_data = [
        ["Bored Piling Concrete", "Pile termination depth omitted on Sheet 100; DBR specifies 15m-20m range.", "20% foundation concrete volume variance across 207 piles.", "Issue RFI for structural engineer pile termination schedule."],
        ["RCC Pile Caps", "Visual count on plan shows 54 caps vs 84 caps in margin schedule.", "Punching shear depth & geometry conflict under grouped columns.", "Issue RFI for reconciled pile cap grouping schedule."],
        ["Reinforcement Steel", "Zero Bar Bending Schedules (BBS) issued for piles, caps, beams, or slabs.", "Cut lengths, lap staggering, and crank hooks cannot be derived.", "Obtain contractor/engineer approved BBS shop drawings."],
        ["Brick Masonry", "Floor-wise wall centerline lengths unsegregated; openings unmapped.", "Miscalculation of net brickwork across non-standard partitions.", "Perform room-wise coordinate mapping of partitions."],
        ["Commercials & Schedule", "RITES tender provided only aggregate multi-building Schedule of Quantities.", "No official single-tower contract price or CPM bar chart exists.", "Cost accuracy not calculated; single-tower duration not calculated."]
    ]

    for i, r_data in enumerate(b_data):
        for j, val in enumerate(r_data):
            cell = t11.cell(i+1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if i % 2 == 0 else LIGHT_BG
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(9.5)
            p.font.color.rgb = CHARCOAL
            if j == 0:
                p.font.bold = True
                p.font.color.rgb = NAVY

    c11 = s11.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(5.42), Inches(11.733), Inches(1.18))
    c11.fill.solid()
    c11.fill.fore_color.rgb = LIGHT_BG
    c11.line.color.rgb = BORDER_COLOR
    c11.line.width = Pt(1)

    tb_c11 = s11.shapes.add_textbox(Inches(1.0), Inches(5.5), Inches(11.333), Inches(1.0))
    tf_c11 = tb_c11.text_frame
    tf_c11.word_wrap = True
    p_c11_t = tf_c11.paragraphs[0]
    p_c11_t.text = "ETHICAL QUANTITY SURVEYING & EVIDENCE DISCIPLINE"
    p_c11_t.font.size = Pt(10.5)
    p_c11_t.font.bold = True
    p_c11_t.font.color.rgb = NAVY
    p_c11_sub = tf_c11.add_paragraph()
    p_c11_sub.text = "Full takeoff remains blocked where evidence is missing. Cost accuracy is not calculated, quantity accuracy is not calculated, and BOQ validation was not performed. In public works civil engineering, documenting missing inputs and blocking execution is responsible engineering."
    p_c11_sub.font.size = Pt(9.5)
    p_c11_sub.font.color.rgb = CHARCOAL

    set_notes(s11, "Slide 11 details our project limitations and the 14 blocked scopes. We maintain complete transparency regarding what cannot be calculated with current tender drawings. Full takeoff remains blocked where evidence is missing. Tender drawings are schematic representations; they are not construction shop drawings. Without an engineer-approved Bar Bending Schedule, steel reinforcement cannot be computed deterministically. Acknowledging these gaps is what makes our framework robust and trustworthy.")

    # =========================================================================
    # SLIDE 12: Next Steps and Future Scope (Realistic Roadmap)
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "Future Roadmap: Scaling from Pilot to Multi-Project Benchmark")

    bullets_s12_left = [
        ("Recover Prerequisite Engineering Records", "Obtain official single-tower BOQ breakdown and contractor BBS shop drawings to unblock reinforcement and bulk concrete."),
        ("Multi-Project Cross-Validation", "Apply the evidence-controlled transcription pipeline to a second public works project (CPWD/PSU) for cross-validation.")
    ]
    bullets_s12_right = [
        ("Deploy Interactive Demonstration UI", "Deploy a lightweight Streamlit/FastAPI interface showcasing real-time evidence provenance tracking, reconciliation matrices, and refusal guardrails."),
        ("Complete Building Services Transcription", "Transcribe the 18 registered MEP sheets (plumbing, drainage, firefighting, electrical distribution) to complete the full multi-discipline model.")
    ]
    add_bullet_card(s12, Inches(0.8), Inches(1.75), Inches(5.6), Inches(4.9), bullets_s12_left, "Immediate Engineering Next Steps")
    add_bullet_card(s12, Inches(6.9), Inches(1.75), Inches(5.6), Inches(4.9), bullets_s12_right, "Tooling & Multi-Discipline Vision")

    set_notes(s12, "To conclude: this major project demonstrates that the primary challenge in construction AI is not generating numbers—it is data provenance, document reconciliation, and hallucination control. We have built a verified pilot pipeline that handles complex tender drawings, enforces IS 1200 measurement principles, and blocks unsafe takeoff. Our immediate next steps are recovering the single-tower BOQ and BBS, cross-validating on a second project, deploying the demo interface, and transcribing the 18 MEP sheets. Thank you, and we welcome your questions.")

    out_path = os.path.join("10_Controlled_Transcription", "priority_i_slide_deck", "major_project_review_deck_final.pptx")
    prs.save(out_path)
    print(f"Final polished slide deck successfully created at: {out_path}")
    print(f"Total slides generated: {len(prs.slides)}")

if __name__ == "__main__":
    create_final_deck()

