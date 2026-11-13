import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.api.deps import get_db
from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.battery import BatteryConfiguration
from app.models.grid import GridConfiguration
from app.models.alert import SystemAlert

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    admin = User(
        email="admin@test.com",
        hashed_password=get_password_hash("Admin@123"),
        full_name="Test Admin",
        role="admin",
        is_active=True
    )
    operator = User(
        email="operator@test.com",
        hashed_password=get_password_hash("Operator@123"),
        full_name="Test Operator",
        role="operator",
        is_active=True
    )
    analyst = User(
        email="analyst@test.com",
        hashed_password=get_password_hash("Analyst@123"),
        full_name="Test Analyst",
        role="analyst",
        is_active=True
    )
    db.add_all([admin, operator, analyst])

    db.add(BatteryConfiguration(
        capacity_kwh=100.0,
        initial_soc=50.0,
        min_soc=20.0,
        max_soc=95.0,
        max_charge_kw=30.0,
        max_discharge_kw=30.0,
        charge_efficiency=0.92,
        discharge_efficiency=0.92,
        is_active=True
    ))
    db.add(GridConfiguration(
        import_limit_kw=150.0,
        export_limit_kw=100.0,
        import_tariff=0.15,
        export_tariff=0.08,
        is_active=True
    ))
    db.add(SystemAlert(
        title="Test Alert",
        message="Initial testing alert",
        category="System",
        severity="INFO",
        is_acknowledged=False
    ))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_headers():
    token = create_access_token(subject=1, role="admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def operator_headers():
    token = create_access_token(subject=2, role="operator")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def analyst_headers():
    token = create_access_token(subject=3, role="analyst")
    return {"Authorization": f"Bearer {token}"}
