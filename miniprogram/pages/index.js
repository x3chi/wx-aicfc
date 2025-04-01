Page({
  data: {},
  formSubmit: function(e) {
    const data = e.detail.value;
    let constructionYears = parseInt(data.constructionYears);
    let operationYears = parseInt(data.operationYears);
    let loanRatio = parseFloat(data.loanRatio) / 100;
    let loanRate = parseFloat(data.loanRate) / 100;
    let serverCount = parseInt(data.serverCount);
    // 所有金额均为万元
    let serverUnitPrice = parseFloat(data.serverUnitPrice);
    let rent = parseFloat(data.rent);
    let equipmentRentalRate = parseFloat(data.equipmentRentalRate) / 100;
    let equipmentResidualRate = parseFloat(data.equipmentResidualRate) / 100;
    let serverRoomCost = parseFloat(data.serverRoomCost);
    let internetFee = parseFloat(data.internetFee);
    let maintenanceCostPerServer = parseFloat(data.maintenanceCostPerServer);
    let additionalTaxRate = parseFloat(data.additionalTaxRate) / 100;
    
    // 固定税率及增值税率
    let incomeTaxRate = 0.25;
    let serviceVATRate = 0.06;
    let goodsVATRate = 0.13;
    
    // 1. 设备与投资类计算
    // 服务器设备总额 = 服务器数量 * 服务器单价
    let serverEquipmentTotal = serverCount * serverUnitPrice;
    // 硬件设备总额 = 服务器设备总额 / 83.0075051444423%
    let hardwareTotal = serverEquipmentTotal / 0.830075051444423;
    // 其它设备总额
    let otherEquipmentTotal = hardwareTotal - serverEquipmentTotal;
    // 总投资 = 硬件设备总额 /93.876409228692%
    let totalInvestment = hardwareTotal / 0.93876409228692;
    // 软件与服务总额 = 总投资 - 硬件设备总额
    let softwareServiceTotal = totalInvestment - hardwareTotal;
    // 资本金 = 总投资 * (1-贷款比例)
    let equity = totalInvestment * (1 - loanRatio);
    // 贷款总额 = 总投资 * 贷款比例
    let loanTotal = totalInvestment * loanRatio;
    
    // 2. 运营成本与收入
    // 年电费 = 服务器机房及电费月单价 * 12 * 服务器数量
    let annualElectricity = serverRoomCost * 12 * serverCount;
    // 年运维费 = 年运维费服务器单价 * 服务器数量
    let annualMaintenance = maintenanceCostPerServer * serverCount;
    // 年现金流入 = 租金 * 服务器数量 * 12
    let annualCashInflow = rent * serverCount * 12;
    
    // 3. 融资成本（等额本金还款）
    let principalPerYear = loanTotal / operationYears;
    let annualPrincipalRepayments = [];
    let annualInterestCosts = [];
    for(let i = 0; i < operationYears; i++){
      let remainingPrincipal = loanTotal - principalPerYear * i;
      let interest = remainingPrincipal * loanRate;
      annualPrincipalRepayments.push(principalPerYear);
      annualInterestCosts.push(interest);
    }
    
    // 4. 年运营成本 = 年电费 + 年运维费
    let annualOperatingCost = annualElectricity + annualMaintenance;
    
    // 5. 税金及附加
    // 应纳服务增值税 = 年现金流入/(1+服务增值税率)*服务增值税率
    let serviceVAT = annualCashInflow / (1 + serviceVATRate) * serviceVATRate;
    // 摊销到每年的货物采购增值税 = (服务器设备总额/(1+货物增值税率)*货物增值税率) / 运营期
    let goodsVATAmortized = (serverEquipmentTotal / (1 + goodsVATRate) * goodsVATRate) / operationYears;
    // 印花税：总投资的3% + 年现金流入的3%
    let stampTax = totalInvestment * 0.03 + annualCashInflow * 0.03;
    let taxAndAdditional = 0;
    if(serviceVAT > goodsVATAmortized){
      taxAndAdditional = (serviceVAT - goodsVATAmortized) * 0.12 + stampTax;
    } else {
      taxAndAdditional = stampTax;
    }
    
    // 6. 计算各项利润数据
    let afterTaxRevenue = annualCashInflow / (1 + serviceVATRate);
    let annualDepreciation = (serverEquipmentTotal / (1 + goodsVATRate)) * (1 - equipmentResidualRate) / operationYears;
    
    let annualPreTaxProfits = [];
    let annualCorporateTaxes = [];
    let annualNetProfits = [];
    for(let i = 0; i < operationYears; i++){
      let interestCost = annualInterestCosts[i];
      let afterTaxCashOutflow = interestCost + annualOperatingCost + taxAndAdditional;
      let preTaxProfit = afterTaxRevenue - afterTaxCashOutflow - annualDepreciation;
      annualPreTaxProfits.push(preTaxProfit);
      let corporateTax = preTaxProfit * incomeTaxRate;
      annualCorporateTaxes.push(corporateTax);
      let netProfit = preTaxProfit - corporateTax;
      annualNetProfits.push(netProfit);
    }
    
    let cumulativeNetProfit = annualNetProfits.reduce((a, b) => a + b, 0);
    
    let GPs = annualPreTaxProfits.map(pt => afterTaxRevenue !== 0 ? (pt / afterTaxRevenue) * 100 : 0);
    let averageGP = GPs.reduce((a, b) => a + b, 0) / GPs.length;
    
    let ROI = (cumulativeNetProfit / totalInvestment) * 100;
    
    // 构造现金流序列（初始投资为负值）
    let cashFlows = [];
    cashFlows.push(-totalInvestment);
    for(let i = 0; i < operationYears; i++){
      let operatingCashFlow = (annualPreTaxProfits[i] - annualCorporateTaxes[i]) + annualDepreciation;
      cashFlows.push(operatingCashFlow);
    }
    let IRR = calculateIRR(cashFlows) * 100;
    
    // 简单项目结论（根据累计净利润与总投资比较判断）
    let summaryConclusion = "";
    if(cumulativeNetProfit > totalInvestment) {
      summaryConclusion = "项目总体盈利丰厚，投资回报率较高，建议投资。";
    } else if(cumulativeNetProfit < 0) {
      summaryConclusion = "项目累计亏损较大，存在较高风险，需谨慎决策。";
    } else {
      summaryConclusion = "项目盈利能力一般，风险与收益均衡，需进一步考察。";
    }
    
    // 传递结果，同时金额均按万元输出，并添加单位提示
    let result = {
      totalInvestment: totalInvestment.toFixed(2) + "（万元）",
      netProfit: annualNetProfits[0].toFixed(2) + "（万元）",
      cumulativeNetProfit: cumulativeNetProfit.toFixed(2) + "（万元）",
      ROI: ROI.toFixed(2) + "%",
      IRR: IRR.toFixed(2) + "%",
      averageGP: averageGP.toFixed(2) + "%",
      summaryConclusion: summaryConclusion
    };
    
    wx.navigateTo({
      url: '/pages/result/result?result=' + encodeURIComponent(JSON.stringify(result))
    });
  }
});

function calculateIRR(cashFlows, guess = 0.1) {
  const maxIteration = 1000;
  const precision = 1e-6;
  let irr = guess;
  
  for(let i = 0; i < maxIteration; i++){
    let npv = 0;
    let derivative = 0;
    for(let t = 0; t < cashFlows.length; t++){
      npv += cashFlows[t] / Math.pow(1 + irr, t);
      if(t !== 0) {
        derivative -= t * cashFlows[t] / Math.pow(1 + irr, t + 1);
      }
    }
    let newIrr = irr - npv / derivative;
    if(Math.abs(newIrr - irr) < precision){
      return newIrr;
    }
    irr = newIrr;
  }
  return irr;
}
