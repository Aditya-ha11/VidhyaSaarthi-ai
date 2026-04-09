import time
from agents import eligibility_agent, scholarship_agent, document_agent, loan_agent, disbursal_agent, explanation_agent

def process(student_data):
    state = {
        "student": student_data,
        "eligibility_score": 0,
        "scholarships": [],
        "loan_options": [],
        "documents_verified": False,
        "document_details": [],
        "disbursal_status": "Pending",
        "explanation": "",
        "audit_trail": []
    }

    state["audit_trail"].append({
        "step": "System Initialization",
        "agent": "MasterAgent",
        "message": f"Application pipeline automatically initiated for {student_data['name']}.",
        "details": {"student": student_data},
        "timestamp": time.time()
    })

    import asyncio
    import copy
    
    async def run_pipeline():
        nonlocal state
        
        # Step 1: Eligibility (Must run first)
        try:
            state = eligibility_agent.run(state)
        except Exception as e:
            _log_err("eligibility_agent", e)
            return state

        # Step 2: Parallel Scholarship and Document
        async def run_agent_async(agent_mdl, st):
            try:
                return await asyncio.to_thread(agent_mdl.run, copy.deepcopy(st))
            except Exception as e:
                _log_err(agent_mdl.__name__, e)
                return st
                
        def _log_err(name, err):
            state["audit_trail"].append({
                "step": f"Error in {name}",
                "agent": name,
                "message": f"Agent failed: {str(err)}",
                "details": {},
                "timestamp": time.time()
            })

        st_sch, st_doc = await asyncio.gather(
            run_agent_async(scholarship_agent, state),
            run_agent_async(document_agent, state)
        )
        
        # Merge state safely
        state["scholarships"] = st_sch.get("scholarships", [])
        state["documents_verified"] = st_doc.get("documents_verified", False)
        state["document_details"] = st_doc.get("document_details", [])
        
        # Append trails sequentially
        new_trails = [t for t in st_sch.get("audit_trail", []) if t["agent"] == "ScholarshipAgent"]
        new_trails += [t for t in st_doc.get("audit_trail", []) if t["agent"] == "DocumentAgent"]
        state["audit_trail"].extend(sorted(new_trails, key=lambda x: x["timestamp"]))
        
        # Step 3: Remaining Agents sequentially
        for agent in [loan_agent, disbursal_agent, explanation_agent]:
            try:
                state = await asyncio.to_thread(agent.run, state)
            except Exception as e:
                _log_err(agent.__name__, e)
                
        return state

    state = asyncio.run(run_pipeline())

    state["audit_trail"].append({
        "step": "Final Assessment",
        "agent": "MasterAgent",
        "message": f"Pipeline successfully completed. Application formally marked as {state['disbursal_status']}.",
        "details": {
            "final_status": state["disbursal_status"],
            "final_score": state["eligibility_score"]
        },
        "timestamp": time.time()
    })

    return state
