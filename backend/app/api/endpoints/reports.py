from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import DailyReport, ReportVerification, Project, User
from app.schemas.schemas import DailyReportSubmit, VerificationSubmit
from app.api.dependencies import require_contractor, require_supervisor, require_project_access
from app.services.audit import log_action

router = APIRouter()

@router.post("/", dependencies=[Depends(require_project_access)])
def submit_report(project_id: str, report_in: DailyReportSubmit, db: Session = Depends(get_db), current_user: User = Depends(require_contractor)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project.active_baseline_id:
        raise HTTPException(status_code=400, detail="Cannot submit report before baseline freeze")
    
    report = DailyReport(
        project_id=project_id,
        baseline_id=project.active_baseline_id,
        submitted_by=current_user.id,
        contractor_declared_work=report_in.contractor_declared_work,
        is_finalized=True
    )
    db.add(report)
    db.flush()
    log_action(db, current_user.id, "SUBMIT_REPORT", "DailyReport", report.id)
    db.commit()
    return {"id": report.id}

@router.put("/{report_id}", dependencies=[Depends(require_project_access)])
def update_report(project_id: str, report_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_contractor)):
    raise HTTPException(status_code=405, detail="Finalized reports cannot be modified. Submit a new report or add a correction.")

@router.delete("/{report_id}", dependencies=[Depends(require_project_access)])
def delete_report(project_id: str, report_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_contractor)):
    raise HTTPException(status_code=405, detail="Finalized reports cannot be deleted.")

@router.post("/{report_id}/verify", dependencies=[Depends(require_project_access)])
def verify_report(project_id: str, report_id: str, verify_in: VerificationSubmit, db: Session = Depends(get_db), current_user: User = Depends(require_supervisor)):
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if report.project_id != project_id:
        raise HTTPException(status_code=400, detail="Project/Report mismatch")
    
    if db.query(ReportVerification).filter(ReportVerification.daily_report_id == report_id).first():
        raise HTTPException(status_code=400, detail="Report already verified")
    
    verification = ReportVerification(
        daily_report_id=report_id,
        verified_by=current_user.id,
        supervisor_verified_work=verify_in.supervisor_verified_work,
        status=verify_in.status
    )
    db.add(verification)
    db.flush()
    log_action(db, current_user.id, "VERIFY_REPORT", "ReportVerification", verification.id)
    db.commit()
    return {"id": verification.id, "supervisor_verified_work": verification.supervisor_verified_work, "status": verification.status}
