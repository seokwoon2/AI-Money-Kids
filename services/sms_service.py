"""
SMS 인증 서비스
휴대폰 번호 인증을 처리합니다.
"""
import os
import streamlit as st
import random
import string
from typing import Optional, Dict
from datetime import datetime, timedelta

# 실제 SMS 발송을 위한 서비스 (나중에 연동 가능)
# 예: CoolSMS, 알리고, Twilio 등


class SMSService:
    """
    SMS 인증 서비스 클래스
    개발 환경에서는 인증번호를 세션에 저장하고, 실제 SMS는 발송하지 않습니다.
    운영 환경에서는 실제 SMS 발송 서비스를 연동해야 합니다.
    """
    
    def __init__(self):
        """SMS 서비스 초기화"""
        # 실제 SMS 발송을 위한 API 키 설정 (나중에 추가)
        # self.api_key = os.getenv('SMS_API_KEY')
        # self.api_secret = os.getenv('SMS_API_SECRET')
        pass
    
    def generate_verification_code(self, length: int = 6) -> str:
        """
        인증번호 생성
        
        Args:
            length: 인증번호 길이 (기본 6자리)
            
        Returns:
            str: 생성된 인증번호
        """
        return ''.join(random.choices(string.digits, k=length))
    
    def send_verification_code(self, phone_number: str) -> Dict[str, any]:
        """
        인증번호를 SMS로 발송
        
        Args:
            phone_number: 휴대폰 번호 (010-1234-5678 형식)
            
        Returns:
            dict: 발송 결과 {'success': bool, 'code': str, 'message': str}
        """
        # 전화번호 형식 검증
        phone_clean = phone_number.replace('-', '').replace(' ', '')
        if not phone_clean.isdigit() or len(phone_clean) not in [10, 11]:
            return {
                'success': False,
                'code': None,
                'message': '올바른 휴대폰 번호를 입력해주세요.'
            }
        
        # 인증번호 생성
        verification_code = self.generate_verification_code()
        
        # 세션에 저장 (만료 시간: 5분)
        if 'sms_verification' not in st.session_state:
            st.session_state.sms_verification = {}
        
        st.session_state.sms_verification[phone_clean] = {
            'code': verification_code,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=5),
            'verified': False,
            'attempts': 0
        }
        
        # 실제 SMS 발송 (운영 환경에서 활성화)
        # 실제 구현 예시:
        # try:
        #     # CoolSMS, 알리고 등의 API 호출
        #     response = send_sms_api(phone_number, f"[AI Money Friends] 인증번호는 {verification_code}입니다.")
        #     if response['success']:
        #         return {
        #             'success': True,
        #             'code': verification_code,  # 개발 환경에서만 반환
        #             'message': '인증번호가 발송되었습니다.'
        #         }
        # except Exception as e:
        #     return {
        #         'success': False,
        #         'code': None,
        #         'message': f'SMS 발송 실패: {str(e)}'
        #     }
        
        # 개발 환경: 인증번호를 직접 반환 (실제로는 SMS로 발송)
        # 실제 SMS 발송 코드는 여기에 추가 가능
        # 예: CoolSMS, 알리고 등의 API 호출
        
        return {
            'success': True,
            'code': verification_code,  # 개발 환경에서만 표시
            'message': '인증번호가 발송되었습니다.'
        }
    
    def verify_code(self, phone_number: str, input_code: str) -> Dict[str, any]:
        """
        입력된 인증번호 검증
        
        Args:
            phone_number: 휴대폰 번호
            input_code: 사용자가 입력한 인증번호
            
        Returns:
            dict: 검증 결과 {'success': bool, 'message': str}
        """
        phone_clean = phone_number.replace('-', '').replace(' ', '')
        
        if 'sms_verification' not in st.session_state:
            return {
                'success': False,
                'message': '인증번호를 먼저 발송해주세요.'
            }
        
        if phone_clean not in st.session_state.sms_verification:
            return {
                'success': False,
                'message': '인증번호를 먼저 발송해주세요.'
            }
        
        verification_data = st.session_state.sms_verification[phone_clean]
        
        # 만료 확인
        if datetime.now() > verification_data['expires_at']:
            del st.session_state.sms_verification[phone_clean]
            return {
                'success': False,
                'message': '인증번호가 만료되었습니다. 다시 발송해주세요.'
            }
        
        # 시도 횟수 확인 (최대 5회)
        if verification_data['attempts'] >= 5:
            del st.session_state.sms_verification[phone_clean]
            return {
                'success': False,
                'message': '인증번호 입력 시도 횟수를 초과했습니다. 다시 발송해주세요.'
            }
        
        # 인증번호 확인
        verification_data['attempts'] += 1
        
        if verification_data['code'] == input_code:
            verification_data['verified'] = True
            return {
                'success': True,
                'message': '인증이 완료되었습니다.'
            }
        else:
            remaining = 5 - verification_data['attempts']
            return {
                'success': False,
                'message': f'인증번호가 일치하지 않습니다. (남은 시도: {remaining}회)'
            }
    
    def is_verified(self, phone_number: str) -> bool:
        """
        해당 번호가 인증되었는지 확인
        
        Args:
            phone_number: 휴대폰 번호
            
        Returns:
            bool: 인증 여부
        """
        phone_clean = phone_number.replace('-', '').replace(' ', '')
        
        if 'sms_verification' not in st.session_state:
            return False
        
        if phone_clean not in st.session_state.sms_verification:
            return False
        
        verification_data = st.session_state.sms_verification[phone_clean]
        
        # 만료 확인
        if datetime.now() > verification_data['expires_at']:
            return False
        
        return verification_data.get('verified', False)
    
    def clear_verification(self, phone_number: str):
        """
        인증 정보 삭제
        
        Args:
            phone_number: 휴대폰 번호
        """
        phone_clean = phone_number.replace('-', '').replace(' ', '')
        
        if 'sms_verification' in st.session_state:
            if phone_clean in st.session_state.sms_verification:
                del st.session_state.sms_verification[phone_clean]
