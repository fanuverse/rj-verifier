import random
from datetime import datetime
from io import BytesIO
from pathlib import Path
import itertools
import base64
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    pass

def _render_template(html: str, first_name: str, last_name: str, school_name: str, address: str, logo_path: str = None) -> str:
    full_name = f"{first_name} {last_name}"
    employee_id = random.randint(1000000, 9999999)
    advice_id = random.randint(10000000, 99999999)
    now = datetime.now()
    pay_date = now.strftime("%m/%d/%Y")
    period_end = now.strftime("%m/%d/%Y")
    
    from datetime import timedelta
    period_start_dt = now - timedelta(days=14)
    period_start = period_start_dt.strftime("%m/%d/%Y")
    pay_month = now.strftime("%B %Y")
    
    if logo_path:
         final_logo_path = Path(logo_path)
    else:
        if "Malcolm X" in school_name or "Chicago" in school_name:
            logo_filename = "MXC.png"
        else:
            logo_filename = "SHS.png"
        
        try:
             from . import config
        except ImportError:
             import config
             
        assets_dir = config.get_assets_dir()
        possible_paths = [
            assets_dir / logo_filename,
            assets_dir / "aassetlogo.png"
        ]
        
        final_logo_path = None
        for p in possible_paths:
            if p.exists():
                final_logo_path = p
                break
                
    hourly_rate = round(random.uniform(34.50, 42.50), 2)
    hours_worked = round(random.uniform(78.0, 82.0), 2)
    regular_pay = round(hourly_rate * hours_worked, 2)
    
    stipend = random.choice([0, 50, 100, 150, 75])
    gross_pay = regular_pay + stipend
    fed_tax_rate = random.uniform(0.10, 0.12)
    ss_tax_rate = 0.062 
    med_tax_rate = 0.0145
    state_tax_rate = random.uniform(0.03, 0.045)
    
    fed_tax = round(gross_pay * fed_tax_rate, 2)
    ss_tax = round(gross_pay * ss_tax_rate, 2)
    med_tax = round(gross_pay * med_tax_rate, 2)
    state_tax = round(gross_pay * state_tax_rate, 2)
    
    total_deductions = fed_tax + ss_tax + med_tax + state_tax
    net_pay = gross_pay - total_deductions
    def fmt(val):
        return f"{val:,.2f}"
    
    if final_logo_path and final_logo_path.exists():
        encoded_logo = base64.b64encode(final_logo_path.read_bytes()).decode('utf-8')
        logo_data_uri = f"data:image/png;base64,{encoded_logo}"
    else:
        logo_data_uri = "" 

    html = html.replace("__LOGO_DATA_URI__", logo_data_uri)
    html = html.replace("LOGO_DATA_URI_PLACEHOLDER", logo_data_uri) 
    html = html.replace("__SCHOOL_NAME__", school_name)
    html = html.replace("__SCHOOL_ADDRESS__", address)
    html = html.replace("__EMP_NAME__", full_name)
    html = html.replace("__EMP_ID__", f"E-{employee_id}")
    html = html.replace("__ADVICE_ID__", str(advice_id))
    html = html.replace("__PAY_DATE__", pay_date)
    html = html.replace("__PAY_MONTH__", pay_month)
    html = html.replace("__PERIOD_START__", period_start)
    html = html.replace("__PERIOD_END__", period_end)
    html = html.replace("__REG_PAY__", fmt(regular_pay))
    html = html.replace("__OTHER_PAY__", fmt(stipend))
    html = html.replace("__GROSS_PAY__", fmt(gross_pay))
    html = html.replace("__FED_TAX__", fmt(fed_tax))
    html = html.replace("__SS_TAX__", fmt(ss_tax))
    html = html.replace("__MED_TAX__", fmt(med_tax))
    html = html.replace("__STATE_TAX__", fmt(state_tax))
    html = html.replace("__TOTAL_DED__", fmt(total_deductions))
    html = html.replace("__NET_PAY__", fmt(net_pay))
    html = html.replace("__HOURLY_RATE__", fmt(hourly_rate))
    html = html.replace("__HOURS_WORKED__", fmt(hours_worked))

    return html


def generate_teacher_pdf(first_name: str, last_name: str, school_name: str = "Springfield High School") -> bytes:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright required for PDF generation") from exc
import itertools
_TEMPLATE_CYCLE = None

def _get_template_file_by_style(templates_dir: Path, style: str) -> Path:
    """Select template based on style name"""
    style_map = {
        'modern': 'template_modern.html',
        'original': 'template_original.html',
        'simple': 'template_simple.html',
        'portal': 'template_portal.html'
    }
    filename = style_map.get(style, 'template_modern.html')
    return templates_dir / filename

def generate_teacher_pdf(first_name: str, last_name: str, school_name: str = "Springfield High School", address: str = "640 A St, Springfield, OR 97477", style: str = "modern", logo_path: str = None) -> bytes:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright required for PDF generation") from exc
        
    try:
        from . import config
    except ImportError:
        import config
    templates_dir = config.get_templates_dir()
    if not templates_dir.exists():
        templates_dir.mkdir(parents=True, exist_ok=True)
        
    template_file = _get_template_file_by_style(templates_dir, style)
    if not template_file.exists():
        template_file = templates_dir / "template_modern.html"
        
    html_content = template_file.read_text(encoding="utf-8")
    
    html = _render_template(html_content, first_name, last_name, school_name, address, logo_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 816, "height": 1056}) 
        page.set_content(html, wait_until="load")
        page.wait_for_timeout(500)
        pdf_bytes = page.pdf(format="Letter", print_background=True, margin={"top": "0.4in", "right": "0.4in", "bottom": "0.4in", "left": "0.4in"})
        browser.close()
        
    return pdf_bytes


def generate_teacher_png(first_name: str, last_name: str, school_name: str = "Springfield High School", address: str = "640 A St, Springfield, OR 97477", style: str = "modern", logo_path: str = None) -> bytes:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright required") from exc
        
    try:
        from . import config
    except ImportError:
        import config
    templates_dir = config.get_templates_dir()
    template_file = _get_template_file_by_style(templates_dir, style)
    if not template_file.exists():
         template_file = templates_dir / "template_modern.html"
    
    html_content = template_file.read_text(encoding="utf-8")
    html = _render_template(html_content, first_name, last_name, school_name, address, logo_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1000, "height": 1200})
        page.set_content(html, wait_until="load")
        page.wait_for_timeout(500)
        card = page.locator("body") 
        png_bytes = card.screenshot(type="png")
        browser.close()
    
    return png_bytes
def generate_teacher_image(first_name: str, last_name: str, school_name: str = "Springfield High School") -> bytes:
    return generate_teacher_pdf(first_name, last_name, school_name)
