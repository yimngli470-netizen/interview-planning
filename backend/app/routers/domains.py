from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Domain
from ..schemas import DomainCreate, DomainOut, DomainUpdate

router = APIRouter(prefix="/api/domains", tags=["domains"])


@router.get("", response_model=list[DomainOut])
def list_domains(db: Session = Depends(get_db)):
    return db.scalars(select(Domain).order_by(Domain.order, Domain.id)).all()


@router.post("", response_model=DomainOut, status_code=201)
def create_domain(payload: DomainCreate, db: Session = Depends(get_db)):
    domain = Domain(**payload.model_dump())
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return domain


@router.patch("/{domain_id}", response_model=DomainOut)
def update_domain(domain_id: int, payload: DomainUpdate, db: Session = Depends(get_db)):
    domain = db.get(Domain, domain_id)
    if not domain:
        raise HTTPException(404, "Domain not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(domain, k, v)
    db.commit()
    db.refresh(domain)
    return domain


@router.delete("/{domain_id}", status_code=204)
def delete_domain(domain_id: int, db: Session = Depends(get_db)):
    domain = db.get(Domain, domain_id)
    if not domain:
        raise HTTPException(404, "Domain not found")
    db.delete(domain)
    db.commit()
