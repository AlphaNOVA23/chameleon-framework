import io
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf_report(all_sessions, system_settings):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=14
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=14,
        spaceAfter=8
    )
    
    normal_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )
    
    story = []
    
    # Title & Header
    story.append(Paragraph("CHAMELEON SOC — Threat Intelligence & Deception Report", title_style))
    now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    story.append(Paragraph(f"Generated: {now_str} | Platform: Chameleon Deception Framework v2.4", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceBefore=0, spaceAfter=14))
    
    # Executive Summary Metrics
    total_sessions = len(all_sessions)
    bots = sum(1 for s in all_sessions if s.get('classification') == 'TIER_1_BOT')
    agents = sum(1 for s in all_sessions if s.get('classification') == 'TIER_2_AGENT')
    humans = sum(1 for s in all_sessions if s.get('classification') == 'TIER_3_HUMAN')
    unknowns = total_sessions - (bots + agents + humans)
    
    tau_bot = system_settings.get('tau_bot', 0.25)
    tau_human = system_settings.get('tau_human', 1.80)
    
    summary_data = [
        ["Total Sessions Monitored", str(total_sessions), "Bot Threshold (τ_bot)", f"<{tau_bot}s"],
        ["Tier 1 Bots Neutralized", str(bots), "Human Threshold (τ_human)", f">{tau_human}s"],
        ["Tier 2 AI Agents Intercepted", str(agents), "Configured Jitter (δ)", f"{system_settings.get('delta_var', 0.08)}s²"],
        ["Tier 3 Humans Trapped", str(humans), "Active Groq Engine", "Llama-3.1-8b-instant"]
    ]
    
    summary_table = Table(summary_data, colWidths=[150, 100, 160, 130])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#0f172a')),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTNAME', (3,0), (3,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('PADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    
    story.append(Paragraph("Executive Summary & Configuration Parameters", h2_style))
    story.append(summary_table)
    story.append(Spacer(1, 14))
    
    # Session Details Table
    story.append(Paragraph("Monitored SSH Attack Sessions", h2_style))
    
    table_headers = ["Session ID", "Source IP", "Classification", "Cmd Count", "Mean IAT", "Status"]
    table_rows = [table_headers]
    
    for s in all_sessions[:20]: # Top 20 sessions
        sid = s.get('session_id', '?')[:10]
        ip = s.get('src_ip', '?')
        cls = s.get('classification', 'UNKNOWN')
        cmds = len(s.get('commands', []))
        iat = s.get('metrics', {}).get('mean_iat', 0)
        iat_str = f"{iat:.3f}s" if iat > 0 else "—"
        status = "CLOSED" if s.get('closed') else "LIVE"
        
        table_rows.append([sid, ip, cls, str(cmds), iat_str, status])
        
    session_table = Table(table_rows, colWidths=[80, 100, 120, 70, 80, 90])
    session_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('PADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f1f5f9')])
    ]))
    
    story.append(session_table)
    story.append(Spacer(1, 14))
    
    # Forensic Recommendations
    story.append(Paragraph("Security Assessment & Recommendations", h2_style))
    recs = (
        "1. High-frequency command bursts (<0.25s IAT) represent automated SSH brute-force scripts; automatically isolated.<br/>"
        "2. Medium-frequency execution (0.25s - 1.8s IAT) indicates automated AI agent reconnaissance; dynamic Groq honeytokens deployed.<br/>"
        "3. High-latency sessions (>1.8s IAT) indicate interactive human adversary activity; active session tarpitting enforced."
    )
    story.append(Paragraph(recs, normal_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
