# BUFN741 Group Assignment 1

## Return Distributions, Tail Risk, and Equity Style Portfolios

## 1. Research Design

The analysis uses monthly returns for the S&P 500 and four Fama-French 2×3 Size/Book-to-Market portfolios: Small/Growth, Small/Value, Big/Growth, and Big/Value.

Monthly simple excess returns are constructed as asset return minus the one-month risk-free rate. The analysis covers the full common sample and three subperiods: 1990–2000, 2001–2010, and 2011–present.

## 2. Statistical Results

### Full_History

| Sample       | Asset        | Start_Month   | End_Month   |   Usable_Months | Mean_Excess_Annualized   | Std_Annualized   |   Sharpe_Ratio | Lower_Partial_Std_Annualized   |   Skewness |   Excess_Kurtosis | Empirical_VaR_1pct_Monthly   | Normal_VaR_1pct_Monthly   | Pct_Below_Mean_Minus_3SD   | Expected_Shortfall_1pct_Monthly   |
|:-------------|:-------------|:--------------|:------------|----------------:|:-------------------------|:-----------------|---------------:|:-------------------------------|-----------:|------------------:|:-----------------------------|:--------------------------|:---------------------------|:----------------------------------|
| Full_History | SP500        | 1988-01       | 2026-07     |             462 | 9.05%                    | 14.60%           |          0.619 | 16.45%                         |     -0.506 |             1.016 | -10.07%                      | -9.05%                    | 0.65%                      | -13.18%                           |
| Full_History | Small_Growth | 1988-01       | 2026-07     |             463 | 7.84%                    | 22.81%           |          0.344 | 24.36%                         |     -0.141 |             1.326 | -16.05%                      | -14.67%                   | 0.43%                      | -19.98%                           |
| Full_History | Small_Value  | 1988-01       | 2026-07     |             463 | 11.52%                   | 19.60%           |          0.588 | 21.41%                         |     -0.569 |             2.227 | -14.95%                      | -12.20%                   | 0.65%                      | -19.63%                           |
| Full_History | Big_Growth   | 1988-01       | 2026-07     |             463 | 10.08%                   | 15.25%           |          0.661 | 16.41%                         |     -0.343 |             0.651 | -10.69%                      | -9.40%                    | 0.43%                      | -12.62%                           |
| Full_History | Big_Value    | 1988-01       | 2026-07     |             463 | 10.67%                   | 18.22%           |          0.586 | 20.34%                         |     -0.705 |             3.023 | -14.53%                      | -11.35%                   | 1.08%                      | -20.04%                           |


### 1990_2000

|    Sample | Asset        | Start_Month   | End_Month   |   Usable_Months | Mean_Excess_Annualized   | Std_Annualized   |   Sharpe_Ratio | Lower_Partial_Std_Annualized   |   Skewness |   Excess_Kurtosis | Empirical_VaR_1pct_Monthly   | Normal_VaR_1pct_Monthly   | Pct_Below_Mean_Minus_3SD   | Expected_Shortfall_1pct_Monthly   |
|----------:|:-------------|:--------------|:------------|----------------:|:-------------------------|:-----------------|---------------:|:-------------------------------|-----------:|------------------:|:-----------------------------|:--------------------------|:---------------------------|:----------------------------------|
| 1990_2000 | SP500        | 1990-01       | 2000-12     |             132 | 10.49%                   | 13.92%           |          0.753 | 15.50%                         |     -0.508 |             1.207 | -9.29%                       | -8.47%                    | 0.76%                      | -12.29%                           |
| 1990_2000 | Small_Growth | 1990-01       | 2000-12     |             132 | 5.80%                    | 25.07%           |          0.231 | 26.06%                         |     -0.011 |             2.026 | -16.54%                      | -16.35%                   | 0.76%                      | -20.79%                           |
| 1990_2000 | Small_Value  | 1990-01       | 2000-12     |             132 | 12.16%                   | 16.03%           |          0.759 | 18.93%                         |     -0.749 |             2.203 | -11.01%                      | -9.75%                    | 0.76%                      | -15.44%                           |
| 1990_2000 | Big_Growth   | 1990-01       | 2000-12     |             132 | 11.49%                   | 15.44%           |          0.744 | 16.25%                         |     -0.334 |             0.696 | -10.86%                      | -9.41%                    | 0.76%                      | -12.59%                           |
| 1990_2000 | Big_Value    | 1990-01       | 2000-12     |             132 | 12.51%                   | 14.01%           |          0.893 | 15.56%                         |     -0.443 |             0.634 | -9.77%                       | -8.36%                    | 0.76%                      | -11.56%                           |


### 2001_2010

|    Sample | Asset        | Start_Month   | End_Month   |   Usable_Months | Mean_Excess_Annualized   | Std_Annualized   |   Sharpe_Ratio | Lower_Partial_Std_Annualized   |   Skewness |   Excess_Kurtosis | Empirical_VaR_1pct_Monthly   | Normal_VaR_1pct_Monthly   | Pct_Below_Mean_Minus_3SD   | Expected_Shortfall_1pct_Monthly   |
|----------:|:-------------|:--------------|:------------|----------------:|:-------------------------|:-----------------|---------------:|:-------------------------------|-----------:|------------------:|:-----------------------------|:--------------------------|:---------------------------|:----------------------------------|
| 2001_2010 | SP500        | 2001-01       | 2010-12     |             120 | 0.61%                    | 16.41%           |          0.037 | 19.15%                         |     -0.603 |             0.768 | -10.94%                      | -10.97%                   | 0.83%                      | -13.94%                           |
| 2001_2010 | Small_Growth | 2001-01       | 2010-12     |             120 | 4.39%                    | 24.03%           |          0.183 | 27.00%                         |     -0.415 |             0.181 | -17.03%                      | -15.77%                   | 0.83%                      | -19.86%                           |
| 2001_2010 | Small_Value  | 2001-01       | 2010-12     |             120 | 10.58%                   | 22.71%           |          0.466 | 24.60%                         |     -0.615 |             0.867 | -15.73%                      | -14.37%                   | 0.83%                      | -18.01%                           |
| 2001_2010 | Big_Growth   | 2001-01       | 2010-12     |             120 | 0.76%                    | 16.03%           |          0.047 | 17.76%                         |     -0.559 |             0.677 | -11.36%                      | -10.70%                   | 0.83%                      | -13.55%                           |
| 2001_2010 | Big_Value    | 2001-01       | 2010-12     |             120 | 1.76%                    | 21.54%           |          0.082 | 24.77%                         |     -0.7   |             1.707 | -18.57%                      | -14.32%                   | 1.67%                      | -20.29%                           |


### 2011_Present

| Sample       | Asset        | Start_Month   | End_Month   |   Usable_Months | Mean_Excess_Annualized   | Std_Annualized   |   Sharpe_Ratio | Lower_Partial_Std_Annualized   |   Skewness |   Excess_Kurtosis | Empirical_VaR_1pct_Monthly   | Normal_VaR_1pct_Monthly   | Pct_Below_Mean_Minus_3SD   | Expected_Shortfall_1pct_Monthly   |
|:-------------|:-------------|:--------------|:------------|----------------:|:-------------------------|:-----------------|---------------:|:-------------------------------|-----------:|------------------:|:-----------------------------|:--------------------------|:---------------------------|:----------------------------------|
| 2011_Present | SP500        | 2011-01       | 2026-07     |             187 | 12.87%                   | 14.12%           |          0.912 | 15.55%                         |     -0.337 |             0.798 | -9.24%                       | -8.41%                    | 0.53%                      | -10.94%                           |
| 2011_Present | Small_Growth | 2011-01       | 2026-07     |             187 | 11.29%                   | 21.42%           |          0.527 | 21.97%                         |      0.011 |             1.09  | -13.61%                      | -13.44%                   | 0.53%                      | -16.35%                           |
| 2011_Present | Small_Value  | 2011-01       | 2026-07     |             187 | 11.28%                   | 20.70%           |          0.545 | 21.67%                         |     -0.414 |             2.663 | -11.48%                      | -12.96%                   | 0.53%                      | -20.41%                           |
| 2011_Present | Big_Growth   | 2011-01       | 2026-07     |             187 | 14.46%                   | 14.84%           |          0.974 | 15.87%                         |     -0.194 |             0.428 | -9.12%                       | -8.76%                    | 0.00%                      | -9.97%                            |
| 2011_Present | Big_Value    | 2011-01       | 2026-07     |             187 | 14.15%                   | 19.32%           |          0.733 | 21.61%                         |     -0.627 |             3.4   | -11.87%                      | -11.79%                   | 0.53%                      | -19.94%                           |


## 3. Figures

The complete figure set is stored in `output/figures/`. It includes monthly excess-return time series, empirical return histograms with fitted normal distributions, and a common left-tail ECDF comparison.

## 4. Economic Interpretation


## Q1 — Average Excess Returns and Sharpe Ratios

Evidence:

In the full-history sample (January 1988–July 2026), Small Value has the highest annualized mean excess return at 11.52%, followed by Big Value at 10.67%, Big Growth at 10.08%, the S&P 500 at 9.05%, and Small Growth at 7.84%. The Sharpe ordering differs: Big Growth ranks first at 0.661, followed by the S&P 500 at 0.619, Small Value at 0.588, Big Value at 0.586, and Small Growth at 0.344. Rankings change across subperiods. Big Value has the highest Sharpe ratio in 1990–2000 (0.893), Small Value in 2001–2010 (0.466), and Big Growth in 2011–July 2026 (0.974). Mean-return leaders likewise change from Big Value (12.51%) to Small Value (10.58%) to Big Growth (14.46%) across those samples.

Interpretation:

The full-history return leader is not the risk-adjusted-return leader: Small Value's higher mean came with enough volatility to leave its Sharpe ratio below those of Big Growth and the S&P 500. Small Growth was weakest on both full-history mean excess return and Sharpe ratio. Because both mean and Sharpe leaders vary by subperiod, the evidence does not support a stable performance ranking through time.

## Q2 — Total and Downside Volatility

Evidence:

For the full-history sample, Small Growth has the highest annualized standard deviation (22.81%) and lower-partial standard deviation (24.36%). The S&P 500 has the lowest total volatility (14.60%), while Big Growth has the lowest downside volatility (16.41%), narrowly below the S&P 500 (16.45%). Small Value records 19.60% total and 21.41% downside volatility; Big Value records 18.22% and 20.34%. In every full-history asset series, lower-partial volatility exceeds total volatility. This pattern also holds for every asset in each reported subperiod—for example, in 2001–2010 Big Value's total volatility is 21.54% and its downside volatility is 24.77%.

Interpretation:

Small Growth carried the greatest overall and adverse-return variability over the full history. The consistently higher lower-partial measures indicate that downside outcomes were more dispersed than the corresponding all-return standard deviations suggest. Thus, total volatility alone understates the concentration of risk in unfavorable months, particularly for the small portfolios and Big Value.

## Q3 — Normality and Tail Risk

Evidence:

The full-history evidence rejects a simple normal characterization most strongly for the value portfolios. Big Value has skewness of -0.705, excess kurtosis of 3.023, an empirical monthly 1% VaR of -14.53% versus normal VaR of -11.35%, and 1.080% of observations below mean minus three standard deviations. Small Value has skewness of -0.569, excess kurtosis of 2.227, empirical VaR of -14.95% versus normal VaR of -12.20%, and a 0.648% beyond-three-SD loss frequency. The S&P 500 is also left-skewed (-0.506) and leptokurtic (excess kurtosis 1.016), with empirical VaR of -10.07% versus normal VaR of -9.05% and a 0.649% beyond-three-SD frequency. Small Growth and Big Growth have less negative skewness (-0.141 and -0.343), but positive excess kurtosis (1.326 and 0.651) and empirical VaRs more negative than their normal VaRs. The five full-history histogram/normal-overlay figures show visible departures from the fitted normal curves, while `tail_comparison_ecdf.png` displays distinct and extended empirical left tails across the assets.

Interpretation:

Taken together—not inferred from any single measure—the negative skewness, positive excess kurtosis, frequent extreme losses, VaR gaps, histogram deviations, and tail-comparison figure indicate asymmetric and fat-tailed downside risk. A normal model would understate the full-history 1% loss threshold for all five assets, with especially large understatement for Big Value and Small Value. The evidence supports non-normal tail risk, not a claim that every asset departs from normality to the same degree.

## Q4 — Expected Shortfall versus VaR

Evidence:

In the full-history sample, every 1% expected shortfall is more negative than its empirical 1% VaR: S&P 500, -13.18% versus -10.07%; Small Growth, -19.98% versus -16.05%; Small Value, -19.63% versus -14.95%; Big Growth, -12.62% versus -10.69%; and Big Value, -20.04% versus -14.53%. Big Value has the most negative full-history expected shortfall, although Small Growth has the most negative full-history empirical VaR. The distinction also matters within subperiods: in 2011–July 2026, Small Value's empirical VaR is -11.48%, but its expected shortfall is -20.41%.

Interpretation:

VaR identifies the loss threshold at the 1% tail, whereas expected shortfall measures the average severity of outcomes beyond that threshold. The more negative expected-shortfall values show that losses can deepen materially after the VaR boundary is crossed. The differing full-history leaders demonstrate why threshold risk and loss severity are separate dimensions: Small Growth has the worse VaR cutoff, but Big Value has the worse average loss beyond the cutoff.

## Q5 — Distribution Differences Across Periods

Evidence:

Distributional characteristics vary substantially across the three subperiods. The S&P 500's annualized mean excess return and Sharpe ratio fall from 10.49% and 0.753 in 1990–2000 to 0.61% and 0.037 in 2001–2010, then rise to 12.87% and 0.912 in 2011–July 2026. Big Growth follows a similar shift: 11.49% and 0.744, then 0.76% and 0.047, then 14.46% and 0.974. Big Value's volatility rises from 14.01% in 1990–2000 to 21.54% in 2001–2010 and is 19.32% in 2011–July 2026. Its excess kurtosis rises across the reported periods from 0.634 to 1.707 to 3.400. Tail measures also change: Big Value's empirical monthly 1% VaR is -9.77%, -18.57%, and -11.87%, respectively. Small Value's 2011–July 2026 empirical VaR (-11.48%) is less negative than its normal VaR (-12.96%), yet its expected shortfall is -20.41% and excess kurtosis is 2.663.

Interpretation:

The middle subperiod is markedly weaker for the S&P 500 and both Big portfolios on mean and Sharpe measures, while Big Value also shows its worst subperiod VaR there. The later sample improves average and risk-adjusted performance for the S&P 500 and Big Growth, but improvement in central performance does not eliminate tail risk: Big Value and Small Value retain high kurtosis and severe expected shortfall. These shifts are consistent with broad changes in market regimes, including expansion and contraction episodes, but the supplied outputs do not identify causal historical events. Nor do they support stable rankings or a time-invariant distribution.

## Q6 — S&P 500 versus Fama-French Big Portfolios

Evidence:

Over the full history, Big Growth exceeds the S&P 500 in annualized mean excess return (10.08% versus 9.05%) and Sharpe ratio (0.661 versus 0.619), with slightly higher total volatility (15.25% versus 14.60%) but slightly lower downside volatility (16.41% versus 16.45%). Its empirical 1% VaR (-10.69%) and expected shortfall (-12.62%) are modestly less favorable than the S&P 500's (-10.07% and -13.18%, respectively), with the ordering differing between the threshold and average tail loss. Big Value also has a higher mean excess return than the S&P 500 (10.67% versus 9.05%), but a lower Sharpe ratio (0.586 versus 0.619), higher total volatility (18.22% versus 14.60%), higher downside volatility (20.34% versus 16.45%), more negative empirical VaR (-14.53% versus -10.07%), and more negative expected shortfall (-20.04% versus -13.18%). Subperiod comparisons are not stable: Big Value's Sharpe exceeds the S&P 500's in 1990–2000 (0.893 versus 0.753) and 2001–2010 (0.082 versus 0.037), but trails it in 2011–July 2026 (0.733 versus 0.912); Big Growth trails the S&P 500 in 1990–2000 (0.744 versus 0.753) but exceeds it in the next two periods.

Interpretation:

The S&P 500 resembles Big Growth more closely than Big Value in full-history volatility and tail risk. Big Growth provides the strongest full-history risk-adjusted result of the three, while Big Value's higher mean is paired with substantially greater total, downside, and tail risk. Because the relative Sharpe rankings change across subperiods, the evidence is insufficient to claim that either Big portfolio consistently dominates the S&P 500.

## Overall Empirical Takeaways

- Full-history return and Sharpe rankings differ: Small Value has the highest mean excess return, whereas Big Growth has the highest Sharpe ratio.
- Risk is asymmetric: downside volatility exceeds total volatility for every asset in every reported sample.
- Multiple measures and the supplied figures jointly indicate non-normal, fat-tailed downside risk, especially for the value portfolios.
- Expected shortfall is materially more negative than empirical 1% VaR and reveals loss severity after the VaR threshold is crossed.
- Performance, volatility, and tail behavior change across subperiods, so neither rankings nor return distributions should be treated as stable.
- Relative to the S&P 500, Big Growth is close in risk and stronger on full-history Sharpe, while Big Value's higher mean comes with distinctly greater downside and tail risk.



## 5. Reproducibility and Quality Assurance

The final report was assembled only after the data-acquisition, validation, processing, statistical-analysis, figure-generation, quality-assurance, and economic-interpretation stages completed successfully.

Numerical statistics were generated by deterministic Python code. Economic interpretation was produced by Codex after the upstream quality assurance gate passed.

