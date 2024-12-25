# app/core/services/ai_service.py
from typing import List, Dict
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timezone

class AIService:
    def __init__(self):
        self.industry_patterns = {
            "retail": ["inventory", "pos", "ecommerce"],
            "professional_services": ["projects", "expenses", "timesheets"],
            "manufacturing": ["inventory", "fixed_assets", "purchase_orders"],
            "healthcare": ["payroll", "expenses", "reports"]
        }

    async def analyze_organization(
        self,
        industry: str,
        size: int,
        current_modules: List[str]
    ) -> Dict:
        """Analiza una organización y recomienda módulos"""
        recommendations = {
            "recommended_modules": [],
            "urgency_level": "low",
            "reason": "",
            "potential_benefits": []
        }

        # Obtener módulos recomendados para la industria
        industry_recommended = self.industry_patterns.get(industry.lower(), [])
        
        # Identificar módulos faltantes importantes
        missing_modules = [
            module for module in industry_recommended 
            if module not in current_modules
        ]

        if missing_modules:
            recommendations["recommended_modules"] = missing_modules
            recommendations["urgency_level"] = "medium"
            recommendations["reason"] = f"Módulos típicos de {industry} no implementados"
            recommendations["potential_benefits"] = await self.calculate_benefits(
                industry, missing_modules, size
            )

        return recommendations

    async def calculate_benefits(
        self, 
        industry: str, 
        missing_modules: List[str], 
        org_size: int
    ) -> List[Dict]:
        """Calcula beneficios potenciales de implementar módulos"""
        benefits = []
        
        benefit_metrics = {
            "inventory": {
                "time_saved": "4-6 horas/semana",
                "error_reduction": "85%",
                "cost_saving": "15-20%"
            },
            "projects": {
                "time_saved": "6-8 horas/semana",
                "efficiency_gain": "30%",
                "revenue_impact": "10-15%"
            }
            # Más métricas según módulo
        }

        for module in missing_modules:
            if module in benefit_metrics:
                benefits.append({
                    "module": module,
                    "metrics": benefit_metrics[module],
                    "roi_period": "3-6 meses"
                })

        return benefits