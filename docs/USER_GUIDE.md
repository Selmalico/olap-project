# OLAP Analytics Platform - User Guide

**Version:** 2.0  
**Last Updated:** February 27, 2026  
**Audience:** Business users, analysts, managers

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Asking Questions in Natural Language](#asking-questions-in-natural-language)
3. [Using OLAP Controls](#using-olap-controls)
4. [Understanding Your Results](#understanding-your-results)
5. [Business Scenarios & Examples](#business-scenarios--examples)
6. [OLAP Operations Glossary](#olap-operations-glossary)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Accessing the Application

1. **Open your web browser** (Chrome, Firefox, Edge, or Safari recommended)
2. **Navigate to the application URL**:
   - Production: `https://your-app-url.vercel.app` *(replace with actual URL)*
   - The app loads with a dark, professional interface
3. **No login required** - start asking questions immediately!

### First Look at the Interface

The application has three main sections:

```
┌─────────────────────────────────────────────────────────┐
│  CHAT TAB          │  OLAP CONTROLS TAB                │
├────────────────────────────────────────────────────────┤
│                                                         │
│  [Type your question here...]                          │
│                                                         │
├────────────────────────────────────────────────────────┤
│                   RESULTS AREA                          │
│  • Executive Summary (narrative)                       │
│  • Chart (automatic visualization)                     │
│  • Data Table (sortable, paginated)                   │
│  • Anomalies (if detected)                            │
└─────────────────────────────────────────────────────────┘
```

---

## Asking Questions in Natural Language

### The Chat Interface

The **Chat tab** lets you ask business questions in plain English, just like talking to a data analyst.

### Example Questions

**Revenue & Sales:**
- "What was our total revenue in 2024?"
- "Show me sales by region for the last quarter"
- "Which products made the most profit last year?"

**Comparisons:**
- "Compare Q3 vs Q4 2024 revenue"
- "How did 2024 perform vs 2023?"
- "Compare Electronics and Furniture sales this year"

**Trends & Growth:**
- "Show year-over-year growth by category"
- "What's the month-over-month change in 2024?"
- "Which regions are growing the fastest?"

**Rankings:**
- "Top 5 countries by revenue"
- "Bottom 3 product categories by profit margin"
- "Best performing regions in Q4"

**Drill-Downs:**
- "Break down 2024 revenue by quarter"
- "Show me Electronics sales by subcategory"
- "Drill into Europe sales by country"

**Detail Investigation:**
- "Show me the actual transactions for Electronics in Q4 2024"
- "What are the individual orders in North America last month?"
- "Give me the raw data for high-profit sales"

### How It Works

1. **Type your question** in the chat input box
2. **Press Enter** or click the send button
3. **Wait 2-5 seconds** while the AI analyzes your question
4. **Review the results**:
   - A brief executive summary appears first
   - Then a chart (automatically chosen for your data)
   - Then a detailed data table
   - Any unusual patterns are highlighted

### Tips for Better Questions

✅ **DO:**
- Use business terms like "revenue", "profit", "growth"
- Mention time periods: "2024", "Q3", "last month"
- Specify dimensions: "by region", "by category", "by country"
- Ask for rankings: "top 5", "best", "worst"

❌ **DON'T:**
- Use technical SQL terms (the AI handles that)
- Worry about exact phrasing - the AI is flexible
- Ask multiple unrelated questions at once

---

## Using OLAP Controls

The **OLAP Controls tab** provides structured forms for advanced analysis without typing questions.

### Drill-Down & Roll-Up

**What it does:** Navigate through data hierarchies

**Time Hierarchy:** Year → Quarter → Month  
**Geography Hierarchy:** Region → Country  
**Product Hierarchy:** Category → Subcategory

**Example:**
1. Select **Hierarchy**: "time"
2. Select **From Level**: "year"
3. Select **To Level**: "quarter"
4. Add filters (optional): `{"year": 2024}`
5. Click **Execute**

**Result:** Revenue broken down by quarters in 2024

**When to use:**
- "I want to see yearly data broken down by months"
- "Show me regional sales split by country"
- "Break product categories into subcategories"

### Roll-Up (Reverse of Drill-Down)

**Example:**
1. Hierarchy: "time"
2. From: "month"
3. To: "quarter"

**Result:** Monthly data summarized to quarterly totals

### Drill-Through

**What it does:** Shows individual transaction records instead of summaries

**Example:**
1. Add filters: `{"year": 2024, "category": "Electronics"}`
2. Set limit: 50 (max 1000)
3. Click **Execute**

**Result:** 50 actual sales transactions with order IDs, dates, amounts

**When to use:**
- "I want to see the actual orders behind this total"
- "Show me examples of high-value transactions"
- "I need to verify specific sales records"

### Slice

**What it does:** Filter data on ONE dimension

**Example:**
- Dimension: "year"
- Value: 2024
- Group by: ["region"]
- Measures: ["revenue", "profit"]

**Result:** 2024 data grouped by region

### Dice

**What it does:** Filter data on MULTIPLE dimensions

**Example:**
- Filters: `{"year": 2024, "region": "Europe", "category": "Electronics"}`
- Group by: ["country"]

**Result:** Electronics sales in Europe for 2024, by country

### Pivot

**What it does:** Creates a cross-tabulation (like Excel pivot tables)

**Example:**
- Rows: "region"
- Columns: "year"
- Values: "revenue"

**Result:** A table with regions as rows, years as columns, and revenue in cells

### KPI Calculations

#### Year-over-Year Growth
**Shows:** How metrics changed compared to the same period last year

**Example:**
- Measure: "revenue"
- Group by: "category"

**Result:** Each category's revenue with % change vs last year

#### Month-over-Month Change
**Shows:** Monthly trends and changes

**Example:**
- Measure: "profit"
- Year: 2024

**Result:** Monthly profit for 2024 with % change from previous month

#### Profit Margins
**Shows:** Profitability analysis

**Example:**
- Group by: "category"

**Result:** Each category's profit margin percentage

#### Top N Rankings
**Shows:** Best or worst performers

**Example:**
- Measure: "revenue"
- N: 5
- Group by: "country"

**Result:** Top 5 countries by revenue

#### Compare Periods
**Shows:** Side-by-side comparison of two time periods

**Example:**
- Period A: `{"year": 2023}`
- Period B: `{"year": 2024}`
- Measure: "revenue"

**Result:** 2023 vs 2024 revenue with change

---

## Understanding Your Results

### Executive Summary

A 3-sentence narrative that tells you:
1. **What happened** - Key metric and direction
2. **What drove it** - Top performers or causes
3. **What to watch** - Actionable recommendation

**Example:**
> "Revenue grew 15% year-over-year to $2.4M in 2024. North America led growth at 22%, driven by Electronics category expansion. Monitor APAC where Q4 demand exceeded supply by 18%."

### Charts

Charts are **automatically selected** based on your data:

- **Line Chart**: Time series, trends (YoY, MoM)
- **Bar Chart**: Category comparisons, rankings
- **Pie Chart**: Market share, percentage breakdowns
- **Composed Chart**: Multiple metrics on same chart

**Chart Controls:**
- Hover over data points for details
- Click legend items to show/hide series
- Charts are interactive and responsive

### Data Tables

**Features:**
- **Sortable**: Click column headers to sort
- **Paginated**: Use arrows to navigate pages
- **Formatted**: Currency ($), percentages (%), thousands (K/M)
- **Totals row**: Shows column sums where appropriate

**Tips:**
- Look for the **totals row** at the bottom (in bold)
- Sort by any column to find highest/lowest values
- Use pagination to explore large datasets

### Anomalies

When unusual patterns are detected, you'll see alerts like:

⚠️ **Anomaly Detected:**
> "revenue for LatAm: $50,000.00 is 340% above mean ($11,340.00)"

**What this means:**
- The system uses statistical analysis (Z-score)
- It flags values that are unusually high or low
- These may indicate opportunities or problems

**What to do:**
1. Investigate the flagged dimension
2. Use drill-through to see individual records
3. Consider whether it's a data quality issue or real insight

---

## Business Scenarios & Examples

### Scenario 1: Monthly Sales Review

**Goal:** Understand current month's performance

**Steps:**
1. Ask: *"Show month-over-month change for 2024"*
2. Review the line chart for trends
3. Check the executive summary for key insights
4. Look for anomalies (unusual spikes or dips)
5. If a month looks odd, ask: *"Show me the transactions for December 2024"*

**Expected Outcome:** Clear picture of monthly trends and any issues

---

### Scenario 2: Regional Performance Analysis

**Goal:** Compare regions and find best opportunities

**Steps:**
1. Ask: *"Compare revenue by region for 2024"*
2. Note which regions are growing vs declining
3. Ask: *"Top 5 countries in Europe by revenue"*
4. Drill down: *"Show Electronics sales in Germany by subcategory"*
5. Use drill-through to see actual orders

**Expected Outcome:** Identify regions for investment or improvement

---

### Scenario 3: Product Portfolio Review

**Goal:** Understand which products are profitable

**Steps:**
1. Ask: *"Profit margins by category"*
2. Identify low-margin categories
3. Ask: *"Show me the worst performing subcategories in Furniture"*
4. Drill through to see individual orders
5. Ask: *"Compare 2024 vs 2023 for Furniture category"*

**Expected Outcome:** Data-driven decisions on product mix

---

### Scenario 4: Quarterly Business Review

**Goal:** Prepare executive presentation for Q4 review

**Steps:**
1. Ask: *"Compare Q4 2024 vs Q3 2024 by region"*
2. Export the chart for your presentation
3. Ask: *"Year-over-year growth by category for 2024"*
4. Note the executive summary narratives
5. Ask: *"Top 10 customers by revenue in Q4"* (if customer dimension available)

**Expected Outcome:** Complete slide deck data in minutes

---

### Scenario 5: Investigating a Spike

**Goal:** Understand why revenue jumped in a specific month

**Steps:**
1. Ask: *"Month-over-month change in 2024"*
2. Notice anomaly: "November revenue +45%"
3. Ask: *"Show November 2024 revenue by category"*
4. Identify: "Electronics up 80%"
5. Ask: *"Show me the actual Electronics transactions in November 2024"*
6. Drill through with limit: 100

**Expected Outcome:** Root cause identified (e.g., holiday promotion, bulk order)

---

## OLAP Operations Glossary

### Slice
**Definition:** Filter data by fixing ONE dimension to a single value  
**Example:** "Show only 2024 data" (fixes year dimension to 2024)  
**When to use:** Focus on a specific time period, region, or category

### Dice
**Definition:** Filter data by fixing MULTIPLE dimensions to specific values  
**Example:** "Show Electronics in Europe for 2024" (three filters)  
**When to use:** Narrow down to a specific subset of data

### Drill-Down
**Definition:** Navigate from summary to detail within a hierarchy  
**Example:** Year (2024) → Quarters (Q1, Q2, Q3, Q4) → Months (Jan, Feb, ...)  
**When to use:** Break down aggregated data to see more detail

### Roll-Up
**Definition:** Navigate from detail to summary within a hierarchy  
**Example:** Months → Quarters → Year  
**When to use:** Summarize detailed data to see the big picture

### Drill-Through
**Definition:** Access the raw transaction records behind a summary  
**Example:** From "Q4 revenue: $500K" to 1,247 individual order records  
**When to use:** Verify numbers, investigate anomalies, audit data

### Pivot
**Definition:** Reorganize data as a cross-tabulation (rows × columns)  
**Example:** Regions as rows, Years as columns, Revenue in cells  
**When to use:** Compare two dimensions simultaneously (Excel-style)

### Time Intelligence
**Definition:** Period-over-period calculations (YoY, MoM, YTD, QTD)  
**Examples:**
- **YoY (Year-over-Year):** 2024 vs 2023
- **MoM (Month-over-Month):** October vs September
- **QoQ (Quarter-over-Quarter):** Q3 vs Q2

**When to use:** Measure growth, trends, and seasonality

---

## Troubleshooting

### "No data found" or empty results

**Possible causes:**
- Filters are too restrictive (e.g., no data exists for that combination)
- Date range is outside available data (2022-2024)
- Dimension value was misspelled

**Solutions:**
- Remove some filters and try again
- Check available data range (ask: "What years are in the database?")
- Use OLAP Controls to see valid dimension values

---

### "Error: Unknown dimension"

**Cause:** You asked for a dimension that doesn't exist

**Available dimensions:**
- Time: year, quarter, month, month_name
- Geography: region, country
- Product: category, subcategory
- Customer: customer_segment

**Solution:** Use one of the valid dimensions above

---

### Chart doesn't display

**Causes:**
- Too few data points (need at least 2)
- Data structure not suitable for charting

**Solutions:**
- Ensure your query returns multiple rows
- Try a different question that yields more results
- Use the data table view instead

---

### Results seem wrong or unexpected

**Steps to verify:**
1. Use **drill-through** to see actual records
2. Check the **SQL query** in developer mode (if available)
3. Verify your filters are correct
4. Try breaking down the question into smaller parts

**Example:**
- Instead of: "Compare all categories across all years by region"
- Try: "Show 2024 revenue by category"
- Then: "Show 2023 revenue by category"
- Then compare the two results manually

---

### Slow performance

**Normal response times:**
- Simple queries: 1-2 seconds
- Complex aggregations: 2-5 seconds
- Drill-through with 1000 records: 3-7 seconds

**If slower:**
- Reduce drill-through limit (e.g., 50 instead of 1000)
- Add more filters to reduce data volume
- Break complex questions into simpler parts

---

## Getting Help

### In-App Help
- Look for the **? icon** in the interface for quick tips
- The app provides **suggested follow-up questions** after each result

### Example Queries
Click the **Suggestions** button to see pre-written example queries you can use as templates

### Best Practices
1. **Start broad, then narrow**: "Revenue 2024" → "Revenue 2024 by region" → "Revenue 2024 in Europe by country"
2. **Use drill-through to verify**: When a number seems surprising, drill through to see the transactions
3. **Combine operations**: Slice + Drill-down + Compare gives you powerful insights
4. **Export your results**: Use the export button to save charts and tables for presentations

---

## Appendix: Sample Questions by Business Function

### Sales Leadership
- "Which regions exceeded quota in Q4 2024?"
- "Show me win rate by product category"
- "Top 10 deals by revenue this year"
- "Month-over-month sales velocity in 2024"

### Finance
- "Profit margins by business unit"
- "Year-over-year cost changes"
- "Revenue mix by product line for 2024"
- "Compare actual vs forecast for Q4" (if forecast data available)

### Marketing
- "Revenue by customer segment"
- "Which campaigns drove the most sales?" (if campaign data available)
- "New customer revenue vs existing customers"
- "Seasonal trends in purchases"

### Operations
- "Show inventory turnover by category" (if inventory data available)
- "Which products have the highest return rate?" (if returns data available)
- "Order fulfillment time by region"
- "Average order value by customer segment"

### Executive
- "Overall business health dashboard"
- "Key metrics year-over-year"
- "Top 5 opportunities and risks"
- "Strategic segment performance"

---

## Keyboard Shortcuts

- **Enter** - Submit question
- **Ctrl + /** - Focus chat input
- **Esc** - Clear current question
- **Tab** - Switch between Chat and OLAP Controls

---

**Need more help?** Contact your data analytics team or system administrator.

**Document Version:** 2.0 | **Last Updated:** February 27, 2026
