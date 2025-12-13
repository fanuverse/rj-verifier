import sys
import os
import json
import logging
import argparse
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("RJ_Verifier_Engine")

try:
    from k12.sheerid_verifier import SheerIDVerifier
    from k12.config import SCHOOLS
except ImportError as e:
    logger.error(f"Import Error: {e}")
    sys.exit(1)

def get_default_docs_path(subfolder):
    docs_path = Path(os.path.expanduser('~')) / 'Documents' / 'RJ Verifier' / subfolder
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)
    return docs_path

def run_verify(args):
    logger.info(f"Starting verification for: {args.get('firstName')} {args.get('lastName')}")
    
    verifier = SheerIDVerifier(args.get('verificationId', ''))
    school_id = args.get('schoolId')
    
    backup_path = args.get('savePath')
    if not backup_path:
        backup_path = str(get_default_docs_path('doc_backup verifier'))

    try:
        result = verifier.verify(
            first_name=args.get('firstName'),
            last_name=args.get('lastName'),
            email=args.get('email'), 
            birth_date=args.get('birthDate'), 
            school_id=school_id,
            doc_type=args.get('docType', 'pdf'),
            doc_style=args.get('docStyle', 'modern'),
            backup_path=backup_path
        )
        
        print(json.dumps(result))
        
    except Exception as e:
        logger.error(f"Verification Failed: {e}")
        error_res = {'success': False, 'message': str(e)}
        print(json.dumps(error_res))

def get_schools():
    schools_list = []
    for sid, data in SCHOOLS.items():
        schools_list.append({
            'id': sid,
            'name': data['name'],
            'country': data['country']
        })
    print(json.dumps(schools_list))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', choices=['verify', 'get_schools', 'generate_docs'], required=True)
    parser.add_argument('--data', type=str, help='JSON string of data')
    
    args = parser.parse_args()
    
    if args.action == 'get_schools':
        get_schools()
    elif args.action == 'verify':
        if not args.data:
            logger.error("No data provided for verify")
            sys.exit(1)
        data = json.loads(args.data)
        run_verify(data)
    elif args.action == 'generate_docs':
        if not args.data:
            logger.error("No data provided for generate_docs")
            sys.exit(1)
        data = json.loads(args.data)
        
        from k12.img_generator import generate_teacher_pdf, generate_teacher_png
        from k12.name_generator import NameGenerator
        
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        
        if not first_name or not last_name:
            n = NameGenerator.generate()
            first_name = first_name or n['first_name']
            last_name = last_name or n['last_name']
            
        school_name = data.get('schoolName') or "Springfield High School"
        address = data.get('address') or "123 Education Lane, Springfield, US 99999" 
        
        logo_path = data.get('logoPath')
        if not logo_path or not Path(logo_path).exists():
             logo_path = config.get_assets_dir() / 'SHS.png'
             if not logo_path.exists():
                 logo_path = None

        doc_type = data.get('docType', 'pdf')
        doc_style = data.get('docStyle', 'modern')
        
        save_path_str = data.get('savePath')
        if save_path_str:
            save_dir = Path(save_path_str)
        else:
            save_dir = get_default_docs_path('doc_generated')
            
        if not save_dir.exists():
            save_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        try:
            if doc_type in ['pdf', 'both']:
                pdf_bytes = generate_teacher_pdf(first_name, last_name, school_name, address, style=doc_style, logo_path=logo_path)
                fname = f"Payslip {first_name} {last_name}.pdf"
                out_path = save_dir / fname
                out_path.write_bytes(pdf_bytes)
                generated_files.append(str(out_path))
                logger.info(f"Generated PDF: {out_path}")
                
            if doc_type in ['png', 'both']:
                png_bytes = generate_teacher_png(first_name, last_name, school_name, address, style=doc_style, logo_path=logo_path)
                fname = f"Payslip {first_name} {last_name}.png"
                out_path = save_dir / fname
                out_path.write_bytes(png_bytes)
                generated_files.append(str(out_path))
                logger.info(f"Generated PNG: {out_path}")
                
            print(json.dumps({"success": True, "files": generated_files, "message": f"Generated {len(generated_files)} files"}))
            
        except Exception as e:
             logger.error(f"Generate Docs Failed: {e}")
             print(json.dumps({"success": False, "message": str(e)}))
