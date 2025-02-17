window.XeroBalanceService = (function () {
    async function getAccountBalance(tenantId, accountCode, startDate, endDate) {
        try {
            console.log("🔍 Consultando saldos para:", {
                tenantId,
                accountCode,
                startDate,
                endDate
            });
 
            // Obtener saldos inicial y final
            const [initialBalance, finalBalance] = await Promise.all([
                getBalanceAtDate(tenantId, accountCode, startDate),
                getBalanceAtDate(tenantId, accountCode, endDate)
            ]);
 
            console.log("✅ Saldos recibidos:", {
                initialBalance,
                finalBalance
            });
 
            return {
                initialBalance: initialBalance,
                finalBalance: finalBalance,
                difference: finalBalance - initialBalance
            };
        } catch (error) {
            console.error("❌ Error en getAccountBalance:", error);
            throw error;
        }
    }
 
    async function getBalanceAtDate(tenantId, accountCode, date) {
        try {
            console.log(`🔍 Buscando saldo para cuenta ${accountCode} en fecha ${date}`);
            
            // Primero obtener el mapping
            const mappingResponse = await fetch(`/api/account-mapping/${tenantId}/${accountCode}`);
            if (!mappingResponse.ok) {
                console.error('Error response:', await mappingResponse.text());
                throw new Error("Error obteniendo el mapping de la cuenta.");
            }
            
            const mappingData = await mappingResponse.json();
            const accountId = mappingData.account_id;
            
            if (!accountId) {
                throw new Error("No se encontró el account_id asociado.");
            }
 
            console.log(`✅ account_id encontrado: ${accountId}`);
 
            // Luego obtener el balance
            const balanceResponse = await fetch(
                `/xero/account-balance/${accountId}?tenant_id=${tenantId}&date=${date}`
            );
            if (!balanceResponse.ok) {
                console.error('Error response:', await balanceResponse.text());
                throw new Error("Error obteniendo el balance de la cuenta.");
            }
 
            const balanceData = await balanceResponse.json();
            console.log("✅ Balance recibido:", balanceData);
            
            return balanceData.balance || 0;
 
        } catch (error) {
            console.error("❌ Error en getBalanceAtDate:", error);
            return null;
        }
    }
 
    function getBalanceFromXeroData(xeroData, accountId) {
        for (const section of xeroData.Rows || []) {
            if (section.RowType === "Section") {
                for (const row of section.Rows || []) {
                    const cells = row.Cells || [];
    
                    if (cells[0] && cells[0].Attributes) {
                        const hasAccount = cells[0].Attributes.some(
                            attr => attr.Value === accountId && attr.Id === "account"
                        );
    
                        if (hasAccount) {
                            return parseFloat(cells[1]?.Value || "0.00");
                        }
                    }
                }
            }
        }
        return null;
    }
    
    return {
        getAccountBalance,
        getBalanceFromXeroData
    };
 })();