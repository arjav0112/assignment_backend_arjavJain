from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.core.config import settings
from app.database import create_all
from app.routers import auth, dashboard, records, users

logger = logging.getLogger(__name__)

DOCS_DESCRIPTION = """
Role-based finance data management backend

**Test Admin Credentials**

- Email: `admin@finance.com`
- Password: `Admin1234`

Use `POST /auth/login`, copy the returned access token, then click `Authorize` in Swagger UI and paste `Bearer <access_token>`.
"""

SWAGGER_UI_OVERRIDES = """
<script>
(() => {
  const applyOverrides = () => {
    const infoSection = document.querySelector('.swagger-ui .information-container .info');
    if (infoSection && !document.getElementById('swagger-admin-creds')) {
      const banner = document.createElement('div');
      banner.id = 'swagger-admin-creds';
      banner.style.marginTop = '16px';
      banner.style.padding = '14px 16px';
      banner.style.border = '2px solid #4fd1a5';
      banner.style.borderRadius = '8px';
      banner.style.background = '#f3fbf8';
      banner.innerHTML = `
        <strong style="display:block; margin-bottom:8px;">Test Admin Credentials</strong>
        <div><strong>Email:</strong> admin@finance.com</div>
        <div><strong>Password:</strong> Admin1234</div>
      `;
      infoSection.appendChild(banner);
    }

    document.querySelectorAll('.swagger-ui .opblock label, .swagger-ui .modal-ux label, .swagger-ui .opblock .body-param__name').forEach((element) => {
      const text = (element.textContent || '').trim();
      if (/^username\\b/i.test(text)) {
        element.textContent = element.textContent.replace(/username/gi, 'email');
      }
    });

    document.querySelectorAll('.swagger-ui input').forEach((input) => {
      const wrapper = input.closest('.wrapper, .parameters-col_description, .auth-container, div');
      const nearbyLabel = wrapper?.querySelector('label, .body-param__name');
      const labelText = (nearbyLabel?.textContent || '').trim().toLowerCase();
      if (labelText.startsWith('email')) {
        input.setAttribute('placeholder', 'admin@finance.com');
        input.setAttribute('autocomplete', 'email');
      }
      if (labelText.startsWith('password')) {
        input.setAttribute('placeholder', 'Admin1234');
      }
    });
  };

  window.addEventListener('load', () => {
    applyOverrides();
    const observer = new MutationObserver(applyOverrides);
    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  });
})();
</script>
"""

app = FastAPI(
    title="Finance Dashboard API",
    description=DOCS_DESCRIPTION,
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(records.router)
app.include_router(dashboard.router)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html() -> HTMLResponse:
    swagger = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
    )
    html = swagger.body.decode("utf-8").replace("</body>", f"{SWAGGER_UI_OVERRIDES}</body>")
    return HTMLResponse(content=html)


@app.get("/redoc", include_in_schema=False)
async def redoc_html() -> HTMLResponse:
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
    )


@app.on_event("startup")
def startup_event() -> None:
    if settings.run_db_init_on_startup:
        create_all()


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": exc.__class__.__name__},
    )
