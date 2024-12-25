# app/core/services/automation_service.py
class AutomationService:
    async def schedule_reconciliation(
        self,
        db: Session,
        org_id: int,
        related_orgs: List[int],
        frequency: str = "daily"
    ):
        """Programa conciliaciones automáticas"""
        schedule = models.ReconciliationSchedule(
            organization_id=org_id,
            related_organizations=related_orgs,
            frequency=frequency,
            next_run=self.calculate_next_run(frequency)
        )
        db.add(schedule)
        await db.commit()
        return schedule

    async def run_reconciliation(
        self,
        db: Session,
        schedule_id: int
    ):
        """Ejecuta conciliación programada"""
        schedule = await self.get_schedule(db, schedule_id)
        
        # Obtener transacciones de todas las organizaciones
        transactions = await self.get_all_transactions(
            db, 
            [schedule.organization_id] + schedule.related_organizations
        )

        # Encontrar coincidencias
        matches = await self.find_matching_transactions(transactions)
        
        # Registrar resultados
        await self.record_reconciliation_results(db, schedule_id, matches)
        
        return matches

    async def find_matching_transactions(
        self,
        transactions: List[Dict]
    ) -> List[Dict]:
        """Encuentra transacciones coincidentes entre organizaciones"""
        matches = []
        
        # Agrupar por monto y fecha aproximada
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        
        # Encontrar coincidencias por monto (con tolerancia para diferencias de cambio)
        for amount in df['amount'].unique():
            potential_matches = df[
                (df['amount'].between(amount * 0.99, amount * 1.01)) &
                (df['type'].isin(['invoice', 'bill', 'payment']))
            ]
            
            if len(potential_matches) >= 2:
                # Verificar si las fechas están cercanas
                for _, group in potential_matches.groupby('organization_id'):
                    for _, row1 in group.iterrows():
                        for _, row2 in potential_matches[
                            potential_matches['organization_id'] != row1['organization_id']
                        ].iterrows():
                            if abs((row1['date'] - row2['date']).days) <= 5:
                                matches.append({
                                    'transaction1': row1.to_dict(),
                                    'transaction2': row2.to_dict(),
                                    'confidence': self.calculate_confidence(row1, row2)
                                })

        return matches

    def calculate_confidence(self, tx1: pd.Series, tx2: pd.Series) -> float:
        """Calcula nivel de confianza para coincidencia"""
        confidence = 0.0
        
        # Monto exacto
        if abs(tx1['amount'] - tx2['amount']) < 0.01:
            confidence += 0.4
        
        # Fecha cercana
        days_diff = abs((tx1['date'] - tx2['date']).days)
        if days_diff == 0:
            confidence += 0.3
        elif days_diff <= 2:
            confidence += 0.2
        elif days_diff <= 5:
            confidence += 0.1
            
        # Descripción similar
        if tx1['description'] and tx2['description']:
            similarity = cosine_similarity(
                [self.text_to_vector(tx1['description'])],
                [self.text_to_vector(tx2['description'])]
            )[0][0]
            confidence += similarity * 0.3
            
        return min(confidence, 1.0)