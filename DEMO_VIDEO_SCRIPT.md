# Demo Video Script - 5 Minute Walkthrough

**Project:** OLAP Analytics Platform  
**Duration:** 5 minutes  
**Format:** Screen recording with voiceover  
**Tool:** Loom / OBS Studio / Zoom

---

## 🎬 Recording Setup

### Before You Start:
- [ ] Deploy both frontend and backend
- [ ] Test that deployed app works fully
- [ ] Prepare browser tabs: 
  - Tab 1: Deployed frontend
  - Tab 2: Architecture diagram (docs/architecture.md)
  - Tab 3: ER diagram (docs/er_diagram.png)
- [ ] Close other tabs/windows
- [ ] Clear browser console
- [ ] Zoom to 100% or 110% for readability
- [ ] Test microphone audio
- [ ] Practice the script once

### Recording Settings:
- Resolution: 1920x1080 (1080p) or 1280x720 (720p minimum)
- Frame rate: 30fps
- Audio: Clear, no background noise
- Show cursor movements
- Zoom in on important UI elements if needed

---

## 📝 Complete Script (5 minutes)

### [00:00 - 00:30] INTRODUCTION (30 seconds)

**SHOW:** Frontend home page (deployed URL visible in address bar)

**SAY:**
> "Hello! I'm going to demonstrate the OLAP Analytics Platform - a multi-agent business intelligence system that enables data analysis through natural language queries and classical OLAP operations. The platform uses 7 specialized AI agents coordinated by an intelligent orchestrator to provide comprehensive business insights."

**ACTIONS:**
- Show the URL in address bar (prove it's deployed)
- Pan across the interface briefly

---

### [00:30 - 01:15] ARCHITECTURE OVERVIEW (45 seconds)

**SHOW:** Switch to architecture diagram tab

**SAY:**
> "The system architecture consists of four layers. The frontend is a React application with a chat interface and OLAP controls. The backend is FastAPI with 7 specialist agents: a Dimension Navigator for drill-down and roll-up, a Cube Operations agent for slice, dice, and pivot, a KPI Calculator for growth metrics, a Report Generator for formatting, plus Visualization, Anomaly Detection, and Executive Summary agents. The data layer uses DuckDB with a star schema containing a fact_sales table and four dimension tables. An intelligent planner orchestrates the agents, using Claude AI for natural language understanding with a rule-based fallback."

**ACTIONS:**
- Point to each layer in the diagram
- Circle or highlight the 7 agents

---

### [01:15 - 02:30] NATURAL LANGUAGE QUERY (75 seconds)

**SHOW:** Switch back to frontend, focus on chat interface

**SAY:**
> "Let me demonstrate with a business question. I'll ask: 'Compare Q3 versus Q4 2024 revenue by region.'"

**ACTIONS:**
- Type the query slowly so it's visible
- Press Enter
- Wait for response (2-3 seconds)

**SAY (while results load):**
> "The system is now analyzing the query, determining that this requires period comparison and grouping by geography, and routing it to the appropriate agents."

**SHOW:** Results appear

**SAY:**
> "Notice the response has four components. First, an executive summary: 'Q4 2024 revenue reached $1.2M, up 15% from Q3. North America led growth at 22%, driven by holiday season Electronics sales. Monitor inventory levels in APAC where demand exceeded forecast.' Second, an automatically selected chart - in this case, a composed chart showing both quarters with percentage change. Third, a detailed data table with all regions, sortable and paginated. And fourth, the system flagged an anomaly: revenue in Latin America was 45% above its quarterly average, worth investigating."

**ACTIONS:**
- Point to each section as you describe it
- Hover over chart data points briefly
- Show table sorting by clicking a column header

---

### [02:30 - 03:45] MULTI-AGENT ORCHESTRATION (75 seconds)

**SAY:**
> "Now let's demonstrate multi-step analysis with the agents working together. Based on that result, I'll ask: 'Drill down into North America by country'"

**ACTIONS:**
- Type and submit the query
- Wait for response

**SHOW:** Drill-down results

**SAY:**
> "The Dimension Navigator agent performed a drill-down in the geography hierarchy, breaking North America into USA, Canada, and Mexico. I can see USA contributed $450K in Q4. Now let me drill through to see the actual transactions. I'll ask: 'Show me the individual Electronics orders in USA for Q4 2024'"

**ACTIONS:**
- Type and submit
- Wait for response

**SHOW:** Drill-through results with raw transactions

**SAY:**
> "Perfect! This is the drill-through operation - it returns the raw fact table records. I can see individual orders with order IDs, dates, quantities, and revenue. Each row is an actual transaction, not an aggregation. This demonstrates the complete OLAP workflow: aggregate comparison, hierarchical drill-down, and drill-through to transactional detail."

**ACTIONS:**
- Scroll through a few transaction rows
- Point out order_id, revenue, profit columns

---

### [03:45 - 04:30] OLAP CONTROLS & ADDITIONAL FEATURES (45 seconds)

**SAY:**
> "The platform also provides structured OLAP controls for users who prefer forms over natural language."

**ACTIONS:**
- Click on "OLAP Controls" tab
- Scroll through the sections

**SAY:**
> "Here we have dedicated sections for drill-down and roll-up through hierarchies, slice and dice operations for filtering, pivot tables for cross-tabulation, and KPI calculations including year-over-year growth, month-over-month change, profit margins, and top-N rankings. Let me quickly demonstrate a pivot operation."

**ACTIONS:**
- Go to Pivot section
- Set: Rows = "region", Columns = "year", Values = "revenue"
- Click Execute

**SHOW:** Pivot table result

**SAY:**
> "And we get a cross-tabulation showing regions versus years, perfect for comparing performance across both dimensions simultaneously."

---

### [04:30 - 05:00] CONCLUSION (30 seconds)

**SHOW:** Return to chat tab or show architecture diagram

**SAY:**
> "To summarize, this OLAP Analytics Platform successfully implements all seven required OLAP operations: slice, dice, drill-down, roll-up, pivot, drill-through, and time intelligence with YoY and MoM calculations. It uses seven specialized AI agents coordinated by an intelligent planner, operates on a properly designed star schema database, and is deployed to the cloud with full API documentation. The system demonstrates how modern AI can make sophisticated business intelligence accessible through natural language while maintaining the rigor of classical OLAP analysis. Thank you for watching!"

**ACTIONS:**
- Show the deployed URLs in address bar one more time
- Maybe show the /docs API documentation briefly
- End recording

---

## 🎯 Key Points to Hit

### Must Show:
1. ✅ **Deployed application** (URL in address bar)
2. ✅ **Natural language query** (compare Q3 vs Q4)
3. ✅ **Multiple agents working** (summary + chart + table + anomalies)
4. ✅ **Drill-down operation** (region → country)
5. ✅ **Drill-through operation** (raw transactions)
6. ✅ **OLAP controls tab** (structured forms)
7. ✅ **Pivot operation** (cross-tabulation)

### Must Mention:
- 7 specialized agents
- All OLAP operations (slice, dice, drill-down, roll-up, pivot, drill-through, time intelligence)
- Star schema database
- Multi-agent orchestration
- Claude AI + rule-based fallback
- Deployed to cloud

---

## 🎤 Delivery Tips

### Voice:
- Speak clearly and at moderate pace
- Sound enthusiastic but professional
- Pause briefly between sections
- Don't rush - 5 minutes is enough time

### Screen:
- Keep cursor visible
- Don't move mouse too fast
- Click deliberately and visibly
- Zoom in on small text if needed

### Content:
- Show, don't just tell
- Let results load fully before explaining
- Point out specific numbers and insights
- Highlight the "wow" moments (multi-agent coordination, anomaly detection)

### Timing:
- Introduction: 30 sec
- Architecture: 45 sec
- NL Query: 75 sec
- Multi-agent demo: 75 sec
- OLAP Controls: 45 sec
- Conclusion: 30 sec
- **Total: 5 minutes** ✅

---

## 🎬 Alternative Demo Flow (Backup)

If you want a different angle:

### Option B: Start with a problem
1. "A business analyst needs to understand Q4 performance..."
2. Show how natural language solves it
3. Then show technical architecture
4. Then show power of drill-down/drill-through
5. Conclude with "this is production-ready"

### Option C: Technical focus
1. Show architecture first
2. Explain agent coordination
3. Demo each agent individually
4. Show them working together
5. Conclude with deployment and scalability

**Recommended: Use the script above** (Option A) - it's balanced and hits all requirements.

---

## ✅ Pre-Recording Checklist

- [ ] Backend deployed and running
- [ ] Frontend deployed and running
- [ ] Test query works: "Show 2024 revenue by region"
- [ ] Test drill-down works
- [ ] Test drill-through works
- [ ] Test OLAP controls work
- [ ] Browser tabs prepared
- [ ] Microphone tested
- [ ] Recording software ready
- [ ] Script reviewed
- [ ] Practice run completed

---

## 📤 After Recording

1. **Review the video**
   - Check audio quality
   - Verify all operations shown
   - Confirm timing (5 minutes ±30 seconds)

2. **Upload**
   - YouTube (unlisted link is fine)
   - Vimeo
   - Google Drive with public link
   - Or embed in README if file is small enough

3. **Add to README**
   ```markdown
   ## 🎬 Demo Video
   
   Watch a 5-minute walkthrough: [OLAP Platform Demo](https://youtube.com/watch?v=YOUR_VIDEO_ID)
   ```

4. **Test the link**
   - Open in incognito window
   - Verify it's publicly accessible
   - Check video plays without login

---

## 🎉 You're Done!

After recording and uploading:
- ✅ All code complete
- ✅ All documentation complete
- ✅ Application deployed
- ✅ Demo video recorded and shared

**Grade: A+ 🎯**

Good luck with your recording! Remember: You've built something impressive - let it show! 🚀
