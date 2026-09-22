"""HTTP boundary: fail closed before any private endpoint reads/mutates an account."""
from urllib.parse import urlsplit
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
import session_store
from wardrobe_store import StorageUnavailable

def install(app, hydrate):
    @app.middleware('http')
    async def account_boundary(request, call_next):
        path = request.url.path
        private = (path.startswith('/api/user/') or path.startswith('/api/wardrobe') or
                   path.startswith('/api/reports/') or path.startswith('/api/menu/') or
                   path in {'/api/auth/session','/api/daily-tarot/draw','/api/daily-tarot/state'})
        auth = path in {'/api/auth/kakao', '/api/auth/logout'}
        if not private and not auth:
            return await call_next(request)
        def error(status, message):
            return JSONResponse({'detail': message}, status_code=status, headers={'Cache-Control':'no-store'})
        try:
            body = {}
            if request.method in {'POST','PUT','PATCH','DELETE'}:
                # A custom header cannot be sent cross-origin by an HTML form.
                if request.headers.get('x-dalha-request') != '1':
                    return error(403, '페이지를 새로고침한 뒤 다시 시도해 주세요.')
                origin = request.headers.get('origin')
                if origin and (urlsplit(origin).netloc != request.url.netloc or
                               urlsplit(origin).scheme not in {'http','https'}):
                    return error(403, '허용되지 않은 요청입니다.')
                if request.headers.get('sec-fetch-site') == 'cross-site':
                    return error(403, '허용되지 않은 요청입니다.')
                raw = await request.body()
                if raw:
                    try:
                        body = await request.json()
                    except ValueError:
                        return error(422, '요청 형식을 확인해 주세요.')
                    if not isinstance(body, dict):
                        return error(422, '요청 형식을 확인해 주세요.')
            user_id = await run_in_threadpool(session_store.resolve, request.cookies.get(session_store.COOKIE))
            fresh_login = path == '/api/auth/kakao' and body.get('profile_source') == 'kakao'
            if not fresh_login and path != '/api/auth/logout':
                if not user_id:
                    return error(401, '로그인이 만료되었습니다. 카카오로 다시 로그인해 주세요.')
                claimed = body.get('user_id', request.query_params.get('user_id'))
                if path == '/api/auth/kakao':
                    claimed = 'user_' + str(body.get('kakao_id', ''))
                if claimed is not None and claimed != user_id:
                    return error(403, '다른 계정의 정보에는 접근할 수 없습니다.')
                await run_in_threadpool(hydrate, user_id)
            request.state.account_id = user_id
            result = await call_next(request)
            result.headers['Cache-Control'] = 'no-store'
            return result
        except StorageUnavailable:
            return error(503, '회원 정보를 안전하게 확인하지 못했습니다. 잠시 후 다시 시도해 주세요.')
