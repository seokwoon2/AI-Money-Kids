from database.db_manager import DatabaseManager
from typing import List, Dict

class AnalysisService:
    """금융습관 분석 서비스"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def calculate_impulsivity_score(self, behaviors: List[Dict]) -> float:
        """
        충동성 점수 계산 (0-100)
        낮을수록 좋음
        충동구매 횟수 / 전체 소비 횟수 * 100
        """
        if not behaviors:
            return 50.0  # 기본값
        
        # 소비 관련 행동만 필터링
        spending_behaviors = [
            b for b in behaviors 
            if b['behavior_type'] in ['planned_spending', 'impulse_buying']
        ]
        
        if not spending_behaviors:
            return 50.0
        
        impulse_count = sum(
            1 for b in spending_behaviors 
            if b['behavior_type'] == 'impulse_buying'
        )
        
        total_spending = len(spending_behaviors)
        impulsivity_ratio = impulse_count / total_spending if total_spending > 0 else 0.5
        
        # 0-100 점수로 변환 (높을수록 나쁨)
        score = impulsivity_ratio * 100
        
        return round(score, 1)
    
    def calculate_saving_tendency(self, behaviors: List[Dict]) -> float:
        """
        저축성향 점수 계산 (0-100)
        높을수록 좋음
        저축 금액 / (저축 금액 + 소비 금액) * 100
        """
        if not behaviors:
            return 50.0  # 기본값
        
        saving_amount = sum(
            b.get('amount', 0) or 0 
            for b in behaviors 
            if b['behavior_type'] == 'saving'
        )
        
        spending_amount = sum(
            b.get('amount', 0) or 0 
            for b in behaviors 
            if b['behavior_type'] in ['planned_spending', 'impulse_buying']
        )
        
        total_amount = saving_amount + spending_amount
        
        if total_amount == 0:
            # 금액이 없으면 횟수로 계산
            saving_count = sum(1 for b in behaviors if b['behavior_type'] == 'saving')
            spending_count = sum(
                1 for b in behaviors 
                if b['behavior_type'] in ['planned_spending', 'impulse_buying']
            )
            total_count = saving_count + spending_count
            
            if total_count == 0:
                return 50.0
            
            ratio = saving_count / total_count
        else:
            ratio = saving_amount / total_amount
        
        # 0-100 점수로 변환
        score = ratio * 100
        
        return round(score, 1)
    
    def calculate_patience_score(self, behaviors: List[Dict]) -> float:
        """
        인내심 점수 계산 (0-100)
        높을수록 좋음
        (계획적 소비 + 만족 지연) / 전체 소비 횟수 * 100
        """
        if not behaviors:
            return 50.0  # 기본값
        
        # 소비 관련 행동만 필터링
        spending_behaviors = [
            b for b in behaviors 
            if b['behavior_type'] in [
                'planned_spending', 
                'impulse_buying',
                'delayed_gratification',
                'comparing_prices'
            ]
        ]
        
        if not spending_behaviors:
            return 50.0
        
        patient_behaviors = sum(
            1 for b in spending_behaviors 
            if b['behavior_type'] in [
                'planned_spending',
                'delayed_gratification',
                'comparing_prices'
            ]
        )
        
        total_spending = len(spending_behaviors)
        patience_ratio = patient_behaviors / total_spending if total_spending > 0 else 0.5
        
        # 0-100 점수로 변환
        score = patience_ratio * 100
        
        return round(score, 1)
    
    def analyze_and_save(self, user_id: int) -> Dict[str, float]:
        """모든 점수 계산 후 DB 저장"""
        # 최근 30일간의 행동 데이터 가져오기
        behaviors = self.db.get_user_behaviors(user_id, limit=1000)
        
        # 점수 계산
        impulsivity = self.calculate_impulsivity_score(behaviors)
        saving_tendency = self.calculate_saving_tendency(behaviors)
        patience = self.calculate_patience_score(behaviors)
        
        # DB에 저장
        self.db.save_score(user_id, impulsivity, saving_tendency, patience)
        
        return {
            "impulsivity": impulsivity,
            "saving_tendency": saving_tendency,
            "patience": patience
        }
    
    def get_latest_scores(self, user_id: int) -> Dict[str, float]:
        """최신 점수 조회 (없으면 계산)"""
        score = self.db.get_latest_score(user_id)
        
        if score:
            return {
                "impulsivity": score['impulsivity'],
                "saving_tendency": score['saving_tendency'],
                "patience": score['patience']
            }
        else:
            # 점수가 없으면 계산해서 저장
            return self.analyze_and_save(user_id)
