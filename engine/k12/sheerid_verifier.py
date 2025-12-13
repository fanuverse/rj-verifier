import re
import random
import logging
import httpx
from typing import Dict, Optional, Tuple
from pathlib import Path
import os
try:
    from . import config
    from .name_generator import NameGenerator, generate_email, generate_birth_date
    from .img_generator import generate_teacher_pdf, generate_teacher_png
except ImportError:
    import config
    from name_generator import NameGenerator, generate_email, generate_birth_date
    from img_generator import generate_teacher_pdf, generate_teacher_png

HTTP_PROXY = os.getenv("HTTP_PROXY", "")
PROGRAM_ID = config.PROGRAM_ID
SHEERID_BASE_URL = config.SHEERID_BASE_URL
MY_SHEERID_URL = config.MY_SHEERID_URL
HCAPTCHA_SECRET = config.HCAPTCHA_SECRET
TURNSTILE_SECRET = config.TURNSTILE_SECRET
SCHOOLS = config.SCHOOLS
DEFAULT_SCHOOL_ID = config.DEFAULT_SCHOOL_ID

logger = logging.getLogger(__name__)


class SheerIDVerifier:

    def __init__(self, verification_id: str):
        match_param = re.search(r'verificationId=([a-f0-9]{24})', verification_id, re.IGNORECASE)
        if match_param:
            self.verification_id = match_param.group(1)
            logger.info(f"Auto-extracted verification ID: {self.verification_id}")
        else:
             self.verification_id = verification_id.strip()

        self.device_fingerprint = self._generate_device_fingerprint()
        proxies = None
        if HTTP_PROXY:
            proxies = HTTP_PROXY
        
        self.http_client = httpx.Client(timeout=30.0, proxy=proxies)

    def __del__(self):
        if hasattr(self, 'http_client'):
            self.http_client.close()

    @staticmethod
    def _generate_device_fingerprint() -> str:
        chars = '0123456789abcdef'
        return ''.join(random.choice(chars) for _ in range(32))

    @staticmethod
    def normalize_url(url: str) -> str:
        return url

    @staticmethod
    def parse_verification_id(url: str) -> Optional[str]:
        match = re.search(r'verificationId=([a-f0-9]+)', url, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def verify_hcaptcha(self, token: str) -> bool:
        if not HCAPTCHA_SECRET or not token:
            return not HCAPTCHA_SECRET

        try:
            response = self.http_client.post(
                'https://hcaptcha.com/siteverify',
                data={
                    'response': token,
                    'secret': HCAPTCHA_SECRET
                },
                headers=headers
            )
            result = response.json()
            return result.get('success', False)
        except Exception as e:
            logger.error(f"hCaptcha verify failed: {e}")
            return False

    def verify_turnstile(self, token: str) -> bool:
        if not TURNSTILE_SECRET or not token:
            return not TURNSTILE_SECRET

        try:
            response = self.http_client.post(
                'https://challenges.cloudflare.com/turnstile/v0/siteverify',
                data={
                    'secret': TURNSTILE_SECRET,
                    'response': token
                }
            )
            result = response.json()
            return result.get('success', False)
        except Exception as e:
            logger.error(f"Turnstile verify failed: {e}")
            return False

    def _sheerid_request(self, method: str, url: str,
                         body: Optional[Dict] = None) -> Tuple[Dict, int]:
        headers = {
            'Content-Type': 'application/json',
        }

        try:
            response = self.http_client.request(
                method=method,
                url=url,
                json=body,
                headers=headers
            )

            try:
                data = response.json()
            except Exception:
                data = response.text

            return data, response.status_code
        except Exception as e:
            logger.error(f"SheerID request failed: {e}")
            raise

    def _upload_to_s3(self, upload_url: str, content: bytes, mime_type: str) -> bool:
        try:
            headers = {
                'Content-Type': mime_type,
            }
            response = self.http_client.put(
                upload_url,
                content=content,
                headers=headers,
                timeout=60.0
            )
            return 200 <= response.status_code < 300
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return False

    def verify(self, first_name: str = None, last_name: str = None,
               email: str = None, birth_date: str = None, 
               school_id: str = None,
               doc_type: str = 'pdf', doc_style: str = 'modern',
               hcaptcha_token: str = None, turnstile_token: str = None, backup_path: str = None) -> Dict:
        try:
            current_step = 'initial'
            if HCAPTCHA_SECRET:
                logger.info("Verify hCaptcha...")
                if not self.verify_hcaptcha(hcaptcha_token):
                    raise Exception("hCaptcha verify failed")
                logger.info("hCaptcha verified")

            if TURNSTILE_SECRET:
                logger.info("Verify Turnstile...")
                if not self.verify_turnstile(turnstile_token):
                    raise Exception("Turnstile verify failed")
                logger.info("Turnstile verified")

            if not first_name or not last_name:
                name_data = NameGenerator.generate()
                first_name = name_data['first_name']
                last_name = name_data['last_name']
            
            if not birth_date:
                birth_date = generate_birth_date()

            if not school_id:
                school_id = random.choice(list(SCHOOLS.keys()))
                logger.info(f"Randomly selected school ID: {school_id}")
            
            if school_id not in SCHOOLS:
                 school_id = random.choice(list(SCHOOLS.keys()))
            school = SCHOOLS[school_id]

            if not email:
                domain = school.get('domain', 'springfield.k12.or.us')
                email = generate_email(first_name, last_name, domain)

            logger.info(f"Teacher Info: {first_name} {last_name}")
            logger.info(f"Email: {email}")
            logger.info(f"School: {school['name']}")
            logger.info(f"DOB: {birth_date}")
            logger.info(f"Verification ID: {self.verification_id}")

            school_info = SCHOOLS.get(school_id, SCHOOLS[DEFAULT_SCHOOL_ID])
            school_name = school_info.get('name', 'Springfield High School')
            school_address = school_info.get('address', '640 A St, Springfield, OR 97477')
            
            if "(" in school_name:
                school_name_clean = school_name.split("(")[0].strip()
            else:
                school_name_clean = school_name

            logger.info(f"Generating document ({school_name_clean})...")
            
            generated_files = []
            if doc_type == 'both' or doc_type == 'pdf':
                pdf_bytes = generate_teacher_pdf(first_name, last_name, school_name_clean, school_address, style=doc_style)
                generated_files.append((pdf_bytes, 'application/pdf', f"Payslip {first_name} {last_name}.pdf"))
                
            if doc_type == 'both' or doc_type == 'png':
                png_bytes = generate_teacher_png(first_name, last_name, school_name_clean, school_address, style=doc_style)
                generated_files.append((png_bytes, 'image/png', f"Payslip {first_name} {last_name}.png"))

            try:
                import tempfile
                backup_dir = Path(tempfile.gettempdir()) / "rj_verifier_backup"
                backup_dir.mkdir(parents=True, exist_ok=True)
                for content, _, fname in generated_files:
                    backup_path = backup_dir / fname
                    backup_path.write_bytes(content)
                    logger.info(f"Backup: {fname}")
            except Exception as e:
                logger.error(f"Backup failed: {e}") 

            if not generated_files:
                return {'success': False, 'message': 'No documents generated'}

            logger.info("Submitting personal info...")
            step2_body = {
                'firstName': first_name,
                'lastName': last_name,
                'email': email,
                'birthDate': birth_date,
                'organization': {
                    'id': int(school_id),
                    'idExtended': school.get('idExtended', school_id),
                    'name': school['name']
                },
                'deviceFingerprintHash': self.device_fingerprint,
                'metadata': {
                    'verificationId': self.verification_id,
                    'submissionOptIn': 'By submitting the personal information above, I acknowledge that my personal information is being collected under the privacy policy of the business from which I am seeking a discount'
                }
            }

            step2_data, step2_status = self._sheerid_request(
                'POST',
                f"{SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/collectTeacherPersonalInfo",
                step2_body
            )

            if step2_status != 200:
                raise Exception(f"Failed (Status {step2_status}): {step2_data}")

            if step2_data.get('currentStep') == 'error':
                error_msg = ', '.join(step2_data.get('errorIds', ['Unknown error']))
                raise Exception(f"Error: {error_msg}")

            logger.info(f"Complete: {step2_data.get('currentStep')}")
            current_step = step2_data.get('currentStep', current_step)

            if current_step in ['sso', 'collectTeacherPersonalInfo']:
                logger.info("Skipping SSO...")
                step3_data, _ = self._sheerid_request(
                    'DELETE',
                    f"{SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/sso"
                )
                logger.info(f"Complete: {step3_data.get('currentStep')}")
                current_step = step3_data.get('currentStep', current_step)

            logger.info("Uploading document...")
            
            files_metadata = []
            for content, mime, fname in generated_files:
                files_metadata.append({
                    'fileName': fname, 
                    'mimeType': mime,
                    'fileSize': len(content)
                })

            step4_body = {'files': files_metadata}

            step4_data, step4_status = self._sheerid_request(
                'POST',
                f"{SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/docUpload",
                step4_body
            )

            if step4_status != 200:
                raise Exception(f"Upload init failed (Status {step4_status}): {step4_data}")
            
            documents = step4_data.get('documents', [])
            if len(documents) != len(generated_files):
                logger.warning("Mismatch in requested vs returned upload URLs")

            for i, doc_info in enumerate(documents):
                upload_url = doc_info['uploadUrl']
                file_content, mime, _ = generated_files[i]
                
                if not self._upload_to_s3(upload_url, file_content, mime):
                     raise Exception(f"Upload failed for file {i+1}")
                logger.info(f"File {i+1} uploaded successfully")

            step6_data, _ = self._sheerid_request(
                'POST',
                f"{SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/completeDocUpload"
            )
            logger.info(f" Document submitted: {step6_data.get('currentStep')}")
            final_status = step6_data

            return {
                'success': True,
                'pending': True,
                'redirect_url': final_status.get('redirectUrl'),
                'raw_status': final_status
            }

        except Exception as e:
            logger.error(f"Verification failed")
            return {
                'success': False,
                'message': str(e),
                'verification_id': self.verification_id
            }
