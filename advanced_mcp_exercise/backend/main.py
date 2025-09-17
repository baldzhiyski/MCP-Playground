from fastmcp import FastMCP
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware import   Middleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import JSONResponse
from fastmcp.server.auth import BearerAuthProvider
from fastmcp.server.dependencies import get_access_token,AccessToken
import os
from jose import jwt
from database import NoteRepository

load_dotenv()

auth = BearerAuthProvider(
    jwks_uri=f"{os.getenv('STYTCH_DOMAIN')}/.well-known/jwks.json",
    issuer=os.getenv("STYTCH_DOMAIN"),
    algorithm="RS256",
    audience=os.getenv("STYTCH_PROJECT_ID")
)

mcp = FastMCP(name="Notes App",auth=auth)

@mcp.tool()
def get_my_notes() -> str:
    """Get all notes for a user"""

    access_token: AccessToken = get_access_token()
    user_id = jwt.get_unverified_claims(access_token.token)["sub"]

    notes = NoteRepository.get_notes_by_user(user_id);

    if not notes :
        return "No notes found"

    results = "Your notes: \n"
    for note in notes:
        results += f"* {note.id} : {note.content}\n"
    return results

@mcp.tool()
def add_note(content: str) -> str:
    """"Add a note to the user"""

    access_token: AccessToken = get_access_token()
    user_id = jwt.get_unverified_claims(access_token.token)["sub"]

    note = NoteRepository.create_note(user_id,content )

    return f"Added note :  {note.content}"


@mcp.custom_route("/.well-known/oauth-protected-resource",methods=["GET","POST"])
def oauth_metadata(request: StarletteRequest) -> JSONResponse:
    base_url = str(request.base_url).rstrip("/")
    return JSONResponse({
        "resource":base_url,
        "authorization_servers":[os.getenv("STYTCH_DOMAIN")],
        "scopes_supported": ["read", "write"],
        "bearer_methods_supported":["header","body"]
    })


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8080,
        middleware=[Middleware(CORSMiddleware, allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])],
    )
