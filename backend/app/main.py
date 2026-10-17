from fastapi import FastAPI
from app.api.endpoints import auth, projects, baselines, reports, documents, engineering_elements, calculations, estimations, resources, resource_plans, schedules, monitoring, boq, cost, progress_valuation, contract_reconciliation, material_reconciliation, material_requirement_planning, material_inventory, material_consumption, material_performance, resource_performance, schedule_performance

app = FastAPI(title="Construction Intelligence MVP")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(baselines.router, prefix="/api/projects/{project_id}/baselines", tags=["baselines"])
app.include_router(reports.router, prefix="/api/projects/{project_id}/reports", tags=["reports"])
app.include_router(documents.router, prefix="/api/projects/{project_id}/documents", tags=["documents"])
app.include_router(engineering_elements.router, prefix="/api/projects/{project_id}/engineering-elements", tags=["engineering_elements"])
app.include_router(calculations.router, prefix="/api/projects/{project_id}/engineering-elements/{element_id}/calculations", tags=["calculations"])
app.include_router(estimations.router, prefix="/api/projects/{project_id}/rule-based-estimations", tags=["estimations"])
app.include_router(resources.router, prefix="/api/resources", tags=["resources"])
app.include_router(resource_plans.router, prefix="/api/projects/{project_id}/resource-plans", tags=["resource_plans"])
app.include_router(schedules.router, prefix="/api/projects/{project_id}", tags=["schedules"])
app.include_router(monitoring.router, prefix="/api/projects/{project_id}", tags=["monitoring"])
app.include_router(boq.router, prefix="/api", tags=["boq"])
app.include_router(cost.router, prefix="/api", tags=["cost"])
app.include_router(progress_valuation.router, prefix="/api", tags=["progress_valuation"])
app.include_router(contract_reconciliation.router, prefix="/api", tags=["contract_reconciliation"])
app.include_router(material_reconciliation.router, prefix="/api", tags=["material_reconciliation"])
app.include_router(material_requirement_planning.router, prefix="/api", tags=["material_requirement_planning"])
app.include_router(material_inventory.router, prefix="/api", tags=["material_inventory"])
app.include_router(material_consumption.router, prefix="/api", tags=["material_consumption"])
app.include_router(material_performance.router, prefix="/api", tags=["material_performance"])
app.include_router(resource_performance.router, tags=["resource_performance"])
app.include_router(schedule_performance.router, tags=["schedule_performance"])

@app.get("/")
def health_check():
    return {"status": "ok"}

